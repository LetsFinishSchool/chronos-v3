"""Verlauf mit Zustandsabbildern und Rückgängig. Objekttypen melden sich an (Registry), kein Typ ist fest verdrahtet."""
import json
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import text

from chronos.core.context import Ctx
from chronos.core.errors import Forbidden, NotFound, NotUndoable

Snapshot = dict[str, Any]


class ObjectType:
    """Wie ein Objekttyp geladen und wiederhergestellt wird (Zustandsabbild = vollständiger Zustand)."""

    def __init__(self, load: Callable[[Ctx, str], Awaitable[Snapshot | None]],
                 store: Callable[[Ctx, str, Snapshot], Awaitable[None]]) -> None:
        self.load, self.store = load, store


OBJECT_TYPES: dict[str, ObjectType] = {}


def register_object_type(name: str, load, store) -> None:
    OBJECT_TYPES[name] = ObjectType(load, store)


async def write(ctx: Ctx, *, action: str, object_type: str, object_id: str, team_id: str,
                before: Snapshot | None, after: Snapshot | None, bundle_id: str | None = None,
                undo_of: str | None = None, event_id: str | None = None) -> str:
    hid = str(uuid.uuid4())
    await ctx.db.execute(
        text("INSERT INTO history (id, actor, action, object_type, object_id, team_id, before, after, bundle_id, "
             "correlation_id, undo_of, event_id) VALUES (:id, :actor, :action, :ot, :oid, :tid, "
             "CAST(:before AS jsonb), CAST(:after AS jsonb), :bundle, :corr, :undo_of, :event_id)"),
        {"id": hid, "actor": ctx.person.id, "action": action, "ot": object_type, "oid": object_id, "tid": team_id,
         "before": json.dumps(before), "after": json.dumps(after), "bundle": bundle_id or str(uuid.uuid4()),
         "corr": ctx.correlation_id, "undo_of": undo_of, "event_id": event_id},
    )
    ctx.affected.append({"type": object_type, "id": object_id, "change": action})
    return hid


async def attach_event(ctx: Ctx, history_id: str, event_id: str) -> None:
    await ctx.db.execute(text("UPDATE history SET event_id = :e WHERE id = :h"), {"e": event_id, "h": history_id})


def _entry(row) -> dict:
    return {
        "id": row.id, "at": row.at.strftime("%Y-%m-%dT%H:%M:%SZ"), "actor": row.actor, "action": row.action,
        "object_type": row.object_type, "object_id": row.object_id, "before": row.before, "after": row.after,
        "bundle_id": row.bundle_id, "correlation_id": row.correlation_id, "undone": row.undone, "undo_of": row.undo_of,
    }


_COLS = ("id::text AS id, at, actor, action, object_type, object_id::text AS object_id, before, after, "
         "bundle_id::text AS bundle_id, correlation_id, undone, undo_of::text AS undo_of")


async def list_entries(ctx: Ctx, object_id: str | None, limit: int) -> list[dict]:
    """Neueste zuerst; nur Objekte in Teams, in denen der Aufrufer (effektiv) Mitglied ist."""
    from chronos.core.access import EFFECTIVE_TEAMS_CTE
    r = await ctx.db.execute(
        text(EFFECTIVE_TEAMS_CTE + f"SELECT {_COLS} FROM history h WHERE h.team_id IN (SELECT id FROM eff) "
             "AND (CAST(:oid AS uuid) IS NULL OR h.object_id = CAST(:oid AS uuid)) ORDER BY h.seq DESC LIMIT :lim"),
        {"person_id": ctx.person.id, "oid": object_id, "lim": limit},
    )
    return [_entry(row) for row in r]


async def undo(ctx: Ctx, history_id: str) -> str:
    """Stellt `before` wieder her, sofern der aktuelle Zustand gleich `after` des Eintrags ist."""
    from chronos.core.access import is_effective_member
    row = (await ctx.db.execute(
        text(f"SELECT {_COLS}, team_id::text AS team_id, event_id::text AS event_id FROM history WHERE id = :id "
             "FOR UPDATE"), {"id": history_id})).first()
    if row is None:
        raise NotFound("Verlaufseintrag nicht gefunden")
    if not await is_effective_member(ctx, row.team_id, ctx.person.id):
        raise Forbidden("kein Mitglied des Teams")
    if row.undone:
        raise NotUndoable("Eintrag wurde bereits rückgängig gemacht")
    ot = OBJECT_TYPES[row.object_type]
    current = await ot.load(ctx, row.object_id)
    if current != row.after:
        raise NotUndoable("Der Zustand des Objekts hat sich seit dem Eintrag geändert")
    target = row.before if row.before is not None else {**row.after, "status": "gelöscht"}
    await ot.store(ctx, row.object_id, target)
    await ctx.db.execute(text("UPDATE history SET undone = true WHERE id = :id"), {"id": history_id})
    new_id = await write(ctx, action="history.undo", object_type=row.object_type, object_id=row.object_id,
                         team_id=row.team_id, before=current, after=target, undo_of=history_id,
                         bundle_id=row.bundle_id)
    if row.event_id:
        recipients = (await ctx.db.execute(text("SELECT recipients FROM event WHERE id = :e"),
                                           {"e": row.event_id})).scalar_one()
        from chronos.core.events import emit
        eid = await emit(ctx, "change.reverted", list(recipients), {"history_id": history_id})
        await attach_event(ctx, new_id, eid)
    return new_id
