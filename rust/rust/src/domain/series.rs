use super::teams::require_member;
use crate::core::changes::{commit_change, HistoryEntry};
use crate::core::ctx::Ctx;
use crate::core::ops::Operation;
use crate::core::time::{fmt, Ts};
use crate::error::{ApiError, ApiResult};
use crate::register;
use chrono::{DateTime, Duration, NaiveDateTime, Utc};
use rrule::RRuleSet;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sqlx::PgConnection;
use utoipa::ToSchema;
use uuid::Uuid;

const LOCAL_FMT: &str = "%Y-%m-%dT%H:%M:%S";
const MAX_OCCURRENCES: u16 = 1000;

#[derive(sqlx::FromRow)]
struct SeriesRow {
    id: Uuid,
    team_id: Uuid,
    title: String,
    rrule: String,
    dtstart: String,
    timezone: String,
    duration_minutes: i32,
    exdates: Vec<String>,
    status: String,
}

impl SeriesRow {
    fn snapshot(&self) -> Value {
        json!({"id": self.id, "team_id": self.team_id, "title": self.title, "rrule": self.rrule, "dtstart": self.dtstart,
               "timezone": self.timezone, "duration_minutes": self.duration_minutes, "exdates": self.exdates, "status": self.status})
    }
}

const COLS: &str = "id, team_id, title, rrule, dtstart, timezone, duration_minutes, exdates, status";

async fn load(conn: &mut PgConnection, id: Uuid, lock: bool) -> ApiResult<Option<SeriesRow>> {
    let sql = format!("SELECT {COLS} FROM series WHERE id = $1{}", if lock { " FOR UPDATE" } else { "" });
    Ok(sqlx::query_as(sqlx::AssertSqlSafe(sql)).bind(id).fetch_optional(&mut *conn).await?)
}

pub async fn snapshot_of(conn: &mut PgConnection, id: Uuid, lock: bool) -> ApiResult<Option<Value>> {
    Ok(load(conn, id, lock).await?.map(|s| s.snapshot()))
}

pub async fn restore(conn: &mut PgConnection, id: Uuid, before: Option<&Value>) -> ApiResult<()> {
    match before {
        None => {
            sqlx::query("UPDATE series SET status = 'gelöscht' WHERE id = $1").bind(id).execute(&mut *conn).await?;
        }
        Some(b) => {
            let s = |k: &str| b.get(k).and_then(Value::as_str).unwrap_or_default().to_string();
            let ex: Vec<String> = b.get("exdates").and_then(Value::as_array).map(|a| a.iter().filter_map(|v| v.as_str().map(String::from)).collect()).unwrap_or_default();
            sqlx::query("UPDATE series SET title=$2, rrule=$3, dtstart=$4, timezone=$5, duration_minutes=$6, exdates=$7, status=$8 WHERE id=$1")
                .bind(id).bind(s("title")).bind(s("rrule")).bind(s("dtstart")).bind(s("timezone"))
                .bind(b.get("duration_minutes").and_then(Value::as_i64).unwrap_or(60) as i32).bind(ex).bind(s("status"))
                .execute(&mut *conn).await?;
        }
    }
    Ok(())
}

fn parse_local(s: &str, what: &str) -> ApiResult<NaiveDateTime> {
    NaiveDateTime::parse_from_str(s, LOCAL_FMT).map_err(|_| ApiError::validation(format!("{what}: Ortszeit im Format YYYY-MM-DDTHH:MM:SS erwartet")))
}

// EIGENBAU:BEGIN Zusätzliche RFC-5545-Prüfungen: die Bibliothek `rrule` (0.14) akzeptiert COUNT+UNTIL, INTERVAL=0 und BYMONTHDAY=0 stillschweigend.
fn precheck(rule: &str) -> ApiResult<()> {
    let bad = |m: &str| Err(ApiError::invalid_rrule(m.to_string()));
    let mut has = std::collections::HashSet::new();
    for part in rule.split(';') {
        let Some((k, v)) = part.split_once('=') else { return bad("Teil ohne '='") };
        let k = k.to_ascii_uppercase();
        has.insert(k.clone());
        let nums = |lo: i64, hi: i64, zero: bool| -> bool {
            v.split(',').all(|x| x.parse::<i64>().map(|n| (zero || n != 0) && n.abs() >= lo && n.abs() <= hi).unwrap_or(false))
        };
        let ok = match k.as_str() {
            "INTERVAL" | "COUNT" => v.parse::<i64>().map(|n| n >= 1).unwrap_or(false),
            "BYMONTHDAY" => nums(0, 31, false),
            "BYYEARDAY" => nums(0, 366, false),
            "BYWEEKNO" => nums(0, 53, false),
            "BYSETPOS" => nums(0, 366, false),
            _ => true,
        };
        if !ok {
            return bad(&format!("Ungültiger Wert für {k}"));
        }
    }
    if has.contains("COUNT") && has.contains("UNTIL") {
        return bad("COUNT und UNTIL dürfen nicht zusammen auftreten");
    }
    Ok(())
}
// EIGENBAU:END

