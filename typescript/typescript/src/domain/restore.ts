import type { Kysely } from "kysely";
import type { Database } from "../core/db.js";
import { appointmentSchema, loadAppointment } from "./appointments.js";
import { loadSeries, seriesSchema } from "./series.js";
import type { z } from "zod";

/** Wiederherstellbare Objektarten für „Rückgängig“: Zustandsabbild laden und zurückschreiben. */
interface Restorable {
  load(db: Kysely<Database>, id: string): Promise<Record<string, unknown> | undefined>;
  restore(db: Kysely<Database>, image: Record<string, unknown>): Promise<void>;
  /** Bild mit Status „gelöscht“ (Rückgängig einer Anlage). */
  deleted(image: Record<string, unknown>): Record<string, unknown>;
}

const appt = (i: Record<string, unknown>) => i as z.infer<typeof appointmentSchema>;
const ser = (i: Record<string, unknown>) => i as z.infer<typeof seriesSchema>;

export const restorable: Record<string, Restorable> = {
  appointment: {
    load: (db, id) => loadAppointment(db, id),
    async restore(db, image) {
      const a = appt(image);
      await db.updateTable("appointment").set({ title: a.title, starts_at: a.starts_at, ends_at: a.ends_at, timezone: a.timezone, status: a.status }).where("id", "=", a.id).execute();
    },
    deleted: (i) => ({ ...i, status: "gelöscht" }),
  },
  series: {
    load: (db, id) => loadSeries(db, id),
    async restore(db, image) {
      const s = ser(image);
      await db.updateTable("series").set({ title: s.title, rrule: s.rrule, dtstart: s.dtstart, timezone: s.timezone, duration_minutes: s.duration_minutes, exdates: s.exdates, status: s.status }).where("id", "=", s.id).execute();
    },
    deleted: (i) => ({ ...i, status: "gelöscht" }),
  },
};
