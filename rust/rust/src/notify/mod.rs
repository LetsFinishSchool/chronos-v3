//! Benachrichtigungseinstellungen, Zustellprotokoll und Kostenliste (Operationen). Kein Fachbereich, kein Kanal.
use crate::channels::ChannelKind;
use crate::core::changes::{emit_event, NewEvent};
use crate::core::ctx::Ctx;
use crate::core::ops::Operation;
use crate::core::time::fmt;
use crate::error::ApiResult;
use crate::register;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use utoipa::ToSchema;
use uuid::Uuid;

#[derive(Serialize, ToSchema)]
pub struct Empty {}

// ---------------------------------------------------------------- notification.set_channels

#[derive(Deserialize, ToSchema)]
pub struct SetChannelsParams {
    /// Geordnete Liste; der erste Kanal wird zuerst versucht, die folgenden dienen als Ersatz.
    #[schema(min_items = 1)]
    pub channels: Vec<ChannelKind>,
}
pub struct SetChannels;
impl Operation for SetChannels {
    type Params = SetChannelsParams;
    type Result = Empty;
    const NAME: &'static str = "notification.set_channels";
    const DESCRIPTION: &'static str = "Legt die geordnete Liste der Benachrichtigungskanäle des Aufrufers fest (mock, email, webpush).";
    const MUTATING: bool = true;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<Empty> {
        let names: Vec<&str> = p.channels.iter().map(|c| c.as_str()).collect();
        sqlx::query("UPDATE persons SET channels = $2 WHERE id = $1").bind(&ctx.caller.id).bind(&names).execute(&ctx.pool).await?;
        Ok(Empty {})
    }
}
register!(SetChannels);

// ---------------------------------------------------------------- notification.subscribe_push

#[derive(Deserialize, ToSchema)]
pub struct SubscribeParams {
    #[schema(pattern = "^https://.+")]
    pub endpoint: String,
    #[schema(min_length = 1)]
    pub p256dh: String,
    #[schema(min_length = 1)]
    pub auth: String,
}
pub struct SubscribePush;
impl Operation for SubscribePush {
    type Params = SubscribeParams;
    type Result = Empty;
    const NAME: &'static str = "notification.subscribe_push";
    const DESCRIPTION: &'static str = "Speichert ein Web-Push-Abonnement des Aufrufers.";
    const MUTATING: bool = true;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<Empty> {
        sqlx::query(
            "INSERT INTO push_subscriptions (person_id, endpoint, p256dh, auth) VALUES ($1,$2,$3,$4)
             ON CONFLICT (person_id, endpoint) DO UPDATE SET p256dh = EXCLUDED.p256dh, auth = EXCLUDED.auth",
        )
        .bind(&ctx.caller.id).bind(&p.endpoint).bind(&p.p256dh).bind(&p.auth)
        .execute(&ctx.pool).await?;
        Ok(Empty {})
    }
}
register!(SubscribePush);

// ---------------------------------------------------------------- notification.test_push

#[derive(Deserialize, ToSchema)]
pub struct NoParams {}
#[derive(Serialize, ToSchema)]
pub struct TestPushResult {
    pub event_id: Uuid,
}
pub struct TestPush;
impl Operation for TestPush {
    type Params = NoParams;
    type Result = TestPushResult;
    const NAME: &'static str = "notification.test_push";
    const DESCRIPTION: &'static str = "Erzeugt ein Testereignis nur für den Aufrufer, zugestellt ausschließlich über Web Push.";
    const MUTATING: bool = true;
    async fn run(ctx: Ctx, _p: Self::Params) -> ApiResult<TestPushResult> {
        let mut tx = ctx.begin().await?;
        let id = emit_event(&mut tx, &ctx, NewEvent { event_type: "notification.test", recipients: vec![ctx.caller.id.clone()], payload: json!({}), only_channel: Some("webpush") }).await?;
        tx.commit().await?;
        Ok(TestPushResult { event_id: id })
    }
}
register!(TestPush);

// ---------------------------------------------------------------- notification.list