/// Dehnt die Regel mit Wanduhrsemantik aus (Bibliothek `rrule`); Ausgabe in UTC, höchstens 1000 Vorkommen.
fn expand(rule: &str, dtstart: &str, tz: &str, exdates: &[String], from: DateTime<Utc>, to: DateTime<Utc>) -> ApiResult<Vec<DateTime<Utc>>> {
    precheck(rule)?;
    let zone: chrono_tz::Tz = tz.parse().map_err(|_| ApiError::validation(format!("Unbekannte Zeitzone '{tz}'")))?;
    let compact = |s: &str| -> ApiResult<String> { Ok(parse_local(s, "Ortszeit")?.format("%Y%m%dT%H%M%S").to_string()) };
    let mut text = format!("DTSTART;TZID={tz}:{}\nRRULE:{rule}", compact(dtstart)?);
    for e in exdates {
        text.push_str(&format!("\nEXDATE;TZID={tz}:{}", compact(e)?));
    }
    let set: RRuleSet = text.parse().map_err(|e: rrule::RRuleError| ApiError::invalid_rrule(e.to_string()))?;
    let res = set
        .after(from.with_timezone(&zone).with_timezone(&rrule::Tz::Tz(zone)))
        .before(to.with_timezone(&zone).with_timezone(&rrule::Tz::Tz(zone)))
        .all(MAX_OCCURRENCES + 1);
    let mut out: Vec<DateTime<Utc>> = res.dates.into_iter().map(|d| d.with_timezone(&Utc)).filter(|d| *d >= from && *d < to).collect();
    out.sort();
    out.truncate(MAX_OCCURRENCES as usize);
    Ok(out)
}

// ---------------------------------------------------------------- series.create

#[derive(Deserialize, ToSchema)]
pub struct CreateParams {
    pub team_id: Uuid,
    #[schema(min_length = 1, max_length = 200)]
    pub title: String,
    /// RRULE ohne Präfix `RRULE:`
    #[schema(min_length = 1)]
    pub rrule: String,
    /// Ortszeit, z. B. 2026-03-02T18:00:00
    pub dtstart: String,
    /// IANA-Zeitzonenname
    pub timezone: String,
    #[schema(minimum = 1, maximum = 1440)]
    pub duration_minutes: i32,
    /// Ausgenommene Vorkommen als Ortszeiten
    pub exdates: Option<Vec<String>>,
}
#[derive(Serialize, ToSchema)]
pub struct CreateResult {
    pub series_id: Uuid,
}
pub struct SeriesCreate;
impl Operation for SeriesCreate {
    type Params = CreateParams;
    type Result = CreateResult;
    const NAME: &'static str = "series.create";
    const DESCRIPTION: &'static str = "Legt eine Terminserie nach iCalendar-RRULE an (Wanduhrsemantik in der angegebenen Zeitzone).";
    const MUTATING: bool = true;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<CreateResult> {
        let exdates = p.exdates.unwrap_or_default();
        // Regel prüfen: ungültig -> 422 invalid_rrule
        let start = parse_local(&p.dtstart, "dtstart")?.and_utc();
        expand(&p.rrule, &p.dtstart, &p.timezone, &exdates, start, start + Duration::days(1))?;
        let mut tx = ctx.begin().await?;
        require_member(&mut tx, p.team_id, &ctx.caller.id).await?;
        let id = Uuid::new_v4();
        sqlx::query("INSERT INTO series (id, team_id, title, rrule, dtstart, timezone, duration_minutes, exdates) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)")
            .bind(id).bind(p.team_id).bind(&p.title).bind(&p.rrule).bind(&p.dtstart).bind(&p.timezone).bind(p.duration_minutes).bind(&exdates)
            .execute(&mut *tx).await?;
        let after = snapshot_of(&mut tx, id, false).await?;
        commit_change(
            &mut tx,
            &ctx,
            HistoryEntry { action: "series.create", object_type: "series", object_id: id, team_id: p.team_id, before: None, after, undo_of: None },
            None,
        )
        .await?;
        tx.commit().await?;
        Ok(CreateResult { series_id: id })
    }
}
register!(SeriesCreate);

