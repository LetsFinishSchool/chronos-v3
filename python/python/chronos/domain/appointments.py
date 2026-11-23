"""Fachbereich Termine: Anlegen, Lesen, Auflisten, Absagen (mit Verlauf und Ereignis in EINER Transaktion)."""
import uuid
from typing import Self
from uuid import UUID

from pydantic import Field, model_validator
from sqlalchemy import text

from chronos.core import access, events, history
from chronos.core.context import Ctx
from chronos.core.errors import Conflict, Forbidden, NotFound
from chronos.core.types import TimeZoneName, UtcTime, fmt_utc
from chronos.ops.registry import Empty, Params, Result, operation

_COLS = "id::text AS id, team_id::text AS team_id, title, starts_at, ends_at, timezone, status"


class AppointmentOut(Result):
    id: str
    team_id: str
    title: str
    starts_at: str
    ends_at: str
    timezone: str
    status: str


def _snapshot(row) -> dict:
    return {"id": row.id, "team_id": row.team_id, "title": row.title, "starts_at": fmt_utc(row.starts_at),
            "ends_at": fmt_utc(row.ends_at), "timezone": row.timezone, "status": row.status}


async def load_snapshot(ctx: Ctx, appointment_id: str, *, lock: bool = True) -> dict | None:
    row = (await ctx.db.execute(text(f"SELECT {_COLS} FROM appointment WHERE id = :id" + (" FOR UPDATE" if lock else "")),
                                {"id": appointment_id})).first()
    return _snapshot(row) if row else None


async def store_snapshot(ctx: Ctx, appointment_id: str, s: dict) -> None:
    await ctx.db.execute(
        text("UPDATE appointment SET title = :title, starts_at = :starts, ends_at = :ends, timezone = :tz, "
             "status = :status WHERE id = :id"),
        {"id": appointment_id, "title": s["title"], "starts": s["starts_at"], "ends": s["ends_at"],
         "tz": s["timezone"], "status": s["status"]})


history.register_object_type("appointment", load_snapshot, store_snapshot)


async def _visible(ctx: Ctx, appointment_id: str, *, lock: bool = True) -> dict:
    """Lädt einen nicht gelöschten Termin und prüft die Mitgliedschaft (404 / 403)."""
    snap = await load_snapshot(ctx, appointment_id, lock=lock)
    if snap is None or snap["status"] == "gelöscht":
        raise NotFound("Termin nicht gefunden")
    if not await access.is_effective_member(ctx, snap["team_id"], ctx.person.id):
        raise Forbidden("kein Mitglied des Teams")
    return snap


async def record_change(ctx: Ctx, *, action: str, event_type: str, before: dict | None, after: dict) -> None:
    """Verlaufseintrag und Ereignis (Empfänger: alle effektiven Mitglieder außer dem Aufrufer) zum Zustandswechsel."""
    hid = await history.write(ctx, action=action, object_type="appointment", object_id=after["id"],
                              team_id=after["team_id"], before=before, after=after)
    recipients = await access.recipients_except_actor(ctx, after["team_id"])
    eid = await events.emit(ctx, event_type, recipients, {"appointment_id": after["id"], "title": after["title"]})
    await history.attach_event(ctx, hid, eid)


