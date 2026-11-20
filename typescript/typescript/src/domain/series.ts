import type { Kysely } from "kysely";
import { z } from "zod";
import type { Database } from "../core/db.js";
import { localTime, timezone, uuid } from "./schemas.js";

export const seriesSchema = z.object({
  id: uuid, team_id: uuid, title: z.string(), rrule: z.string(), dtstart: localTime, timezone,
  duration_minutes: z.number().int(), exdates: z.array(localTime), status: z.enum(["aktiv", "gelöscht"]),
});
export type SeriesImage = z.infer<typeof seriesSchema>;

export async function loadSeries(db: Kysely<Database>, id: string): Promise<SeriesImage | undefined> {
  const r = await db.selectFrom("series").selectAll().where("id", "=", id).executeTakeFirst();
  return r && { id: r.id, team_id: r.team_id, title: r.title, rrule: r.rrule, dtstart: r.dtstart, timezone: r.timezone,
    duration_minutes: r.duration_minutes, exdates: r.exdates, status: r.status as SeriesImage["status"] };
}
