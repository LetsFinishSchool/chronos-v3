"""Kanal webpush: VAPID und verschlüsselte Nutzlast ausschließlich durch die Bibliothek pywebpush."""
import asyncio
import json

from py_vapid import Vapid
from pywebpush import WebPushException, webpush
from sqlalchemy import text

from chronos import db
from chronos.channels.base import ChannelError, Message, Skipped
from chronos.config import settings

name = "webpush"
_vapid: Vapid | None = None


def _send_sync(sub: dict, data: str) -> None:
    global _vapid
    if _vapid is None:
        _vapid = Vapid.from_raw(settings.vapid_private_key.encode())
    webpush(subscription_info=sub, data=data, vapid_private_key=_vapid,
            vapid_claims={"sub": settings.vapid_subject}, timeout=10)


async def deliver(msg: Message) -> None:
    async with db.session() as s:
        subs = (await s.execute(text("SELECT endpoint, p256dh, auth FROM push_subscription WHERE person_id = :p"),
                                {"p": msg.recipient})).all()
    if not subs:
        raise Skipped("kein Web-Push-Abo")
    data = json.dumps({"event_type": msg.event_type, "event_id": msg.event_id})
    errors = []
    for sub in subs:
        info = {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}}
        try:
            await asyncio.to_thread(_send_sync, info, data)
        except (WebPushException, OSError, ValueError) as e:
            errors.append(f"{type(e).__name__}")
    if len(errors) == len(subs):
        raise ChannelError("Web Push fehlgeschlagen: " + ",".join(errors))
