import { createServer } from "node:http";
import { sql, type Kysely } from "kysely";
import { channels } from "../channels/index.js";
import type { ChannelName } from "../core/channels.js";
import { config } from "../core/config.js";
import { createDb, waitForSchema, type Database } from "../core/db.js";
import { rootLog } from "../core/logger.js";

const MAX_ATTEMPTS = 3;
const LEASE_SECONDS = 15;

interface Task { id: string; event_id: string; recipient: string; channels: string[]; channel_idx: number; attempt: number }

async function claim(db: Kysely<Database>, n: number): Promise<Task[]> {
  const r = await sql<Task>`
    update event_recipient set locked_until = now() + make_interval(secs => ${LEASE_SECONDS})
    where id in (select id from event_recipient where status = 'pending' and next_attempt_at <= now() and (locked_until is null or locked_until < now())
                 order by next_attempt_at, id limit ${n} for update skip locked)
    returning id, event_id, recipient, channels, channel_idx, attempt`.execute(db);
  return r.rows;
}

async function handleTask(db: Kysely<Database>, t: Task): Promise<void> {
  const event = await db.selectFrom("event").selectAll().where("id", "=", t.event_id).executeTakeFirstOrThrow();
  const log = rootLog.child({ correlation_id: event.correlation_id, event_id: event.id });
  const channelName = t.channels[t.channel_idx] as ChannelName | undefined;
  if (!channelName || !channels[channelName]) {
    await db.updateTable("event_recipient").set({ status: "done", locked_until: null }).where("id", "=", t.id).execute();
    return;
  }
  const attempt = t.attempt + 1;
  const key = `${event.id}:${t.recipient}:${channelName}`;
  const person = await db.selectFrom("person").select(["id", "email"]).where("id", "=", t.recipient).executeTakeFirstOrThrow();
  const subs = channelName === "webpush"
    ? await db.selectFrom("push_subscription").select(["endpoint", "p256dh", "auth"]).where("person_id", "=", t.recipient).execute() : [];

  let result: "success" | "failed" | "skipped";
  let error: string | null = null;
  try {
    const r = await channels[channelName].deliver({
      eventId: event.id, eventType: event.type, correlationId: event.correlation_id, idempotencyKey: key,
      recipient: { id: person.id, email: person.email, pushSubscriptions: subs },
    });
    result = r === "sent" ? "success" : "skipped";
  } catch (e) {
    result = "failed";
    error = String(e instanceof Error ? e.message : e).slice(0, 500);
  }

  // Nächster Schritt: Erfolg → fertig; übersprungen/erschöpft → nächster Kanal; sonst Wiederholung mit Wartezeit base·2^(n-1)
  let next: { channel_idx: number; attempt: number; status: string; delayMs: number };
  if (result === "success") next = { channel_idx: t.channel_idx, attempt, status: "done", delayMs: 0 };
  else if (result === "skipped" || attempt >= MAX_ATTEMPTS) {
    const idx = t.channel_idx + 1;
    next = { channel_idx: idx, attempt: 0, status: idx >= t.channels.length ? "done" : "pending", delayMs: 0 };
  } else next = { channel_idx: t.channel_idx, attempt, status: "pending", delayMs: config.retryBaseMs * 2 ** (attempt - 1) };

  await db.transaction().execute(async (trx) => {
    await trx.insertInto("delivery").values({
      event_id: event.id, event_type: event.type, correlation_id: event.correlation_id, trigger_kind: event.trigger_kind, trigger_actor: event.trigger_actor,
      recipient: t.recipient, channel: channelName, attempt, result, error, idempotency_key: key,
    }).execute();
    if (result === "success" && channelName === "email") {
      await trx.insertInto("cost_entry").values({
        person_id: event.trigger_actor, provider: "smtp", trigger_kind: "operation", trigger_name: event.operation, correlation_id: event.correlation_id,
        quantity: JSON.stringify({ messages: 1 }), amount_micro_eur: String(config.emailPriceMicroEur),
      }).execute();
    }
    await trx.updateTable("event_recipient").set({
      channel_idx: next.channel_idx, attempt: next.attempt, status: next.status, locked_until: null,
      next_attempt_at: sql<Date>`now() + make_interval(secs => ${next.delayMs / 1000})`,
    }).where("id", "=", t.id).execute();
  });
  log.info({ recipient: t.recipient, channel: channelName, attempt, result, error }, "Zustellversuch");
}

export async function startWorker(): Promise<void> {
  const db = createDb(config.workerConcurrency + 4);
  await waitForSchema(db);

  const health = createServer((req, res) => {
    if (req.url !== "/healthz") { res.writeHead(404).end(); return; }
    sql`select 1`.execute(db).then(
      () => res.writeHead(200, { "Content-Type": "application/json" }).end('{"status":"ok"}'),
      () => res.writeHead(503, { "Content-Type": "application/json" }).end('{"error":{"code":"internal","message":"Datenbank nicht erreichbar"}}'),
    );
  }).listen(config.workerHealthPort, "0.0.0.0");

  let running = true;
  const inflight = new Set<Promise<void>>();
  const stop = () => { running = false; };
  process.on("SIGTERM", stop);
  process.on("SIGINT", stop);
  rootLog.info({ concurrency: config.workerConcurrency }, "worker gestartet");

  const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
  while (running) {
    const free = config.workerConcurrency - inflight.size;
    if (free <= 0) { await Promise.race(inflight); continue; }
    let tasks: Task[] = [];
    try {
      tasks = await claim(db, free);
    } catch (e) {
      rootLog.error({ err: String(e) }, "Abholen fehlgeschlagen");
    }
    for (const t of tasks) {
      const p: Promise<void> = handleTask(db, t)
        .catch((e) => rootLog.error({ err: String(e), event_id: t.event_id }, "Zustellung fehlgeschlagen (Lease läuft ab, späterer Wiederanlauf)"))
        .finally(() => inflight.delete(p));
      inflight.add(p);
    }
    if (tasks.length === 0) await sleep(150);
  }
  await Promise.allSettled(inflight);
  health.close();
  await db.destroy();
}

