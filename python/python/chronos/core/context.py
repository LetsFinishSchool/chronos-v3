"""Aufrufkontext einer Operation: eine Datenbanktransaktion, Aufrufer, Korrelations-ID, Vorschau-Sammler."""
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class Person:
    id: str
    name: str
    email: str


@dataclass
class Ctx:
    db: AsyncSession
    person: Person
    correlation_id: str
    operation: str
    preview: bool = False
    fault: str | None = None  # Wert des Headers X-Spike-Fault (nur wirksam mit SPIKE_FAULTS=1)
    affected: list[dict] = field(default_factory=list)
