import { createClient } from "./client";

const c = createClient("http://localhost:8080", () => "token");

// Erwartet: Übersetzungsfehler (Pflichtparameter ends_at und timezone fehlen)
void c.call("appointment.create", {
  team_id: "11111111-1111-1111-1111-111111111111",
  title: "Vorbereitung",
  starts_at: "2026-12-01T17:00:00Z",
});