#[derive(Deserialize, ToSchema)]
pub struct ListParams {
    pub event_id: Option<Uuid>,
    pub correlation_id: Option<String>,
    #[schema(minimum = 1, maximum = 500)]
    pub limit: Option<i64>,
}
#[derive(Serialize, ToSchema)]
pub struct TriggerView {
    pub kind: String,
    pub actor: String,
}
#[derive(Serialize, ToSchema)]
pub struct DeliveryView {
    pub event_id: Uuid,
    pub event_type: String,
    pub correlation_id: String,
    pub trigger: TriggerView,
    pub recipient: String,
    pub channel: String,
    pub attempt: i32,
    /// success, failed oder skipped
    pub result: String,
    pub error: Option<String>,
    pub at: String,
    pub idempotency_key: String,
}
#[derive(Serialize, ToSchema)]
pub struct ListResult {
    pub deliveries: Vec<DeliveryView>,
}
#[derive(sqlx::FromRow)]
struct DeliveryRow {
    event_id: Uuid,
    event_type: String,
    correlation_id: String,
    trigger_kind: String,
    trigger_actor: String,
    recipient: String,
    channel: String,
    attempt: i32,
    result: String,
    error: Option<String>,
    at: DateTime<Utc>,
    idempotency_key: String,
}
pub struct NotificationList;
impl Operation for NotificationList {
    type Params = ListParams;
    type Result = ListResult;
    const NAME: &'static str = "notification.list";
    const DESCRIPTION: &'static str = "Listet das Zustellprotokoll (ein Eintrag je Versuch) der Ereignisse, die der Aufrufer ausgelöst hat oder bei denen er Empfänger ist; älteste zuerst.";
    const MUTATING: bool = false;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<ListResult> {
        let rows: Vec<DeliveryRow> = sqlx::query_as(
            "SELECT d.event_id, e.event_type, e.correlation_id, e.trigger_kind, e.trigger_actor, d.recipient, d.channel, d.attempt,
                    d.result, d.error, d.at, d.idempotency_key
             FROM deliveries d JOIN events e ON e.id = d.event_id
             WHERE (e.trigger_actor = $1 OR d.recipient = $1) AND ($2::uuid IS NULL OR e.id = $2) AND ($3::text IS NULL OR e.correlation_id = $3)
             ORDER BY d.id LIMIT $4",
        )
        .bind(&ctx.caller.id).bind(p.event_id).bind(p.correlation_id).bind(p.limit.unwrap_or(100))
        .fetch_all(&ctx.pool).await?;
        Ok(ListResult {
            deliveries: rows.into_iter().map(|r| DeliveryView {
                event_id: r.event_id, event_type: r.event_type, correlation_id: r.correlation_id,
                trigger: TriggerView { kind: r.trigger_kind, actor: r.trigger_actor },
                recipient: r.recipient, channel: r.channel, attempt: r.attempt, result: r.result, error: r.error,
                at: fmt(r.at), idempotency_key: r.idempotency_key,
            }).collect(),
        })
    }
}
register!(NotificationList);

// ---------------------------------------------------------------- cost.list

#[derive(Deserialize, ToSchema)]
pub struct CostListParams {
    #[schema(minimum = 1, maximum = 500)]
    pub limit: Option<i64>,
}
#[derive(Serialize, ToSchema)]
pub struct CostTrigger {
    pub kind: String,
    pub name: String,
    pub correlation_id: String,
}
#[derive(Serialize, ToSchema)]
pub struct CostEntry {
    pub id: Uuid,
    pub at: String,
    pub person_id: String,
    /// anthropic oder smtp
    pub provider: String,
    pub trigger: CostTrigger,
    #[schema(value_type = Object)]
    pub quantity: Value,
    pub amount_micro_eur: i64,
}
#[derive(Serialize, ToSchema)]
pub struct CostListResult {
    pub entries: Vec<CostEntry>,
}
#[derive(sqlx::FromRow)]
struct CostRow {
    id: Uuid,
    at: DateTime<Utc>,
    person_id: String,
    provider: String,
    trigger_kind: String,
    trigger_name: String,
    correlation_id: String,
    quantity: Value,
    amount_micro_eur: i64,
}
pub struct CostList;
impl Operation for CostList {
    type Params = CostListParams;
    type Result = CostListResult;
    const NAME: &'static str = "cost.list";
    const DESCRIPTION: &'static str = "Listet die Kostenposten des Aufrufers (als Verursacher), neueste zuerst.";
    const MUTATING: bool = false;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<CostListResult> {
        let rows: Vec<CostRow> = sqlx::query_as(
            "SELECT id, at, person_id, provider, trigger_kind, trigger_name, correlation_id, quantity, amount_micro_eur
             FROM cost_entries WHERE person_id = $1 ORDER BY seq DESC LIMIT $2",
        )
        .bind(&ctx.caller.id).bind(p.limit.unwrap_or(100)).fetch_all(&ctx.pool).await?;
        Ok(CostListResult {
            entries: rows.into_iter().map(|r| CostEntry {
                id: r.id, at: fmt(r.at), person_id: r.person_id, provider: r.provider,
                trigger: CostTrigger { kind: r.trigger_kind, name: r.trigger_name, correlation_id: r.correlation_id },
                quantity: r.quantity, amount_micro_eur: r.amount_micro_eur,
            }).collect(),
        })
    }
}
register!(CostList);

