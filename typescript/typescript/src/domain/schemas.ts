import { z } from "zod";
import { DateTime } from "luxon";

const UTC_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
const LOCAL_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/;

export const uuid = z.guid().describe("UUID");
export const utcTime = z.string().regex(UTC_RE, "UTC-Zeitpunkt wie 2026-12-01T17:00:00Z erwartet")
  .refine((s) => DateTime.fromISO(s, { zone: "utc" }).isValid, "ungültiger Zeitpunkt").describe("UTC, ISO 8601 mit Z");
export const localTime = z.string().regex(LOCAL_RE, "Ortszeit wie 2026-03-02T18:00:00 erwartet")
  .refine((s) => DateTime.fromISO(s).isValid, "ungültige Ortszeit").describe("Ortszeit ohne Zone");
export const timezone = z.string().min(1).refine((s) => DateTime.local().setZone(s).isValid, "unbekannte IANA-Zeitzone").describe("IANA-Zeitzone");

export const fmtUtc = (d: Date): string => d.toISOString().replace(/\.\d{3}Z$/, "Z");
