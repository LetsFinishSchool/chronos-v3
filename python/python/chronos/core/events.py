"""Ereignisse: werden in derselben Transaktion wie Zustand und Verlauf geschrieben; der Worker liest sie aus der DB."""
import json
import uuid

from sqlalchemy import text

from chronos.config import settings
from chronos.core.context import Ctx


async def emit(ctx: Ctx, event_type: str, recipients: list[str], payload: dict | None = None) -> str:
    """Schreibt Ereignis und je Empfänger eine Zustellaufgabe. Gibt die Ereignis-ID zurück."""
    if settings.spike_faults and ctx.fault == "after_history":
        raise RuntimeError("Fehlerinjektion after_history")
    event_id = str(uuid.uuid4())
    await ctx.db.execute(
        text("INSERT INTO event (id, type, trigger_kind, actor, operation, correlation_id, recipients, payload) "
             "VALUES (:id, :type, 'person', :actor, :op, :corr, CAST(:rcpt AS jsonb), CAST(:payload AS jsonb))"),
        {"id": event_id, "type": event_type, "actor": ctx.person.id, "op": ctx.operation, "corr": ctx.correlation_id,
         "rcpt": json.dumps(recipients), "payload": json.dumps(payload or {})},
    )
    if recipients:
        await ctx.db.execute(
            text("INSERT INTO delivery_task (event_id, recipient) SELECT :e, unnest(CAST(:r AS text[]))"),
            {"e": event_id, "r": recipients},
        )
    return event_id