class AppointmentCreateParams(Params):
    team_id: UUID
    title: str = Field(min_length=1, max_length=200)
    starts_at: UtcTime
    ends_at: UtcTime
    timezone: TimeZoneName = Field(description="IANA-Zeitzonenname, z. B. Europe/Berlin")

    @model_validator(mode="after")
    def _order(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at muss nach starts_at liegen")
        return self


class AppointmentCreateResult(Result):
    appointment_id: str


@operation("appointment.create", "Legt einen Termin (Status geplant) in einem Team an und benachrichtigt alle "
           "effektiven Mitglieder außer dem Aufrufer. Zeiten in UTC (Endung Z).", mutating=True)
async def appointment_create(ctx: Ctx, p: AppointmentCreateParams) -> AppointmentCreateResult:
    await access.require_member(ctx, str(p.team_id))
    aid = str(uuid.uuid4())
    after = {"id": aid, "team_id": str(p.team_id), "title": p.title, "starts_at": fmt_utc(p.starts_at),
             "ends_at": fmt_utc(p.ends_at), "timezone": p.timezone, "status": "geplant"}
    await ctx.db.execute(
        text("INSERT INTO appointment (id, team_id, title, starts_at, ends_at, timezone, status) "
             "VALUES (:id, :team, :title, :starts, :ends, :tz, 'geplant')"),
        {"id": aid, "team": after["team_id"], "title": p.title, "starts": after["starts_at"],
         "ends": after["ends_at"], "tz": p.timezone})
    await record_change(ctx, action="appointment.create", event_type="appointment.created", before=None, after=after)
    return AppointmentCreateResult(appointment_id=aid)


class AppointmentGetParams(Params):
    appointment_id: UUID


class AppointmentGetResult(Result):
    appointment: AppointmentOut


@operation("appointment.get", "Liefert einen Termin (gelöschte Termine sind nicht abrufbar).")
async def appointment_get(ctx: Ctx, p: AppointmentGetParams) -> AppointmentGetResult:
    return AppointmentGetResult(appointment=AppointmentOut(**await _visible(ctx, str(p.appointment_id), lock=False)))


class AppointmentListParams(Params):
    team_id: UUID


class AppointmentListResult(Result):
    appointments: list[AppointmentOut]


@operation("appointment.list", "Listet die Termine eines Teams (inklusive abgesagter, ohne gelöschte), nach "
           "Beginn sortiert.")
async def appointment_list(ctx: Ctx, p: AppointmentListParams) -> AppointmentListResult:
    await access.require_member(ctx, str(p.team_id))
    r = await ctx.db.execute(text(f"SELECT {_COLS} FROM appointment WHERE team_id = :t AND status <> 'gelöscht' "
                                  "ORDER BY starts_at, id"), {"t": str(p.team_id)})
    return AppointmentListResult(appointments=[AppointmentOut(**_snapshot(x)) for x in r])


class AppointmentCancelParams(Params):
    appointment_id: UUID


@operation("appointment.cancel", "Sagt einen geplanten Termin ab und benachrichtigt alle effektiven Mitglieder "
           "außer dem Aufrufer.", mutating=True, preview=True)
async def appointment_cancel(ctx: Ctx, p: AppointmentCancelParams) -> Empty:
    before = await _visible(ctx, str(p.appointment_id))
    if before["status"] != "geplant":
        raise Conflict("Termin ist bereits abgesagt")
    after = {**before, "status": "abgesagt"}
    await store_snapshot(ctx, before["id"], after)
    await record_change(ctx, action="appointment.cancel", event_type="appointment.cancelled", before=before,
                        after=after)
    return Empty()


class AppointmentRescheduleParams(Params):
    appointment_id: UUID
    starts_at: UtcTime
    ends_at: UtcTime

    @model_validator(mode="after")
    def _order(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at muss nach starts_at liegen")
        return self


@operation("appointment.reschedule", "Verschiebt einen geplanten Termin auf neue Zeiten (UTC) und benachrichtigt "
           "alle effektiven Mitglieder außer dem Aufrufer.", mutating=True, preview=True)
async def appointment_reschedule(ctx: Ctx, p: AppointmentRescheduleParams) -> Empty:
    before = await _visible(ctx, str(p.appointment_id))
    if before["status"] != "geplant":
        raise Conflict("Nur geplante Termine lassen sich verschieben")
    after = {**before, "starts_at": fmt_utc(p.starts_at), "ends_at": fmt_utc(p.ends_at)}
    await store_snapshot(ctx, before["id"], after)
    await record_change(ctx, action="appointment.reschedule", event_type="appointment.rescheduled", before=before,
                        after=after)
    return Empty()
