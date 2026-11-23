import { createClient } from "./client";

const c = createClient("http://localhost:8080", () => "token");

// Erwartet: Übersetzungsfehler (Operation existiert nicht)
void c.call("appointment.does_not_exist", {});
