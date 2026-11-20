import { randomUUID } from "node:crypto";
import { z } from "zod";
import { defineOperation } from "../../core/operation.js";
import { CHANNEL_NAMES } from "../../core/channels.js";
import { insertEvent } from "../changes.js";
import { fmtUtc, utcTime, uuid } from "../schemas.js";

defineOperation({
  name: "notification.set_channels",
  description: "Setzt die geordnete Liste der Benachrichtigungskanäle des Aufrufers (mock, email, webpush); bei Ausfall folgt der nächste Kanal.",
  mutating: true,
  params: z.strictObject({ channels: z.array(z.enum(CHANNEL_NAMES)).min(1) }),
  result: z.object({}),
  async run(ctx, p) {
    const channels = [...new Set(p.channels)];
    await ctx.db.updateTable("person").set({ channels }).where("id", "=", ctx.caller.id).execute();
    ctx.affected.push({ type: "person", id: ctx.caller.id, change: `Kanäle: ${channels.join(", ")}` });
    return {};
  },
});

defineOperation({
  name: "notification.subscribe_push",
  description: "Speichert ein Web-Push-Abo des Aufrufers (Endpunkt, p256dh, auth).",
  mutating: true,
  params: z.strictObject({ endpoint: z.string().regex(/^https:\/\/\S+$/, "https-URL erwartet"), p256dh: z.string().min(1), auth: z.string().min(1) }),
  result: z.object({}),
  async run(ctx, p) {
    await ctx.db.insertInto("push_subscription").values({ person_id: ctx.caller.id, endpoint: p.endpoint, p256dh: p.p256dh, auth: p.auth })
      .onConflict((oc) => oc.columns(["person_id", "endpoint"]).doUpdateSet({ p256dh: p.p256dh, auth: p.auth })).execute();
    ctx.affected.push({ type: "person", id: ctx.caller.id, change: "Web-Push-Abo wird gespeichert" });
    return {};
  },
});

defineOperation({
  name: "notification.test_push",
  description: "Erzeugt ein Testereignis (notification.test) nur für den Aufrufer, zugestellt ausschließlich über Web Push.",
  mutating: true,
  params: z.strictObject({}),
  result: z.object({ event_id: uuid }),
  async run(ctx) {
    const id = randomUUID();
    await insertEvent(ctx, id, { type: "notification.test", recipients: [ctx.caller.id], channels: ["webpush"] });
    ctx.affected.push({ type: "event", id, change: "Test-Push wird ausgelöst" });
    return { event_id: id };
  },
});

const deliverySchema = z.object({
  event_id: uuid, event_type: z.string(), correlation_id: z.string(), trigger: z.object({ kind: z.string(), actor: z.string() }),
  recipient: z.string(), channel: z.enum(CHANNEL_NAMES), attempt: z.number().int(), result: z.enum(["success", "failed", "skipped"]),
  error: z.string().optional(), at: utcTime, idempotency_key: z.string(),
});

defineOperation({
  name: "notification.list",
  description: "Zustellprotokoll (je Versuch eine Zeile, älteste zuerst) der Ereignisse, die der Aufrufer ausgelöst hat oder bei denen er Empfänger ist.",
  mutating: false,
  params: z.strictObject({ event_id: uuid.optional(), correlation_id: z.string().optional(), limit: z.number().int().min(1).max(500).optional() }),
  result: z.object({ deliveries: z.array(deliverySchema) }),
  async run(ctx, p) {
    let q = ctx.db.selectFrom("delivery").selectAll().where((eb) => eb.or([eb("trigger_actor", "=", ctx.caller.id), eb("recipient", "=", ctx.caller.id)]));
    if (p.event_id) q = q.where("event_id", "=", p.event_id);
    if (p.correlation_id) q = q.where("correlation_id", "=", p.correlation_id);
    const rows = await q.orderBy("id").limit(p.limit ?? 100).execute();
    return {
      deliveries: rows.map((r) => ({
        event_id: r.event_id, event_type: r.event_type, correlation_id: r.correlation_id, trigger: { kind: r.trigger_kind, actor: r.trigger_actor },
        recipient: r.recipient, channel: r.channel as (typeof CHANNEL_NAMES)[number], attempt: r.attempt, result: r.result as "success" | "failed" | "skipped",
        ...(r.error ? { error: r.error } : {}), at: fmtUtc(new Date(r.at)), idempotency_key: r.idempotency_key,
      })),
    };
  },
});

defineOperation({
  name: "cost.list",
  description: "Listet die Kostenposten des Aufrufers als Verursacher (neueste zuerst).",
  mutating: false,
  params: z.strictObject({ limit: z.number().int().min(1).max(500).optional() }),
  result: z.object({
    entries: z.array(z.object({
      id: z.string(), at: utcTime, person_id: z.string(), provider: z.enum(["anthropic", "smtp"]),
      trigger: z.object({ kind: z.string(), name: z.string(), correlation_id: z.string() }),
      quantity: z.record(z.string(), z.number()), amount_micro_eur: z.number().int(),
    })),
  }),
  async run(ctx, p) {
    const rows = await ctx.db.selectFrom("cost_entry").selectAll().where("person_id", "=", ctx.caller.id).orderBy("id", "desc").limit(p.limit ?? 100).execute();
    return {
      entries: rows.map((r) => ({
        id: r.id, at: fmtUtc(new Date(r.at)), person_id: r.person_id, provider: r.provider as "anthropic" | "smtp",
        trigger: { kind: r.trigger_kind, name: r.trigger_name, correlation_id: r.correlation_id },
        quantity: r.quantity as Record<string, number>, amount_micro_eur: Number(r.amount_micro_eur),
      })),
    };
  },
});
