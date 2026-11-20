import { createClient } from "./client";

const c = createClient("http://localhost:8080", () => "token");

export async function ok(): Promise<string> {
  const r = await c.call("appointment.create", {
    team_id: "11111111-1111-1111-1111-111111111111",
    title: "Vorbereitung",
    starts_at: "2026-12-01T17:00:00Z",
    ends_at: "2026-12-01T18:00:00Z",
    timezone: "Europe/Berlin",
  });
  const id: string = r.appointment_id;
  return id;
}
