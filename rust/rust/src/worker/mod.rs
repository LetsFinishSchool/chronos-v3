//! Worker: liest Zustellaufträge aus der Datenbank (kein Aufruf vom Web) und stellt über die Kanäle zu.
use crate::channels::{self, ChannelKind, Delivery, Env, Outcome};
use crate::config::Config;
use crate::core::cost;
use crate::db;
use crate::error::BoxResult;
use crate::logging::CORRELATION;
use axum::{extract::State, http::StatusCode, routing::get, Json, Router};
use serde_json::json;
use sqlx::PgPool;
use std::sync::Arc;
use std::time::Duration;
use uuid::Uuid;

const MAX_ATTEMPTS: i32 = 3;
const LEASE_SECONDS: i32 = 30;

#[derive(sqlx::FromRow)]
struct Task {
    id: i64,
    event_id: Uuid,
    recipient: String,
    channel_idx: i32,
    attempt: i32,
}

#[derive(sqlx::FromRow)]
struct EventRow {
    event_type: String,
    correlation_id: String,
    trigger_actor: String,
    trigger_op: String,
    only_channel: Option<String>,
}

pub async fn run(cfg: Config) -> BoxResult {
    let cfg = Arc::new(cfg);
    let pool = db::connect(&cfg.database_url).await?;
    db::wait_for_schema(&pool, Duration::from_secs(60)).await?;
    // Wiederanlauf: Aufträge, die ein beendeter Worker gesperrt hielt, sofort wieder freigeben (ein Worker-Prozess).
    sqlx::query("UPDATE delivery_tasks SET locked_until = NULL WHERE state = 'pending'").execute(&pool).await?;
    tracing::info!("Worker gestartet");

    let health = Router::new().route("/healthz", get(healthz)).with_state(pool.clone());
    let listener = tokio::net::TcpListener::bind(("0.0.0.0", cfg.worker_health_port)).await?;
    tokio::spawn(async move {
        let _ = axum::serve(listener, health).await;
    });

    let env = Env { cfg: cfg.clone(), http: reqwest::Client::new(), pool: pool.clone() };
    loop {
        match claim(&pool, cfg.worker_concurrency as i64).await {
            Ok(tasks) if !tasks.is_empty() => {
                futures::future::join_all(tasks.into_iter().map(|t| process(&env, t))).await;
            }
            Ok(_) => tokio::time::sleep(Duration::from_millis(100)).await,
            Err(e) => {
                tracing::error!(error = %e, "Aufträge konnten nicht geholt werden");
                tokio::time::sleep(Duration::from_secs(1)).await;
            }
        }
    }
}

async fn healthz(State(pool): State<PgPool>) -> (StatusCode, Json<serde_json::Value>) {
    match sqlx::query("SELECT 1").execute(&pool).await {
        Ok(_) => (StatusCode::OK, Json(json!({"status": "ok"}))),
        Err(_) => (StatusCode::SERVICE_UNAVAILABLE, Json(json!({"status": "db_unreachable"}))),
    }
}

async fn claim(pool: &PgPool, n: i64) -> Result<Vec<Task>, sqlx::Error> {
    sqlx::query_as(
        "UPDATE delivery_tasks SET locked_until = now() + make_interval(secs => $2)
         WHERE id IN (SELECT id FROM delivery_tasks
                      WHERE state = 'pending' AND next_at <= now() AND (locked_until IS NULL OR locked_until < now())
                      ORDER BY next_at, id LIMIT $1 FOR UPDATE SKIP LOCKED)
         RETURNING id, event_id, recipient, channel_idx, attempt",
    )
    .bind(n)
    .bind(LEASE_SECONDS as f64)
    .fetch_all(pool)
    .await
}

async fn process(env: &Env, task: Task) {
    let ev: Result<EventRow, _> = sqlx::query_as("SELECT event_type, correlation_id, trigger_actor, trigger_op, only_channel FROM events WHERE id = $1")
        .bind(task.event_id)
        .fetch_one(&env.pool)
        .await;
    let ev = match ev {
        Ok(e) => e,
        Err(e) => {
            tracing::error!(error = %e, event_id = %task.event_id, "Ereignis nicht lesbar");
            return;
        }
    };
    let corr = ev.correlation_id.clone();
    CORRELATION.scope(corr, async {
        if let Err(e) = process_task(env, &task, &ev).await {
            tracing::error!(error = %e, event_id = %task.event_id, "Zustellung nicht verbucht; wird wiederholt");
        }
    })
    .await;
}

