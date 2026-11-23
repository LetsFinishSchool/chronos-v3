"""Benachrichtigungen: Kanaleinstellung, Push-Abo, Test-Push, Zustellprotokoll, Kostenposten."""
import json
from typing import Annotated, Any
from uuid import UUID

from pydantic import AfterValidator, Field
from sqlalchemy import text

from chronos.core import events
from chronos.core.context import Ctx
from chronos.core.types import Channel, fmt_utc
from chronos.ops.registry import Empty, Params, Result, operation


def _dedupe(v: list[str]) -> list[str]:
    return list(dict.fromkeys(v))


class SetChannelsParams(Params):
    channels: Annotated[list[Channel], Field(min_length=1), AfterValidator(_dedupe)]


@operation("notification.set_channels", "Setzt die geordnete Kanalliste des Aufrufers (mock, email, webpush); "
           "der nächste Kanal ist jeweils der Ersatzkanal.", mutating=True)
async def set_channels(ctx: Ctx, p: SetChannelsParams) -> Empty:
    await ctx.db.execute(text("UPDATE person SET channels = CAST(:c AS jsonb) WHERE id = :id"),
                         {"c": json.dumps(p.channels), "id": ctx.person.id})
    return Empty()


class SubscribePushParams(Params):
    endpoint: str = Field(pattern=r"^https://\S+$", description="https-URL des Push-Dienstes")
    p256dh: str = Field(min_length=1)
    auth: str = Field(min_length=1)


@operation("notification.subscribe_push", "Speichert ein Web-Push-Abonnement des Aufrufers.", mutating=True)
async def subscribe_push(ctx: Ctx, p: SubscribePushParams) -> Empty:
    await ctx.db.execute(
        text("INSERT INTO push_subscription (person_id, endpoint, p256dh, auth) VALUES (:p, :e, :k, :a) "
             "ON CONFLICT (person_id, endpoint) DO UPDATE SET p256dh = EXCLUDED.p256dh, auth = EXCLUDED.auth"),
        {"p": ctx.person.id, "e": p.endpoint, "k": p.p256dh, "a": p.auth})
    return Empty()


class PushTestParams(Params):
    pass


class PushTestResult(Result):
    event_id: str


@operation("notification.test_push", "Erzeugt das Ereignis notification.test nur für den Aufrufer, zugestellt "
           "ausschließlich über Web Push (unabhängig von der Kanaleinstellung).", mutating=True)
async def test_push(ctx: Ctx, p: PushTestParams) -> PushTestResult:
    eid = await events.emit(ctx, "notification.test", [ctx.person.id], {"channels": ["webpush"]})
    return PushTestResult(event_id=eid)


class Trigger(Result):
    kind: str
    actor: str


class Delivery(Result):
    event_id: str
    event_type: str
    correlation_id: str
    trigger: Trigger
    recipient: str
    channel: str
    attempt: int
    result: str
    error: str | None
    at: str
    idempotency_key: str


class NotificationListParams(Params):
    event_id: UUID | None = None
    correlation_id: str | None = Field(default=None, max_length=64)
    limit: int = Field(default=100, ge=1, le=500)


class NotificationListResult(Result):
    deliveries: list[Delivery]


@operation("notification.list", "Zustellprotokoll (eine Zeile je Versuch, älteste zuerst) der Ereignisse, die der "
           "Aufrufer ausgelöst hat oder bei denen er Empfänger ist.")
async def notification_list(ctx: Ctx, p: NotificationListParams) -> NotificationListResult:
    r = await ctx.db.execute(
        text("SELECT * FROM (SELECT d.id, d.event_id::text AS event_id, e.type, d.correlation_id, e.trigger_kind, "
             "e.actor, d.recipient, d.channel, d.attempt, d.result, d.error, d.at, d.idempotency_key "
             "FROM delivery d JOIN event e ON e.id = d.event_id "
             "WHERE (e.actor = :me OR d.recipient = :me) "
             "AND (CAST(:eid AS uuid) IS NULL OR d.event_id = CAST(:eid AS uuid)) "
             "AND (CAST(:corr AS text) IS NULL OR d.correlation_id = CAST(:corr AS text)) "
             "ORDER BY d.id DESC LIMIT :lim) newest ORDER BY id"),
        {"me": ctx.person.id, "eid": str(p.event_id) if p.event_id else None, "corr": p.correlation_id,
         "lim": p.limit})
    return NotificationListResult(deliveries=[
        Delivery(event_id=x.event_id, event_type=x.type, correlation_id=x.correlation_id,
                 trigger=Trigger(kind=x.trigger_kind, actor=x.actor), recipient=x.recipient, channel=x.channel,
                 attempt=x.attempt, result=x.result, error=x.error, at=fmt_utc(x.at),
                 idempotency_key=x.idempotency_key) for x in r])


class CostTrigger(Result):
    kind: str
    name: str
    correlation_id: str


class CostEntry(Result):
    id: str
    at: str
    person_id: str
    provider: str
    trigger: CostTrigger
    quantity: dict[str, Any]
    amount_micro_eur: int


class CostListParams(Params):
    limit: int = Field(default=100, ge=1, le=500)


class CostListResult(Result):
    entries: list[CostEntry]


@operation("cost.list", "Listet die Kostenposten des Aufrufers als Verursacher (neueste zuerst).")
async def cost_list(ctx: Ctx, p: CostListParams) -> CostListResult:
    r = await ctx.db.execute(
        text("SELECT id::text AS id, at, person_id, provider, trigger_kind, trigger_name, correlation_id, quantity, "
             "amount_micro_eur FROM cost WHERE person_id = :me ORDER BY id DESC LIMIT :lim"),
        {"me": ctx.person.id, "lim": p.limit})
    return CostListResult(entries=[
        CostEntry(id=x.id, at=fmt_utc(x.at), person_id=x.person_id, provider=x.provider,
                  trigger=CostTrigger(kind=x.trigger_kind, name=x.trigger_name, correlation_id=x.correlation_id),
                  quantity=x.quantity, amount_micro_eur=x.amount_micro_eur) for x in r])
