//! Zustandsänderung + Verlaufseintrag + Ereignis in EINER Transaktion (V-1 §5, S-3).
use super::ctx::Ctx;
use crate::error::{ApiError, ApiResult};
use serde_json::Value;
use sqlx::PgConnection;
use uuid::Uuid;

pub struct HistoryEntry<'a> {
    pub action: &'a str,
    pub object_type: &'a str,
    pub object_id: Uuid,
    pub team_id: Uuid,
    pub before: Option<Value>,
    pub after: Option<Value>,
    pub undo_of: Option<Uuid>,
}

pub struct NewEvent {
    pub event_type: &'static str,
    pub recipients: Vec<String>,
    pub payload: Value,
    /// Nur dieser Kanal (z. B. `webpush` für `notification.test`), unabhängig von der Kanaleinstellung.
    pub only_channel: Option<&'static str>,
}

/// Schreibt Verlaufseintrag und (optional) Ereignis samt Zustellaufträgen. Gibt die Verlaufs-ID zurück.
/// Muss auf der Transaktion der Zustandsänderung laufen; bei Fehler rollt der Aufrufer zurück.
pub async fn commit_change(
    conn: &mut PgConnection,
    ctx: &Ctx,
    entry: HistoryEntry<'_>,
    event: Option<NewEvent>,
) -> ApiResult<Uuid> {
    let history_id = Uuid::new_v4();
    let event_id = event.as_ref().map(|_| Uuid::new_v4());
    sqlx::query(
        "INSERT INTO history (id, actor, action, object_type, object_id, team_id, before, after, bundle_id, correlation_id, undo_of, event_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)",
    )
    .bind(history_id)
    .bind(&ctx.caller.id)
    .bind(entry.action)
    .bind(entry.object_type)
    .bind(entry.object_id)
    .bind(entry.team_id)
    .bind(entry.before)
    .bind(entry.after)
    .bind(Uuid::new_v4())
    .bind(&ctx.correlation_id)
    .bind(entry.undo_of)
    .bind(event_id)
    .execute(&mut *conn)
    .await?;
    if ctx.fault_after_history {
        return Err(ApiError::internal("Fehlerinjektion after_history"));
    }
    if let (Some(ev), Some(id)) = (event, event_id) {
        insert_event(conn, ctx, id, ev).await?;
    }
    Ok(history_id)
}

pub async fn insert_event(conn: &mut PgConnection, ctx: &Ctx, id: Uuid, ev: NewEvent) -> ApiResult<()> {
    sqlx::query(
        "INSERT INTO events (id, event_type, trigger_actor, trigger_op, correlation_id, payload, recipients, only_channel)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
    )
    .bind(id)
    .bind(ev.event_type)
    .bind(&ctx.caller.id)
    .bind(ctx.op_name)
    .bind(&ctx.correlation_id)
    .bind(&ev.payload)
    .bind(&ev.recipients)
    .bind(ev.only_channel)
    .execute(&mut *conn)
    .await?;
    sqlx::query("INSERT INTO delivery_tasks (event_id, recipient) SELECT $1, r FROM unnest($2::text[]) AS r")
        .bind(id)
        .bind(&ev.recipients)
        .execute(&mut *conn)
        .await?;
    Ok(())
}

/// Ereignis ohne Verlaufseintrag (z. B. `notification.test`); eigene Transaktion des Aufrufers.
pub async fn emit_event(conn: &mut PgConnection, ctx: &Ctx, ev: NewEvent) -> ApiResult<Uuid> {
    let id = Uuid::new_v4();
    insert_event(conn, ctx, id, ev).await?;
    Ok(id)
}
