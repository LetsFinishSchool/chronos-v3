"""Kanalschnittstelle: ein Kanal stellt eine Nachricht zu oder wirft ChannelError / Skipped."""
from dataclasses import dataclass, field
from typing import Any, Protocol


class ChannelError(Exception):
    """Zustellung fehlgeschlagen (wird wiederholt, danach Ersatzkanal)."""


class Skipped(Exception):
    """Voraussetzung fehlt (z. B. kein Push-Abo): Zeile `skipped`, weiter zum nächsten Kanal."""


@dataclass(frozen=True)
class Message:
    recipient: str
    recipient_email: str
    event_type: str
    event_id: str
    correlation_id: str
    idempotency_key: str
    payload: dict[str, Any] = field(default_factory=dict)


class Channel(Protocol):
    name: str
    async def deliver(self, msg: Message) -> None: ...
