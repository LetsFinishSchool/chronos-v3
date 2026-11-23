"""Datenbank: asynchrone Engine (SQLAlchemy 2, psycopg 3), Migration, Hilfen."""
import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib import resources

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from chronos.config import settings
from chronos.logging import log

_engine: AsyncEngine | None = None
_maker: async_sessionmaker[AsyncSession] | None = None


def engine() -> AsyncEngine:
    global _engine, _maker
    if _engine is None:
        _engine = create_async_engine(settings.database_url, pool_size=10, max_overflow=10, pool_pre_ping=True)
        _maker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


@asynccontextmanager
async def session() -> AsyncIterator[AsyncSession]:
    """Eine Sitzung; die aufrufende Stelle steuert die Transaktion (begin/commit/rollback)."""
    engine()
    assert _maker is not None
    async with _maker() as s:
        yield s


async def ping() -> bool:
    try:
        async with engine().connect() as c:
            await c.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - Gesundheitsprüfung darf nie werfen
        return False


async def migrate() -> None:
    sql = resources.files("chronos").joinpath("schema.sql").read_text(encoding="utf-8")
    async with engine().begin() as c:
        await c.execute(text("SELECT pg_advisory_xact_lock(727001)"))
        # Mehrere Anweisungen: einzeln ausführen (psycopg erlaubt mit Parametern nur eine)
        for stmt in (s.strip() for s in sql.split(";\n")):
            if stmt:
                await c.execute(text(stmt.rstrip(";")))
    log.info("Migration abgeschlossen")


async def wait_for_schema(timeout_s: int = 60) -> None:
    """Worker: wartet, bis das Web das Schema angelegt hat."""
    end = time.monotonic() + timeout_s
    while True:
        try:
            async with engine().connect() as c:
                await c.execute(text("SELECT 1 FROM delivery_task LIMIT 1"))
            return
        except Exception as e:  # noqa: BLE001
            if time.monotonic() > end:
                raise
            log.info("warte auf Schema: %s", type(e).__name__)
            await asyncio.sleep(1)


async def conn_scalar(c: AsyncConnection, sql: str, **params):
    return (await c.execute(text(sql), params)).scalar_one_or_none()
