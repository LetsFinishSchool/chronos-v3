"""Fachbereich Serien: RRULE-Serien mit Wanduhrsemantik (Bibliothek python-dateutil)."""
import json
import uuid
from datetime import UTC, datetime, timedelta
from itertools import islice
from uuid import UUID
from zoneinfo import ZoneInfo

from dateutil import rrule as dr
from pydantic import Field
from sqlalchemy import text

from chronos.core import access, history
from chronos.core.context import Ctx
from chronos.core.errors import InvalidRrule, NotFound
from chronos.core.types import LocalTime, TimeZoneName, UtcTime, fmt_utc
from chronos.ops.registry import Params, Result, operation

MAX_OCCURRENCES = 1000
MAX_ITERATIONS = 200_000  # Schutz vor Regeln, die im Fenster nie treffen


# EIGENBAU:BEGIN RRULE-Zusatzprüfung (dateutil lässt COUNT+UNTIL, INTERVAL=0, BYMONTHDAY=0 und fehlendes FREQ durch)
def _check_rrule_extra(rule: str) -> None:
    parts = {}
    for item in rule.split(";"):
        key, sep, value = item.partition("=")
        if not sep or not value:
            raise InvalidRrule(f"ungültiger Bestandteil: {item!r}")
        parts[key.upper()] = value
    if "FREQ" not in parts:
        raise InvalidRrule("FREQ fehlt")
    if "COUNT" in parts and "UNTIL" in parts:
        raise InvalidRrule("COUNT und UNTIL schließen sich aus")
    if "INTERVAL" in parts and int(parts["INTERVAL"]) < 1:
        raise InvalidRrule("INTERVAL muss mindestens 1 sein")
    if "BYMONTHDAY" in parts and any(int(x) == 0 for x in parts["BYMONTHDAY"].split(",")):
        raise InvalidRrule("BYMONTHDAY darf nicht 0 sein")
# EIGENBAU:END


def build_rule(rule: str, dtstart_local: datetime, tz: str) -> dr.rrule:
    """Prüft und erzeugt die Regel; Beginn gilt als Ortszeit in `tz` (Wanduhr bleibt über Sommerzeit gleich)."""
    if rule.upper().startswith("RRULE:") or "\n" in rule:
        raise InvalidRrule("rrule ohne Präfix RRULE: und einzeilig erwartet")
    try:
        _check_rrule_extra(rule)
        start = dtstart_local.replace(tzinfo=ZoneInfo(tz))
        parsed = dr.rrulestr(rule, dtstart=start)
    except InvalidRrule:
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        raise InvalidRrule(f"ungültige RRULE: {e}") from e
    if not isinstance(parsed, dr.rrule):
        raise InvalidRrule("genau eine RRULE erwartet")
    return parsed


def expand(rule: dr.rrule, tz: str, exdates: list[datetime], frm: datetime, to: datetime) -> list[datetime]:
    ztz = ZoneInfo(tz)
    ex = {d.replace(tzinfo=ztz) for d in exdates}
    out: list[datetime] = []
    for occ in islice(rule, MAX_ITERATIONS):
        occ_utc = occ.astimezone(UTC)
        if occ_utc >= to:
            break
        if occ in ex or occ_utc < frm:
            continue
        out.append(occ_utc)
        if len(out) >= MAX_OCCURRENCES:
            break
    return out


async def _load(ctx: Ctx, series_id: str):
    return (await ctx.db.execute(
        text("SELECT id::text AS id, team_id::text AS team_id, title, rrule, dtstart, timezone, duration_minutes, "
             "exdates, status FROM series WHERE id = :id"), {"id": series_id})).first()


def _snapshot(r) -> dict:
    return {"id": r.id, "team_id": r.team_id, "title": r.title, "rrule": r.rrule,
            "dtstart": r.dtstart.strftime("%Y-%m-%dT%H:%M:%S"), "timezone": r.timezone,
            "duration_minutes": r.duration_minutes, "exdates": r.exdates, "status": r.status}


async def load_snapshot(ctx: Ctx, series_id: str) -> dict | None:
    r = await _load(ctx, series_id)
    return _snapshot(r) if r else None


async def store_snapshot(ctx: Ctx, series_id: str, s: dict) -> None:
    await ctx.db.execute(text("UPDATE series SET status = :st WHERE id = :id"), {"id": series_id, "st": s["status"]})


history.register_object_type("series", load_snapshot, store_snapshot)


class SeriesCreateParams(Params):
    team_id: UUID
    title: str = Field(min_length=1, max_length=200)
    rrule: str = Field(min_length=1, description="RFC-5545-Regel ohne Präfix RRULE:, z. B. FREQ=WEEKLY;BYDAY=MO")
    dtstart: LocalTime = Field(description="Beginn als Ortszeit, z. B. 2026-03-02T18:00:00")
    timezone: TimeZoneName
    duration_minutes: int = Field(ge=1, le=1440)
    exdates: list[LocalTime] | None = Field(default=None, description="Ausgenommene Vorkommen (Ortszeiten)")


class SeriesCreateResult(Result):
    series_id: str


@operation("series.create", "Legt eine Terminserie nach RRULE an (Wanduhrsemantik in der angegebenen Zeitzone). "
           "Ungültige RRULE ergibt invalid_rrule.", mutating=True)
async def series_create(ctx: Ctx, p: SeriesCreateParams) -> SeriesCreateResult:
    await access.require_member(ctx, str(p.team_id))
    build_rule(p.rrule, p.dtstart, p.timezone)
    sid = str(uuid.uuid4())
    exdates = [d.strftime("%Y-%m-%dT%H:%M:%S") for d in (p.exdates or [])]
    await ctx.db.execute(
        text("INSERT INTO series (id, team_id, title, rrule, dtstart, timezone, duration_minutes, exdates) "
             "VALUES (:id, :team, :title, :rrule, :dtstart, :tz, :dur, CAST(:ex AS jsonb))"),
        {"id": sid, "team": str(p.team_id), "title": p.title, "rrule": p.rrule, "dtstart": p.dtstart,
         "tz": p.timezone, "dur": p.duration_minutes, "ex": json.dumps(exdates)})
    after = await load_snapshot(ctx, sid)
    await history.write(ctx, action="series.create", object_type="series", object_id=sid, team_id=str(p.team_id),
                        before=None, after=after)
    return SeriesCreateResult(series_id=sid)


class Occurrence(Result):
    starts_at: str
    ends_at: str


class SeriesOccurrencesParams(Params):
    series_id: UUID
    from_: UtcTime = Field(alias="from")
    to: UtcTime


class SeriesOccurrencesResult(Result):
    occurrences: list[Occurrence]


@operation("series.occurrences", "Berechnet die Vorkommen einer Serie im Fenster [from, to) in UTC "
           "(höchstens 1000, aufsteigend sortiert).")
async def series_occurrences(ctx: Ctx, p: SeriesOccurrencesParams) -> SeriesOccurrencesResult:
    row = await _load(ctx, str(p.series_id))
    if row is None or row.status == "gelöscht":
        raise NotFound("Serie nicht gefunden")
    await access.require_member(ctx, row.team_id)
    rule = build_rule(row.rrule, row.dtstart, row.timezone)
    exdates = [datetime.fromisoformat(x) for x in row.exdates]
    starts = expand(rule, row.timezone, exdates, p.from_, p.to)
    dur = timedelta(minutes=row.duration_minutes)
    return SeriesOccurrencesResult(
        occurrences=[Occurrence(starts_at=fmt_utc(s), ends_at=fmt_utc(s + dur)) for s in starts])
