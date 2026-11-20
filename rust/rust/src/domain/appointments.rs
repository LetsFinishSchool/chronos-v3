use super::teams::{recipients_except, require_member};
use crate::core::changes::{commit_change, HistoryEntry, NewEvent};
use crate::core::ctx::Ctx;
use crate::core::ops::{Affected, Operation, Preview};
use crate::core::time::{fmt, Ts};
use crate::error::{ApiError, ApiResult};
use crate::register;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sqlx::PgConnection;
use utoipa::ToSchema;
use uuid::Uuid;

#[derive(sqlx::FromRow)]
pub struct AppointmentRow {
    pub id: Uuid,
    pub team_id: Uuid,
    pub title: String,
    pub starts_at: DateTime<Utc>,
    pub ends_at: DateTime<Utc>,
    pub timezone: String,
    pub status: String,
}

#[derive(Serialize, ToSchema)]
pub struct AppointmentView {
    pub id: Uuid,
    pub team_id: Uuid,
    pub title: String,
    pub starts_at: String,
    pub ends_at: String,
    pub timezone: String,
    pub status: String,
}

impl From<AppointmentRow> for AppointmentView {
    fn from(r: AppointmentRow) -> Self {
        AppointmentView {
            id: r.id,
            team_id: r.team_id,
            title: r.title,
            starts_at: fmt(r.starts_at),
            ends_at: fmt(r.ends_at),
            timezone: r.timezone,
            status: r.status,
        }
    }
}

pub fn snapshot(r: AppointmentRow) -> Value {
    serde_json::to_value(AppointmentView::from(r)).unwrap_or(Value::Null)
}

pub async fn load(conn: &mut PgConnection, id: Uuid, lock: bool) -> ApiResult<Option<AppointmentRow>> {
    let sql = if lock {
        "SELECT id, team_id, title, starts_at, ends_at, timezone, status FROM appointments WHERE id = $1 FOR UPDATE"
    } else {
        "SELECT id, team_id, title, starts_at, ends_at, timezone, status FROM appointments WHERE id = $1"
    };
    Ok(sqlx::query_as(sql).bind(id).fetch_optional(&mut *conn).await?)
}

/// Lädt einen nicht gelöschten Termin und prüft die Mitgliedschaft.
pub async fn load_visible(conn: &mut PgConnection, id: Uuid, person: &str, lock: bool) -> ApiResult<AppointmentRow> {
    match load(conn, id, lock).await? {
        Some(a) if a.status != "gelöscht" => {
            require_member(conn, a.team_id, person).await?;
            Ok(a)
        }
        _ => Err(ApiError::not_found("Termin nicht gefunden")),
    }
}

pub fn check_timezone(tz: &str) -> ApiResult<()> {
    tz.parse::<chrono_tz::Tz>().map(|_| ()).map_err(|_| ApiError::validation(format!("Unbekannte Zeitzone '{tz}'")))
}

pub fn check_range(s: Ts, e: Ts) -> ApiResult<()> {
    if e.0 <= s.0 { Err(ApiError::validation("ends_at muss nach starts_at liegen")) } else { Ok(()) }
}

// ---------------------------------------------------------------- appointment.create

#[derive(Deserialize, ToSchema)]
pub struct CreateParams {
    pub team_id: Uuid,
    #[schema(min_length = 1, max_length = 200)]
    pub title: String,
    #[schema(value_type = String, format = DateTime)]
    pub starts_at: Ts,
    #[schema(value_type = String, format = DateTime)]
    pub ends_at: Ts,
    /// IANA-Zeitzonenname, z. B. Europe/Berlin
    #[schema(min_length = 1)]
    pub timezone: String,
}
#[derive(Serialize, ToSchema)]
pub struct CreateResult {
    pub appointment_id: Uuid,
}
pub struct AppointmentCreate;
impl Operation for AppointmentCreate {
    type Params = CreateParams;
    type Result = CreateResult;
    const NAME: &'static str = "appointment.create";
    const DESCRIPTION: &'static str = "Legt einen Termin (Status geplant) in einem Team an und benachrichtigt die übrigen Mitglieder. Zeiten in UTC (ISO 8601 mit Z).";
    const MUTATING: bool = true;
    const PREVIEW: bool = true;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<CreateResult> {
        check_range(p.starts_at, p.ends_at)?;
        check_timezone(&p.timezone)?;
        let mut tx = ctx.begin().await?;
        require_member(&mut tx, p.team_id, &ctx.caller.id).await?;
        let id = Uuid::new_v4();
        sqlx::query("INSERT INTO appointments (id, team_id, title, starts_at, ends_at, timezone, status) VALUES ($1,$2,$3,$4,$5,$6,'geplant')")
            .bind(id).bind(p.team_id).bind(&p.title).bind(p.starts_at.0).bind(p.ends_at.0).bind(&p.timezone)
            .execute(&mut *tx).await?;
        let after = load(&mut tx, id, false).await?.map(snapshot);
        let recipients = recipients_except(&mut tx, p.team_id, &ctx.caller.id).await?;
        commit_change(
            &mut tx,
            &ctx,
            HistoryEntry { action: "appointment.create", object_type: "appointment", object_id: id, team_id: p.team_id, before: None, after, undo_of: None },
            Some(NewEvent { event_type: "appointment.created", recipients, payload: json!({"appointment_id": id}), only_channel: None }),
        )
        .await?;
        tx.commit().await?;
        Ok(CreateResult { appointment_id: id })
    }
    async fn preview(ctx: Ctx, p: Self::Params) -> ApiResult<Preview> {
        check_range(p.starts_at, p.ends_at)?;
        check_timezone(&p.timezone)?;
        let mut c = ctx.pool.acquire().await?;
        require_member(&mut c, p.team_id, &ctx.caller.id).await?;
        Ok(Preview::new(vec![Affected { kind: "appointment".into(), id: Uuid::nil().to_string(), change: format!("wird angelegt: {}", p.title) }]))
    }
}
register!(AppointmentCreate);

