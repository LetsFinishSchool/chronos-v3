"""Zustellung: Aufgaben aus der Datenbank holen, je Empfänger Kanäle der Reihe nach, Wiederholung, Ersatzkanal.

Fortschritt (Kanalindex, Versuch, nächster Zeitpunkt) liegt in `delivery_task`; nach SIGKILL setzt ein neuer Worker
nach Ablauf der Sperre (`lease_until`) genau dort fort. Doppelte Versuche tragen denselben Idempotenzschlüssel.
"""
import asyncio
import json
from dataclasses import dataclass

from sqlalchemy import text

from chronos import db
from chronos.channels import CHANNELS
from chronos.channels.base import ChannelError, Message, Skipped
from chronos.config import settings
from chronos.logging import correlation_id_var, event_id_var, log

MAX_ATTEMPTS = 3
LEASE_SECONDS = 8
CONCURRENCY = 16


@dataclass(frozen=True)
class Task:
    event_id: str
    recipient: str
    channel_idx: int
    attempt: int


# EIGENBAU:BEGIN Auftragswarteschlange auf PostgreSQL (SKIP LOCKED, Sperre, Wiederholung statt Auftragsbibliothek)
async def claim(limit: int) -> list[Task]:
    async with db.session() as s, s.begin():
        rows = (await s.execute(
            text("UPDATE delivery_task t SET lease_until = now() + make_interval(secs => :lease) FROM ("
                 "SELECT event_id, recipient FROM delivery_task WHERE status = 'pending' AND next_at <= now() "
                 "AND (lease_until IS NULL OR lease_until < now()) ORDER BY next_at LIMIT :n "
                 "FOR UPDATE SKIP LOCKED) c WHERE t.event_id = c.event_id AND t.recipient = c.recipient "
                 "RETURNING t.event_id::text AS event_id, t.recipient, t.channel_idx, t.attempt"),
            {"lease": LEASE_SECONDS, "n": limit})).all()
    return [Task(r.event_id, r.recipient, r.channel_idx, r.attempt) for r in rows]


async def process(task: Task) -> None:
    """Führt EINEN Versuch aus und schreibt Zustellzeile und neuen Fortschritt in einer Transaktion."""
    event_id_var.set(task.event_id)
    async with db.session() as s:
        ev = (await s.execute(
            text("SELECT type, actor, operation, correlation_id, payload FROM event WHERE id = :e"),
            {"e": task.event_id})).one()
        person = (await s.execute(text("SELECT email, channels FROM person WHERE id = :p"),
                                  {"p": task.recipient})).first()
    correlation_id_var.set(ev.correlation_id)
    channels: list[str] = ev.payload.get("channels") or (person.channels if person else [])
    if task.channel_idx >= len(channels):
        await _finish(task, None)
        return
    channel_name = channels[task.channel_idx]
    attempt = task.attempt + 1
    key = f"{task.event_id}:{task.recipient}:{channel_name}"
    msg = Message(task.recipient, person.email if person else "", ev.type, task.event_id, ev.correlation_id, key,
                  ev.payload)
    result, error = "success", None
    try:
        await CHANNELS[channel_name].deliver(msg)
    except Skipped as e:
        result, error = "skipped", str(e)
    except ChannelError as e:
        result, error = "failed", str(e)
    except Exception as e:  # noqa: BLE001 - jeder Kanalfehler zählt als fehlgeschlagener Versuch
        log.exception("Kanal %s warf unerwartet", channel_name)
        result, error = "failed", f"{type(e).__name__}: {e}"
    log.info("Zustellung %s über %s Versuch %d: %s", task.recipient, channel_name, attempt, result)

    async with db.session() as s, s.begin():
        await s.execute(
            text("INSERT INTO delivery (event_id, recipient, channel, attempt, result, error, idempotency_key, "
                 "correlation_id) VALUES (:e, :r, :c, :a, :res, :err, :k, :corr)"),
            {"e": task.event_id, "r": task.recipient, "c": channel_name, "a": attempt, "res": result, "err": error,
             "k": key, "corr": ev.correlation_id})
        if result == "success" and channel_name == "email":
            await s.execute(
                text("INSERT INTO cost (person_id, provider, trigger_kind, trigger_name, correlation_id, quantity, "
                     "amount_micro_eur) VALUES (:p, 'smtp', 'operation', :op, :corr, CAST(:q AS jsonb), :amt)"),
                {"p": ev.actor, "op": ev.operation, "corr": ev.correlation_id, "q": json.dumps({"messages": 1}),
                     "amt": settings.email_price})
        last_channel = task.channel_idx + 1 >= len(channels)
        if result == "success":
            nxt = "status = 'done', lease_until = NULL"
        elif result == "skipped" or attempt >= MAX_ATTEMPTS:
            # nächster Kanal (Ersatzkanal); war es der letzte, ist die Zustellung endgültig beendet
            nxt = "channel_idx = channel_idx + 1, attempt = 0, next_at = now(), lease_until = NULL"
            if last_channel:
                nxt += ", status = 'done'"
        else:
            wait_ms = settings.retry_base_ms * 2 ** (attempt - 1)
            nxt = f"attempt = {attempt}, next_at = now() + make_interval(secs => {wait_ms / 1000}), lease_until = NULL"
        await s.execute(text(f"UPDATE delivery_task SET {nxt} WHERE event_id = :e AND recipient = :r"),
                        {"e": task.event_id, "r": task.recipient})


async def _finish(task: Task, _: None) -> None:
    async with db.session() as s, s.begin():
        await s.execute(text("UPDATE delivery_task SET status = 'done', lease_until = NULL "
                             "WHERE event_id = :e AND recipient = :r"), {"e": task.event_id, "r": task.recipient})
# EIGENBAU:END


# EIGENBAU:BEGIN Schleife der Warteschlange
async def _guarded(task: Task, sem: asyncio.Semaphore) -> None:
    try:
        await process(task)
    except Exception:  # noqa: BLE001 - Aufgabe bleibt gesperrt und wird nach Ablauf der Sperre erneut versucht
        log.exception("Verarbeitung von %s/%s gescheitert", task.event_id, task.recipient)
    finally:
        sem.release()


async def release_stale_leases() -> None:
    """Start: Sperren eines abgestürzten Vorgängers sofort freigeben (Annahme: ein Worker-Prozess)."""
    async with db.session() as s, s.begin():
        n = (await s.execute(text("UPDATE delivery_task SET lease_until = NULL WHERE status = 'pending' "
                                  "AND lease_until IS NOT NULL"))).rowcount
    log.info("Sperren freigegeben: %d", n)


async def run_loop() -> None:
    await release_stale_leases()
    sem = asyncio.Semaphore(CONCURRENCY)
    running: set[asyncio.Task] = set()
    while True:
        free = CONCURRENCY - len(running)
        try:
            tasks = await claim(free) if free > 0 else []
        except Exception:  # noqa: BLE001 - Datenbank kurz weg: weiter versuchen
            log.exception("Abholen fehlgeschlagen")
            tasks = []
            await asyncio.sleep(1)
        for t in tasks:
            await sem.acquire()
            fut = asyncio.create_task(_guarded(t, sem))
            running.add(fut)
            fut.add_done_callback(running.discard)
        if not tasks:
            await asyncio.sleep(0.1)
# EIGENBAU:END
