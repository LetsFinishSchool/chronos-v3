import { randomUUID } from "node:crypto";
import { z } from "zod";
import { defineOperation, type Ctx } from "../../core/operation.js";
import { AppError } from "../../core/errors.js";
import { requireMember } from "../access.js";
import { recordChange, teamRecipients } from "../changes.js";
import { timezone, utcTime, uuid } from "../schemas.js";
import { appointmentImage, appointmentSchema, loadAppointment } from "../appointments.js";

const times = (p: { starts_at: string; ends_at: string }) => new Date(p.ends_at) > new Date(p.starts_at);

defineOperation({
  name: "appointment.create",
  description: "Legt einen Termin im Team an (Status geplant). Die übrigen Teammitglieder werden benachrichtigt.",
  mutating: true,
  params: z.strictObject({
    team_id: uuid, title: z.string().min(1).max(200), starts_at: utcTime, ends_at: utcTime, timezone,
  }).refine(times, { message: "ends_at muss nach starts_at liegen", path: ["ends_at"] }),
  result: z.object({ appointment_id: uuid }),
  async run(ctx, p) {
    await requireMember(ctx, p.team_id);
    const id = randomUUID();
    await ctx.db.insertInto("appointment").values({
      id, team_id: p.team_id, title: p.title, starts_at: p.starts_at, ends_at: p.ends_at, timezone: p.timezone, status: "geplant",
    }).execute();
    const after = { id, team_id: p.team_id, title: p.title, starts_at: p.starts_at, ends_at: p.ends_at, timezone: p.timezone, status: "geplant" };
    await recordChange(ctx, {
      action: "appointment.create", objectType: "appointment", objectId: id, teamId: p.team_id, before: null, after,
      change: `Termin „${p.title}“ wird angelegt`,
      event: { type: "appointment.created", recipients: await teamRecipients(ctx, p.team_id) },
    });
    return { appointment_id: id };
  },
});

async function visible(ctx: Ctx, id: string) {
  const a = await loadAppointment(ctx.db, id);
  if (!a || a.status === "gelöscht") throw new AppError("not_found", "Termin nicht gefunden");
  await requireMember(ctx, a.team_id);
  return a;
}

defineOperation({
  name: "appointment.get",
  description: "Liefert einen Termin (nicht gelöschte).",
  mutating: false,
  params: z.strictObject({ appointment_id: uuid }),
  result: z.object({ appointment: appointmentSchema }),
  async run(ctx, p) {
    return { appointment: await visible(ctx, p.appointment_id) };
  },
});

defineOperation({
  name: "appointment.list",
  description: "Listet die Termine eines Teams (inklusive abgesagter, ohne gelöschte) nach Beginn sortiert.",
  mutating: false,
  params: z.strictObject({ team_id: uuid }),
  result: z.object({ appointments: z.array(appointmentSchema) }),
  async run(ctx, p) {
    await requireMember(ctx, p.team_id);
    const rows = await ctx.db.selectFrom("appointment").selectAll().where("team_id", "=", p.team_id).where("status", "<>", "gelöscht")
      .orderBy("starts_at").orderBy("id").execute();
    return { appointments: rows.map(appointmentImage) };
  },
});

defineOperation({
  name: "appointment.cancel",
  description: "Sagt einen geplanten Termin ab (geplant → abgesagt). Die übrigen Teammitglieder werden benachrichtigt.",
  mutating: true,
  params: z.strictObject({ appointment_id: uuid }),
  result: z.object({}),
  async run(ctx, p) {
    const before = await visible(ctx, p.appointment_id);
    if (before.status !== "geplant") throw new AppError("conflict", `Termin ist bereits ${before.status}`);
    await ctx.db.updateTable("appointment").set({ status: "abgesagt" }).where("id", "=", before.id).execute();
    await recordChange(ctx, {
      action: "appointment.cancel", objectType: "appointment", objectId: before.id, teamId: before.team_id,
      before, after: { ...before, status: "abgesagt" }, change: `Termin „${before.title}“ wird abgesagt`,
      event: { type: "appointment.cancelled", recipients: await teamRecipients(ctx, before.team_id) },
    });
    return {};
  },
});