// ---------------------------------------------------------------- appointment.get / list

#[derive(Deserialize, ToSchema)]
pub struct GetParams {
    pub appointment_id: Uuid,
}
#[derive(Serialize, ToSchema)]
pub struct GetResult {
    pub appointment: AppointmentView,
}
pub struct AppointmentGet;
impl Operation for AppointmentGet {
    type Params = GetParams;
    type Result = GetResult;
    const NAME: &'static str = "appointment.get";
    const DESCRIPTION: &'static str = "Liefert einen Termin (Status geplant oder abgesagt); gelöschte Termine sind nicht abrufbar.";
    const MUTATING: bool = false;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<GetResult> {
        let mut c = ctx.pool.acquire().await?;
        let a = load_visible(&mut c, p.appointment_id, &ctx.caller.id, false).await?;
        Ok(GetResult { appointment: a.into() })
    }
}
register!(AppointmentGet);

#[derive(Deserialize, ToSchema)]
pub struct ListParams {
    pub team_id: Uuid,
}
#[derive(Serialize, ToSchema)]
pub struct ListResult {
    pub appointments: Vec<AppointmentView>,
}
pub struct AppointmentList;
impl Operation for AppointmentList {
    type Params = ListParams;
    type Result = ListResult;
    const NAME: &'static str = "appointment.list";
    const DESCRIPTION: &'static str = "Listet die Termine eines Teams (inklusive abgesagter, ohne gelöschte), nach Beginn sortiert.";
    const MUTATING: bool = false;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<ListResult> {
        let mut c = ctx.pool.acquire().await?;
        require_member(&mut c, p.team_id, &ctx.caller.id).await?;
        let rows: Vec<AppointmentRow> = sqlx::query_as(
            "SELECT id, team_id, title, starts_at, ends_at, timezone, status FROM appointments
             WHERE team_id = $1 AND status <> 'gelöscht' ORDER BY starts_at, id",
        )
        .bind(p.team_id)
        .fetch_all(&mut *c)
        .await?;
        Ok(ListResult { appointments: rows.into_iter().map(Into::into).collect() })
    }
}
register!(AppointmentList);

// ---------------------------------------------------------------- appointment.cancel

#[derive(Serialize, ToSchema)]
pub struct EmptyResult {}

pub struct AppointmentCancel;
impl Operation for AppointmentCancel {
    type Params = GetParams;
    type Result = EmptyResult;
    const NAME: &'static str = "appointment.cancel";
    const DESCRIPTION: &'static str = "Sagt einen geplanten Termin ab und benachrichtigt die übrigen Mitglieder.";
    const MUTATING: bool = true;
    const PREVIEW: bool = true;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<EmptyResult> {
        let mut tx = ctx.begin().await?;
        let a = load_visible(&mut tx, p.appointment_id, &ctx.caller.id, true).await?;
        if a.status != "geplant" {
            return Err(ApiError::conflict("Termin ist bereits abgesagt"));
        }
        let team_id = a.team_id;
        let before = snapshot(a);
        sqlx::query("UPDATE appointments SET status = 'abgesagt' WHERE id = $1").bind(p.appointment_id).execute(&mut *tx).await?;
        let after = load(&mut tx, p.appointment_id, false).await?.map(snapshot);
        let recipients = recipients_except(&mut tx, team_id, &ctx.caller.id).await?;
        commit_change(
            &mut tx,
            &ctx,
            HistoryEntry { action: "appointment.cancel", object_type: "appointment", object_id: p.appointment_id, team_id, before: Some(before), after, undo_of: None },
            Some(NewEvent { event_type: "appointment.cancelled", recipients, payload: json!({"appointment_id": p.appointment_id}), only_channel: None }),
        )
        .await?;
        tx.commit().await?;
        Ok(EmptyResult {})
    }
    async fn preview(ctx: Ctx, p: Self::Params) -> ApiResult<Preview> {
        let mut c = ctx.pool.acquire().await?;
        let a = load_visible(&mut c, p.appointment_id, &ctx.caller.id, false).await?;
        if a.status != "geplant" {
            return Err(ApiError::conflict("Termin ist bereits abgesagt"));
        }
        Ok(Preview::new(vec![Affected { kind: "appointment".into(), id: a.id.to_string(), change: format!("'{}' wird abgesagt", a.title) }]))
    }
}
register!(AppointmentCancel);
