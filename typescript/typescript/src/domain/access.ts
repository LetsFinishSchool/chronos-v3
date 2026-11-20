import { sql, type Kysely } from "kysely";
import type { Database } from "../core/db.js";
import { AppError } from "../core/errors.js";
import type { Ctx } from "../core/operation.js";

type Db = Kysely<Database>;

/** Alle Teams mit direkter Mitgliedschaft der Person und alle übergeordneten Teams. */
export async function effectiveTeams(db: Db, personId: string) {
  const r = await sql<{ id: string; name: string; parent_id: string | null }>`
    with recursive up as (
      select t.id, t.name, t.parent_id from team t join team_member m on m.team_id = t.id where m.person_id = ${personId}
      union
      select p.id, p.name, p.parent_id from team p join up on up.parent_id = p.id)
    select id, name, parent_id from up order by name, id`.execute(db);
  return r.rows;
}

/** Direkte Mitglieder des Teams und aller Unter-Teams (beliebig tief), ohne Duplikate. */
export async function effectiveMembers(db: Db, teamId: string) {
  const r = await sql<{ person_id: string; name: string }>`
    with recursive down as (
      select id from team where id = ${teamId}
      union
      select c.id from team c join down on c.parent_id = down.id)
    select distinct p.id as person_id, p.name from team_member m join down on m.team_id = down.id join person p on p.id = m.person_id
    order by p.id`.execute(db);
  return r.rows;
}

/** Die EINE Berechtigungsprüfung: 404 bei unbekanntem Team, 403 für Nicht-Mitglieder (effektive Mitgliedschaft). */
export async function requireMember(ctx: Pick<Ctx, "db" | "caller">, teamId: string): Promise<void> {
  const exists = await ctx.db.selectFrom("team").select("id").where("id", "=", teamId).executeTakeFirst();
  if (!exists) throw new AppError("not_found", "Team nicht gefunden");
  const r = await sql<{ ok: boolean }>`
    select exists (
      with recursive down as (
        select id from team where id = ${teamId}
        union
        select c.id from team c join down on c.parent_id = down.id)
      select 1 from team_member m join down on m.team_id = down.id where m.person_id = ${ctx.caller.id}) as ok`.execute(ctx.db);
  if (!r.rows[0]?.ok) throw new AppError("forbidden", "Kein Mitglied des Teams");
}