// ---------------------------------------------------------------- series.occurrences

#[derive(Deserialize, ToSchema)]
pub struct OccurrencesParams {
    pub series_id: Uuid,
    #[schema(value_type = String, format = DateTime)]
    pub from: Ts,
    #[schema(value_type = String, format = DateTime)]
    pub to: Ts,
}
#[derive(Serialize, ToSchema)]
pub struct Occurrence {
    pub starts_at: String,
    pub ends_at: String,
}
#[derive(Serialize, ToSchema)]
pub struct OccurrencesResult {
    pub occurrences: Vec<Occurrence>,
}
pub struct SeriesOccurrences;
impl Operation for SeriesOccurrences {
    type Params = OccurrencesParams;
    type Result = OccurrencesResult;
    const NAME: &'static str = "series.occurrences";
    const DESCRIPTION: &'static str = "Berechnet die Vorkommen einer Serie im Zeitfenster [from, to) in UTC (höchstens 1000, aufsteigend).";
    const MUTATING: bool = false;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<OccurrencesResult> {
        let mut c = ctx.pool.acquire().await?;
        let s = match load(&mut c, p.series_id, false).await? {
            Some(s) if s.status != "gelöscht" => s,
            _ => return Err(ApiError::not_found("Serie nicht gefunden")),
        };
        require_member(&mut c, s.team_id, &ctx.caller.id).await?;
        let dur = Duration::minutes(s.duration_minutes as i64);
        let occ = expand(&s.rrule, &s.dtstart, &s.timezone, &s.exdates, p.from.0, p.to.0)?;
        Ok(OccurrencesResult { occurrences: occ.into_iter().map(|d| Occurrence { starts_at: fmt(d), ends_at: fmt(d + dur) }).collect() })
    }
}
register!(SeriesOccurrences);

#[cfg(test)]
mod tests {
    use super::*;

    fn utc(s: &str) -> DateTime<Utc> {
        DateTime::parse_from_rfc3339(s).unwrap().with_timezone(&Utc)
    }

    #[test]
    fn weekly_keeps_wall_clock_over_dst() {
        let occ = expand("FREQ=WEEKLY;BYDAY=MO;COUNT=8", "2026-03-02T18:00:00", "Europe/Berlin", &[], utc("2026-01-01T00:00:00Z"), utc("2027-01-01T00:00:00Z")).unwrap();
        let s: Vec<String> = occ.into_iter().map(fmt).collect();
        assert_eq!(s[3], "2026-03-23T17:00:00Z");
        assert_eq!(s[4], "2026-03-30T16:00:00Z");
    }

    #[test]
    fn invalid_rules_are_rejected() {
        for r in ["FREQ=FOO", "FREQ=DAILY;INTERVAL=0", "FREQ=WEEKLY;COUNT=3;UNTIL=20270101T000000Z", "FREQ=MONTHLY;BYMONTHDAY=0", "COUNT=2"] {
            let e = expand(r, "2026-03-02T18:00:00", "Europe/Berlin", &[], utc("2026-01-01T00:00:00Z"), utc("2027-01-01T00:00:00Z")).unwrap_err();
            assert_eq!(e.code, "invalid_rrule", "{r}");
        }
    }

    #[test]
    fn exdates_and_limit() {
        let occ = expand("FREQ=DAILY", "2026-01-01T08:00:00", "Europe/Berlin", &["2026-01-02T08:00:00".into()], utc("2026-01-01T00:00:00Z"), utc("2031-01-01T00:00:00Z")).unwrap();
        assert_eq!(occ.len(), 1000);
        assert_eq!(fmt(occ[1]), "2026-01-03T07:00:00Z");
    }
}
