"""Gemeinsame Feldtypen: Zeitpunkte (UTC, Sekunden, Z), Ortszeiten, Zeitzonen, Kanalnamen."""
from datetime import UTC, datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, BeforeValidator, PlainSerializer, WithJsonSchema

Channel = Literal["mock", "email", "webpush"]
CHANNEL_NAMES: tuple[str, ...] = ("mock", "email", "webpush")


def fmt_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(v: object) -> datetime:
    if isinstance(v, datetime):
        dt = v
    elif isinstance(v, str):
        if not v.endswith("Z"):
            raise ValueError("UTC-Zeitpunkt mit Endung Z erwartet")
        dt = datetime.fromisoformat(v)
    else:
        raise ValueError("Zeitpunkt als Zeichenkette erwartet")
    if dt.tzinfo is None:
        raise ValueError("Zeitzone fehlt")
    return dt.astimezone(UTC).replace(microsecond=0)


def _parse_local(v: object) -> datetime:
    if not isinstance(v, str):
        raise ValueError("Ortszeit als Zeichenkette erwartet")
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is not None:
        raise ValueError("Ortszeit ohne Zeitzone erwartet")
    return dt.replace(microsecond=0)


def _check_tz(v: str) -> str:
    try:
        ZoneInfo(v)
    except (ZoneInfoNotFoundError, ValueError, OSError) as e:
        raise ValueError("unbekannte IANA-Zeitzone") from e
    return v


UtcTime = Annotated[
    datetime,
    BeforeValidator(_parse_utc),
    PlainSerializer(fmt_utc, return_type=str),
    WithJsonSchema({"type": "string", "format": "date-time", "description": "UTC, ISO 8601 mit Z"}),
]
LocalTime = Annotated[
    datetime,
    BeforeValidator(_parse_local),
    PlainSerializer(lambda d: d.strftime("%Y-%m-%dT%H:%M:%S"), return_type=str),
    WithJsonSchema({"type": "string", "description": "Ortszeit ohne Zone, z. B. 2026-03-02T18:00:00"}),
]
TimeZoneName = Annotated[str, AfterValidator(_check_tz)]
