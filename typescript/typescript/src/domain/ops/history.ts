import { isDeepStrictEqual } from "node:util";
import { z } from "zod";
import { sql } from "kysely";
import { defineOperation } from "../../core/operation.js";
import { AppError } from "../../core/errors.js";
import { requireMember } from "../access.js";
import { recordChange } from "../changes.js";
import { restorable } from "../restore.js";
import { utcTime, uuid, fmtUtc } from "../schemas.js";

const entrySchema = z.object({
  id: uuid, at: utcTime, actor: z.string(), action: z.string(), object_type: z.string(), object_id: uuid,
  before: z.unknown().nullable(), after: z.unknown().nullable(), bundle_id: uuid, correlation_id: z.string(),
  undone: z.boolean(), undo_of: uuid.nullable(),
});

defineOperation({
  name: "history.list",
  description: "Listet Verlaufseinträge (neueste zuerst) zu Objekten in Teams, in denen der Aufrufer Mitglied ist; optional für ein Objekt.",
  mutating: false,
  params: z.strictObject({ object_id: uuid.optional(), limit: z.number().int().min(1).max(200).optional() }),
  result: z.object({ entries: z.array(entrySchema) }),
  async run(ctx, p) {
    let q = ctx.db.selectFrom("history").selectAll()
      .where(sql<boolean>`team_id in (
        with recursive up as (
          select t.id, t.parent_id from team t join team_member m on m.team_id = t.id where m.person_id = ${ctx.caller.id}
          union select p.id, p.parent_id from team p join up on up.parent_id = p.id)
        select id from up)`);
    if (p.object_id) q = q.where("object_id", "=", p.object_id);
    const rows = await q.orderBy("seq", "desc").limit(p.limit ?? 50).execute();
    return {
      entries: rows.map((r) => ({
        id: r.id, at: fmtUtc(new Date(r.at)), actor: r.actor, action: r.action, object_type: r.object_type, object_id: r.object_id,
        before: r.before ?? null, after: r.after ?? null, bundle_id: r.bundle_id, correlation_id: r.correlation_id, undone: r.undone, undo_of: r.undo_of,
      })),
    };
  },
});

defineOperation({
  name: "history.undo",
  description: "Macht einen Verlaufseintrag rückgängig (stellt den Zustand davor wieder her), sofern das Objekt noch im Zustand nach dem Eintrag ist. Ein Rückgängig lässt sich selbst rückgängig machen.",
  mutating: true,
  params: z.strictObject({ history_id: uuid }),
  result: z.object({ history_id: uuid }),
  async run(ctx, p) {
    const e = await ctx.db.selectFrom("history").selectAll().where("id", "=", p.history_id).forUpdate().executeTakeFirst();
    if (!e) throw new AppError("not_found", "Verlaufseintrag nicht gefunden");
    await requireMember(ctx, e.team_id);
    const kind = restorable[e.object_type];
    if (!kind) throw new AppError("not_undoable", `Objektart ${e.object_type} ist nicht rückgängig zu machen`);
    if (e.undone) throw new AppError("not_undoable", "Eintrag wurde bereits rückgängig gemacht");
    const current = await kind.load(ctx.db, e.object_id);
    if (!current || !isDeepStrictEqual(current, e.after)) {
      throw new AppError("not_undoable", "Das Objekt hat sich seit diesem Eintrag geändert");
    }
    const target = (e.before ?? kind.deleted(current)) as Record<string, unknown>;
    await kind.restore(ctx.db, target);
    const recipients = e.event_id
      ? (await ctx.db.selectFrom("event_recipient").select("recipient").where("event_id", "=", e.event_id).execute()).map((r) => r.recipient)
      : [];
    const id = await recordChange(ctx, {
      action: "history.undo", objectType: e.object_type, objectId: e.object_id, teamId: e.team_id, before: current, after: target,
      undoOf: e.id, change: `Änderung „${e.action}“ wird rückgängig gemacht`,
      event: { type: "change.reverted", recipients },
    });
    await ctx.db.updateTable("history").set({ undone: true }).where("id", "=", e.id).execute();
    if (e.undo_of) await ctx.db.updateTable("history").set({ undone: false }).where("id", "=", e.undo_of).execute();
    return { history_id: id };
  },
});
