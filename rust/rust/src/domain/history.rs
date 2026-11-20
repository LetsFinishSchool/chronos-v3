use super::teams::require_member;
use crate::core::changes::{commit_change, HistoryEntry, NewEvent};
use crate::core::ctx::Ctx;
use crate::core::ops::{Affected, Operation, Preview};
use crate::core::time::fmt;
use crate::error::{ApiError, ApiResult};
use crate::register;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sqlx::PgConnection;
use utoipa::ToSchema;
use uuid::Uuid;

#[derive(sqlx::FromRow)]
struct Row {
    id: Uuid,
    at: DateTime<Utc>,
    actor: String,
    action: String,
    object_type: String,
    object_id: Uuid,
    team_id: Uuid,
    before: Option<Value>,
    after: Option<Value>,
    bundle_id: Uuid,
    correlation_id: String,
    undone: bool,
    undo_of: Option<Uuid>,
    event_id: Option<Uuid>,
}

const COLS: &str = "id, at, actor, action, object_type, object_id, team_id, before, after, bundle_id, correlation_id, undone, undo_of, event_id";

#[derive(Serialize, ToSchema)]
pub struct EntryView {
    pub id: Uuid,
    pub at: String,
    pub actor: String,
    pub action: String,
    pub object_type: String,
    pub object_id: Uuid,
    #[schema(value_type = Option<Object>)]
    pub before: Option<Value>,
    #[schema(value_type = Option<Object>)]
    pub after: Option<Value>,
    pub bundle_id: Uuid,
    pub correlation_id: String,
    pub undone: bool,
    pub undo_of: Option<Uuid>,
}

impl From<Row> for EntryView {
    fn from(r: Row) -> Self {
        EntryView {
            id: r.id, at: fmt(r.at), actor: r.actor, action: r.action, object_type: r.object_type, object_id: r.object_id,
            before: r.before, after: r.after, bundle_id: r.bundle_id, correlation_id: r.correlation_id, undone: r.undone, undo_of: r.undo_of,
        }
    }
}

// ---------------------------------------------------------------- history.list

#[derive(Deserialize, ToSchema)]
pub struct ListParams {
    pub object_id: Option<Uuid>,
    #[schema(minimum = 1, maximum = 200)]
    pub limit: Option<i64>,
}
#[derive(Serialize, ToSchema)]
pub struct ListResult {
    pub entries: Vec<EntryView>,
}
pub struct HistoryList;
impl Operation for HistoryList {
    type Params = ListParams;
    type Result = ListResult;
    const NAME: &'static str = "history.list";
    const DESCRIPTION: &'static str = "Listet Verlaufseinträge der Teams des Aufrufers, neueste zuerst (limit 1–200, Standard 50).";
    const MUTATING: bool = false;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<ListResult> {
        let mut c = ctx.pool.acquire().await?;
        let sql = format!(
            "WITH RECURSIVE up AS (
               SELECT t.id, t.parent_id FROM teams t JOIN team_members m ON m.team_id = t.id WHERE m.person_id = $1
               UNION SELECT t.id, t.parent_id FROM teams t JOIN up ON up.parent_id = t.id)
             SELECT {COLS} FROM history WHERE team_id IN (SELECT id FROM up) AND ($2::uuid IS NULL OR object_id = $2)
             ORDER BY seq DESC LIMIT $3"
        );
        let rows: Vec<Row> = sqlx::query_as(sqlx::AssertSqlSafe(sql)).bind(&ctx.caller.id).bind(p.object_id).bind(p.limit.unwrap_or(50)).fetch_all(&mut *c).await?;
        Ok(ListResult { entries: rows.into_iter().map(Into::into).collect() })
    }
}
register!(HistoryList);

// ---------------------------------------------------------------- history.undo

#[derive(Deserialize, ToSchema)]
pub struct UndoParams {
    pub history_id: Uuid,
}
#[derive(Serialize, ToSchema)]
pub struct UndoResult {
    pub history_id: Uuid,
}

async fn current_snapshot(conn: &mut PgConnection, object_type: &str, id: Uuid, lock: bool) -> ApiResult<Option<Value>> {
    match object_type {
        "appointment" => Ok(super::appointments::load(conn, id, lock).await?.map(super::appointments::snapshot)),
        "series" => super::series::snapshot_of(conn, id, lock).await,
        other => Err(ApiError::internal(format!("unbekannter Objekttyp {other}"))),
    }
}

