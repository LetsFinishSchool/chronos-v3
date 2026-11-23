"""Kanal mock: POST an den Mock-Kanal mit Idempotency-Key."""
import httpx

from chronos.channels.base import ChannelError, Message
from chronos.config import settings

name = "mock"
_client: httpx.AsyncClient | None = None


async def deliver(msg: Message) -> None:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=10)
    try:
        r = await _client.post(
            f"{settings.mock_channel_url}/deliver",
            json={"recipient": msg.recipient, "event_type": msg.event_type, "event_id": msg.event_id,
                  "correlation_id": msg.correlation_id},
            headers={"Idempotency-Key": msg.idempotency_key})
    except httpx.HTTPError as e:
        raise ChannelError(f"Mock-Kanal nicht erreichbar: {type(e).__name__}") from e
    if not r.is_success:
        raise ChannelError(f"Mock-Kanal antwortete {r.status_code}")
