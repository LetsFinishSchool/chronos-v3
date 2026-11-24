import { randomUUID } from "node:crypto";
import type { Ctx } from "../core/operation.js";
import { AppError } from "../core/errors.js";
import { effectiveMembers } from "./access.js";

export interface ChangeEvent {
  type: string;
  recipients: string[];
  /** Kanalliste statt der Einstellung der Person (z. B. Test-Push nur über webpush). */
  channels?: string[];
}

export interface Change {
  action: string;
  objectType: string;
  objectId: string;
  teamId: string;
  before: unknown;
  after: unknown;
  /** Text für die Vorschau. */
  change: string;
  event?: ChangeEvent;
  undoOf?: string;
}

/** Alle effektiven Mitglieder des Teams außer dem Aufrufer. */
export async function teamRecipients(ctx: Ctx, teamId: string): Promise<string[]> {
  return (await effectiveMembers(ctx.db, teamId)).map((m) => m.person_id).filter((id) => id !== ctx.caller.id);
}

/** Schreibt Verlaufseintrag UND Ereignis (mit Empfängern) in der Transaktion des Aufrufs. Gibt die Verlauf-ID zurück. */
export async function recordChange(ctx: Ctx, c: Change): Promise<string> {
  ctx.affected.push({ type: c.objectType, id: c.objectId, change: c.change });
  const historyId = randomUUID();
  const eventId = c.event ? randomUUID() : null;
  await ctx.db.insertInto("history").values({
    id: historyId, actor: ctx.caller.id, action: c.action, object_type: c.objectType, object_id: c.objectId, team_id: c.teamId,
    before: c.before == null ? null : JSON.stringify(c.before), after: c.after == null ? null : JSON.stringify(c.after),
    bundle_id: ctx.bundleId, correlation_id: ctx.correlationId, undo_of: c.undoOf ?? null, event_id: null,
  }).execute();
  if (ctx.faultAfterHistory) throw new AppError("internal", "Fehlerinjektion after_history");
  if (c.event && eventId) {
    await insertEvent(ctx, eventId, c.event);
    await ctx.db.updateTable("history").set({ event_id: eventId }).where("id", "=", historyId).execute();
  }
  return historyId;
}

export async function insertEvent(ctx: Ctx, eventId: string, e: ChangeEvent): Promise<void> {
  await ctx.db.insertInto("event").values({
    id: eventId, type: e.type, trigger_kind: "person", trigger_actor: ctx.caller.id, operation: ctx.operation, correlation_id: ctx.correlationId,
  }).execute();
  if (e.recipients.length === 0) return;
  const people = await ctx.db.selectFrom("person").select(["id", "channels"]).where("id", "in", e.recipients).execute();
  const rows = people.map((p) => ({ event_id: eventId, recipient: p.id, channels: e.channels ?? p.channels }));
  if (rows.length) await ctx.db.insertInto("event_recipient").values(rows).execute();
}
