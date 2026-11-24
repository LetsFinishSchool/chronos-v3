import { createClient } from "./client";

const c = createClient("http://localhost:8080", () => "token");

// Erwartet: Übersetzungsfehler (title muss string sein)
void c.call("appointment.create", {
  team_id: "11111111-1111-1111-1111-111111111111",
  title: 42,
  starts_at: "2026-12-01T17:00:00Z",
  ends_at: "2026-12-01T18:00:00Z",
  timezone: "Europe/Berlin",
});
