"""Fachbereich Verlauf: Abfrage und Rückgängig (die Logik liegt in chronos.core.history)."""
from typing import Any
from uuid import UUID

from pydantic import Field

from chronos.core import history
from chronos.core.context import Ctx
from chronos.ops.registry import Params, Result, operation


class HistoryEntry(Result):
    id: str
    at: str
    actor: str
    action: str
    object_type: str
    object_id: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    bundle_id: str
    correlation_id: str
    undone: bool
    undo_of: str | None


class HistoryListParams(Params):
    object_id: UUID | None = None
    limit: int = Field(default=50, ge=1, le=200)


class HistoryListResult(Result):
    entries: list[HistoryEntry]


@operation("history.list", "Listet Verlaufseinträge (neueste zuerst) zu Objekten in Teams, in denen der Aufrufer "
           "Mitglied ist; optional für ein Objekt.")
async def history_list(ctx: Ctx, p: HistoryListParams) -> HistoryListResult:
    rows = await history.list_entries(ctx, str(p.object_id) if p.object_id else None, p.limit)
    return HistoryListResult(entries=[HistoryEntry(**r) for r in rows])


class HistoryUndoParams(Params):
    history_id: UUID


class HistoryUndoResult(Result):
    history_id: str


@operation("history.undo", "Macht eine Änderung rückgängig (stellt den Zustand vor dem Eintrag wieder her), sofern "
           "das Objekt seither unverändert ist.", mutating=True, preview=True)
async def history_undo(ctx: Ctx, p: HistoryUndoParams) -> HistoryUndoResult:
    return HistoryUndoResult(history_id=await history.undo(ctx, str(p.history_id)))
