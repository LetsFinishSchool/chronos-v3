import { randomUUID } from "node:crypto";
import { z } from "zod";
import { defineOperation } from "../../core/operation.js";
import { AppError } from "../../core/errors.js";
import { requireMember } from "../access.js";
import { recordChange } from "../changes.js";
import { expand, InvalidRRule, parseRule } from "../rrule.js";
import { loadSeries } from "../series.js";
import { fmtUtc, localTime, timezone, utcTime, uuid } from "../schemas.js";

defineOperation({
  name: "series.create",
  description: "Legt eine Terminserie nach iCalendar-RRULE (ohne Präfix RRULE:) in Ortszeit mit Zeitzone an. Sommerzeitwechsel erhalten die Ortszeit.",
  mutating: true,
  params: z.strictObject({
    team_id: uuid, title: z.string().min(1).max(200), rrule: z.string().min(1), dtstart: localTime, timezone,
    duration_minutes: z.number().int().min(1).max(1440), exdates: z.array(localTime).optional(),
  }),
  result: z.object({ series_id: uuid }),
  async run(ctx, p) {
    await requireMember(ctx, p.team_id);
    try {
      parseRule(p.rrule, p.dtstart, p.timezone);
    } catch (e) {
      if (e instanceof InvalidRRule) throw new AppError("invalid_rrule", e.message);
      throw e;
    }
    const id = randomUUID();
    const exdates = p.exdates ?? [];
    await ctx.db.insertInto("series").values({
      id, team_id: p.team_id, title: p.title, rrule: p.rrule, dtstart: p.dtstart, timezone: p.timezone, duration_minutes: p.duration_minutes, exdates, status: "aktiv",
    }).execute();
    await recordChange(ctx, {
      action: "series.create", objectType: "series", objectId: id, teamId: p.team_id, before: null,
      after: { id, team_id: p.team_id, title: p.title, rrule: p.rrule, dtstart: p.dtstart, timezone: p.timezone, duration_minutes: p.duration_minutes, exdates, status: "aktiv" },
      change: `Serie „${p.title}“ wird angelegt`,
    });
    return { series_id: id };
  },
});

defineOperation({
  name: "series.occurrences",
  description: "Berechnet die Vorkommen einer Serie im Fenster [from, to) (höchstens 1000, nach Beginn sortiert, Ausgabe in UTC).",
  mutating: false,
  params: z.strictObject({ series_id: uuid, from: utcTime, to: utcTime }),
  result: z.object({ occurrences: z.array(z.object({ starts_at: utcTime, ends_at: utcTime })) }),
  async run(ctx, p) {
    const s = await loadSeries(ctx.db, p.series_id);
    if (!s || s.status === "gelöscht") throw new AppError("not_found", "Serie nicht gefunden");
    await requireMember(ctx, s.team_id);
    const occ = expand(s, new Date(p.from), new Date(p.to));
    return { occurrences: occ.map((o) => ({ starts_at: fmtUtc(o.starts_at), ends_at: fmtUtc(o.ends_at) })) };
  },
});