async fn restore(conn: &mut PgConnection, object_type: &str, id: Uuid, before: Option<&Value>) -> ApiResult<()> {
    match object_type {
        "appointment" => match before {
            None => {
                sqlx::query("UPDATE appointments SET status = 'gelöscht' WHERE id = $1").bind(id).execute(&mut *conn).await?;
            }
            Some(b) => {
                let s = |k: &str| b.get(k).and_then(Value::as_str).unwrap_or_default().to_string();
                sqlx::query("UPDATE appointments SET title=$2, starts_at=$3::timestamptz, ends_at=$4::timestamptz, timezone=$5, status=$6 WHERE id=$1")
                    .bind(id).bind(s("title")).bind(s("starts_at")).bind(s("ends_at")).bind(s("timezone")).bind(s("status"))
                    .execute(&mut *conn).await?;
            }
        },
        "series" => super::series::restore(conn, id, before).await?,
        other => return Err(ApiError::internal(format!("unbekannter Objekttyp {other}"))),
    }
    Ok(())
}

/// Gemeinsame Prüfung für Aufruf und Vorschau. Gibt Eintrag und aktuellen Zustand zurück.
async fn check_undoable(conn: &mut PgConnection, ctx: &Ctx, id: Uuid, lock: bool) -> ApiResult<(Row, Option<Value>)> {
    let sql = format!("SELECT {COLS} FROM history WHERE id = $1{}", if lock { " FOR UPDATE" } else { "" });
    let entry: Row = sqlx::query_as(sqlx::AssertSqlSafe(sql)).bind(id).fetch_optional(&mut *conn).await?.ok_or_else(|| ApiError::not_found("Verlaufseintrag nicht gefunden"))?;
    require_member(conn, entry.team_id, &ctx.caller.id).await?;
    if entry.undone {
        return Err(ApiError::not_undoable("Der Eintrag wurde bereits rückgängig gemacht"));
    }
    let current = current_snapshot(conn, &entry.object_type, entry.object_id, lock).await?;
    if current != entry.after {
        return Err(ApiError::not_undoable("Der Zustand des Objekts hat sich seit dem Eintrag verändert"));
    }
    Ok((entry, current))
}

pub struct HistoryUndo;
impl Operation for HistoryUndo {
    type Params = UndoParams;
    type Result = UndoResult;
    const NAME: &'static str = "history.undo";
    const DESCRIPTION: &'static str = "Macht einen Verlaufseintrag rückgängig (stellt den Zustand davor wieder her), sofern das Objekt seither unverändert ist.";
    const MUTATING: bool = true;
    const PREVIEW: bool = true;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<UndoResult> {
        let mut tx = ctx.begin().await?;
        let (entry, current) = check_undoable(&mut tx, &ctx, p.history_id, true).await?;
        restore(&mut tx, &entry.object_type, entry.object_id, entry.before.as_ref()).await?;
        let after = current_snapshot(&mut tx, &entry.object_type, entry.object_id, false).await?;
        sqlx::query("UPDATE history SET undone = true WHERE id = $1").bind(entry.id).execute(&mut *tx).await?;
        if let Some(orig) = entry.undo_of {
            // Rückgängig eines Rückgängig: der ursprüngliche Eintrag gilt wieder als wirksam
            sqlx::query("UPDATE history SET undone = false WHERE id = $1").bind(orig).execute(&mut *tx).await?;
        }
        let recipients: Vec<String> = match entry.event_id {
            Some(e) => sqlx::query_scalar("SELECT recipients FROM events WHERE id = $1").bind(e).fetch_optional(&mut *tx).await?.unwrap_or_default(),
            None => vec![],
        };
        let new_id = commit_change(
            &mut tx,
            &ctx,
            HistoryEntry { action: "history.undo", object_type: &entry.object_type, object_id: entry.object_id, team_id: entry.team_id, before: current, after, undo_of: Some(entry.id) },
            Some(NewEvent { event_type: "change.reverted", recipients, payload: json!({"history_id": entry.id, "object_id": entry.object_id}), only_channel: None }),
        )
        .await?;
        tx.commit().await?;
        Ok(UndoResult { history_id: new_id })
    }
    async fn preview(ctx: Ctx, p: Self::Params) -> ApiResult<Preview> {
        let mut c = ctx.pool.acquire().await?;
        let (entry, _) = check_undoable(&mut c, &ctx, p.history_id, false).await?;
        Ok(Preview::new(vec![Affected {
            kind: entry.object_type.clone(),
            id: entry.object_id.to_string(),
            change: format!("'{}' wird rückgängig gemacht", entry.action),
        }]))
    }
}
register!(HistoryUndo);
