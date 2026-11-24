import type { Kysely, Selectable } from "kysely";
import { z } from "zod";
import type { Database } from "../core/db.js";
import { fmtUtc, timezone, utcTime, uuid } from "./schemas.js";

export const appointmentSchema = z.object({
  id: uuid, team_id: uuid, title: z.string(), starts_at: utcTime, ends_at: utcTime, timezone,
  status: z.enum(["geplant", "abgesagt", "gelöscht"]),
});
export type AppointmentImage = z.infer<typeof appointmentSchema>;

export function appointmentImage(r: Selectable<Database["appointment"]>): AppointmentImage {
  return {
    id: r.id, team_id: r.team_id, title: r.title, starts_at: fmtUtc(new Date(r.starts_at)), ends_at: fmtUtc(new Date(r.ends_at)),
    timezone: r.timezone, status: r.status as AppointmentImage["status"],
  };
}

export async function loadAppointment(db: Kysely<Database>, id: string): Promise<AppointmentImage | undefined> {
  const r = await db.selectFrom("appointment").selectAll().where("id", "=", id).executeTakeFirst();
  return r && appointmentImage(r);
}
