import { randomUUID } from "node:crypto";
import { z } from "zod";
import { defineOperation } from "../../core/operation.js";
import { AppError } from "../../core/errors.js";
import { effectiveMembers, effectiveTeams, requireMember } from "../access.js";
import { uuid } from "../schemas.js";

defineOperation({
  name: "team.create",
  description: "Legt ein Team an; der Aufrufer wird direktes Mitglied. Mit parent_id entsteht ein Unter-Team (Aufrufer muss Mitglied des Eltern-Teams sein).",
  mutating: true,
  params: z.strictObject({ name: z.string().min(1).max(100), parent_id: uuid.optional() }),
  result: z.object({ team_id: uuid }),
  async run(ctx, p) {
    if (p.parent_id) await requireMember(ctx, p.parent_id);
    const id = randomUUID();
    await ctx.db.insertInto("team").values({ id, name: p.name, parent_id: p.parent_id ?? null }).execute();
    await ctx.db.insertInto("team_member").values({ team_id: id, person_id: ctx.caller.id }).execute();
    ctx.affected.push({ type: "team", id, change: `Team „${p.name}“ wird angelegt` });
    return { team_id: id };
  },
});

defineOperation({
  name: "team.add_member",
  description: "Fügt eine bereits angemeldete Person (Keycloak-sub) als direktes Mitglied zu einem Team hinzu. Doppeltes Hinzufügen ist ohne Wirkung.",
  mutating: true,
  params: z.strictObject({ team_id: uuid, person_id: z.string().min(1) }),
  result: z.object({}),
  async run(ctx, p) {
    await requireMember(ctx, p.team_id);
    const person = await ctx.db.selectFrom("person").select("id").where("id", "=", p.person_id).executeTakeFirst();
    if (!person) throw new AppError("not_found", "Person unbekannt");
    const r = await ctx.db.insertInto("team_member").values({ team_id: p.team_id, person_id: p.person_id }).onConflict((oc) => oc.doNothing()).executeTakeFirst();
    if (Number(r.numInsertedOrUpdatedRows ?? 0) > 0) ctx.affected.push({ type: "team", id: p.team_id, change: `Mitglied ${p.person_id} wird hinzugefügt` });
    return {};
  },
});

defineOperation({
  name: "team.effective_members",
  description: "Liefert die direkten Mitglieder eines Teams und aller Unter-Teams (beliebig tief), ohne Duplikate, nach person_id sortiert.",
  mutating: false,
  params: z.strictObject({ team_id: uuid }),
  result: z.object({ members: z.array(z.object({ person_id: z.string(), name: z.string() })) }),
  async run(ctx, p) {
    await requireMember(ctx, p.team_id);
    return { members: await effectiveMembers(ctx.db, p.team_id) };
  },
});

defineOperation({
  name: "team.effective_teams",
  description: "Liefert alle Teams mit direkter Mitgliedschaft der Person und alle übergeordneten Teams (Standard: der Aufrufer).",
  mutating: false,
  params: z.strictObject({ person_id: z.string().optional() }),
  result: z.object({ teams: z.array(z.object({ team_id: uuid, name: z.string(), parent_id: uuid.nullable() })) }),
  async run(ctx, p) {
    if (p.person_id && p.person_id !== ctx.caller.id) throw new AppError("forbidden", "Nur die eigenen Teams abrufbar");
    const teams = await effectiveTeams(ctx.db, ctx.caller.id);
    return { teams: teams.map((t) => ({ team_id: t.id, name: t.name, parent_id: t.parent_id })) };
  },
});