async fn process_task(env: &Env, task: &Task, ev: &EventRow) -> Result<(), sqlx::Error> {
    let person: Option<(String, Vec<String>)> = sqlx::query_as("SELECT email, channels FROM persons WHERE id = $1").bind(&task.recipient).fetch_optional(&env.pool).await?;
    let (email, names) = person.unwrap_or_else(|| (String::new(), vec!["webpush".into(), "email".into()]));
    let names: Vec<String> = match &ev.only_channel {
        Some(c) => vec![c.clone()],
        None => names,
    };
    let kinds: Vec<ChannelKind> = names.iter().filter_map(|n| ChannelKind::parse(n)).collect();
    let Some(kind) = kinds.get(task.channel_idx as usize).copied() else {
        sqlx::query("UPDATE delivery_tasks SET state = 'failed', locked_until = NULL WHERE id = $1").bind(task.id).execute(&env.pool).await?;
        return Ok(());
    };
    let key = format!("{}:{}:{}", task.event_id, task.recipient, kind.as_str());
    let d = Delivery {
        event_id: task.event_id,
        event_type: ev.event_type.clone(),
        correlation_id: ev.correlation_id.clone(),
        recipient: task.recipient.clone(),
        recipient_email: email,
        idempotency_key: key.clone(),
    };
    let outcome = channels::deliver(kind, env, &d).await;
    let (result, error) = match &outcome {
        Outcome::Success => ("success", None),
        Outcome::Failed(e) => ("failed", Some(e.clone())),
        Outcome::Skipped(e) => ("skipped", Some(e.clone())),
    };
    tracing::info!(event_id = %task.event_id, channel = kind.as_str(), attempt = task.attempt, result, "Zustellversuch");

    let last_channel = task.channel_idx as usize + 1 >= kinds.len();
    let mut tx = env.pool.begin().await?;
    sqlx::query("INSERT INTO deliveries (event_id, recipient, channel, attempt, result, error, idempotency_key) VALUES ($1,$2,$3,$4,$5,$6,$7)")
        .bind(task.event_id).bind(&task.recipient).bind(kind.as_str()).bind(task.attempt).bind(result).bind(&error).bind(&key)
        .execute(&mut *tx).await?;
    match outcome {
        Outcome::Success => {
            sqlx::query("UPDATE delivery_tasks SET state = 'done', locked_until = NULL WHERE id = $1").bind(task.id).execute(&mut *tx).await?;
            if kind == ChannelKind::Email {
                cost::record(&mut tx, &ev.trigger_actor, "smtp", &ev.trigger_op, &ev.correlation_id, json!({"messages": 1}), env.cfg.email_price).await?;
            }
        }
        Outcome::Skipped(_) => advance(&mut tx, task, last_channel).await?,
        Outcome::Failed(_) if task.attempt < MAX_ATTEMPTS => {
            let wait_ms = env.cfg.retry_base_ms * (1u64 << (task.attempt - 1));
            sqlx::query("UPDATE delivery_tasks SET attempt = attempt + 1, next_at = now() + make_interval(secs => $2), locked_until = NULL WHERE id = $1")
                .bind(task.id).bind(wait_ms as f64 / 1000.0).execute(&mut *tx).await?;
        }
        Outcome::Failed(_) => advance(&mut tx, task, last_channel).await?,
    }
    tx.commit().await
}

/// Nächster Kanal (Ersatzkanal) oder Ende, wenn keiner mehr folgt.
async fn advance(tx: &mut sqlx::PgConnection, task: &Task, last_channel: bool) -> Result<(), sqlx::Error> {
    if last_channel {
        sqlx::query("UPDATE delivery_tasks SET state = 'failed', locked_until = NULL WHERE id = $1").bind(task.id).execute(&mut *tx).await?;
    } else {
        sqlx::query("UPDATE delivery_tasks SET channel_idx = channel_idx + 1, attempt = 1, next_at = now(), locked_until = NULL WHERE id = $1")
            .bind(task.id).execute(&mut *tx).await?;
    }
    Ok(())
}
