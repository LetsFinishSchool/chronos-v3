import rrulePkg, { type Options, type RRule as RRuleType } from "rrule";

// rrule 2.8.1 ist CommonJS: unter Node-ESM nur über den Default-Export erreichbar
const { RRule } = rrulePkg;
type RRule = RRuleType;
import { DateTime } from "luxon";

// EIGENBAU:BEGIN Wanduhrsemantik (Ortszeit ↔ UTC über luxon) und Ergänzungsprüfungen, die rrule 2.8.1 selbst nicht macht
export class InvalidRRule extends Error {}

const LOCAL_FMT = "yyyy-MM-dd'T'HH:mm:ss";

/** Ortszeit-Text → "schwebendes" Datum (Ortszeitfelder als UTC), wie rrule es erwartet. */
function floating(local: string): Date {
  return new Date(local + "Z");
}

/** Parst und prüft eine RRULE (ohne Präfix); wirft InvalidRRule. */
export function parseRule(rrule: string, dtstartLocal: string, zone: string): RRule {
  if (/^\s*(RRULE:|DTSTART|EXDATE)/i.test(rrule)) throw new InvalidRRule("Präfix oder DTSTART nicht erlaubt");
  let opts: Partial<Options>;
  try {
    opts = RRule.parseString(rrule);
  } catch (e) {
    throw new InvalidRRule(String(e instanceof Error ? e.message : e));
  }
  if (opts.freq === undefined || opts.freq === null || Number.isNaN(opts.freq)) throw new InvalidRRule("FREQ fehlt oder ist ungültig");
  if (opts.count != null && opts.until != null) throw new InvalidRRule("COUNT und UNTIL schließen sich aus");
  if (opts.interval !== undefined && !(opts.interval >= 1)) throw new InvalidRRule("INTERVAL muss ≥ 1 sein");
  if (opts.bymonthday != null && [opts.bymonthday].flat().some((d) => d === 0 || Math.abs(d) > 31)) {
    throw new InvalidRRule("BYMONTHDAY ungültig");
  }
  for (const key of ["byweekday"] as const) {
    if (opts[key] != null && [opts[key]].flat().some((d) => d == null || Number.isNaN(d as number))) throw new InvalidRRule("BYDAY ungültig");
  }
  if (/BYDAY=[^;]*[A-Z]{2}/i.test(rrule)) {
    const days = /BYDAY=([^;]*)/i.exec(rrule)?.[1]?.split(",") ?? [];
    if (days.some((d) => !/^[+-]?\d{0,2}(MO|TU|WE|TH|FR|SA|SU)$/i.test(d))) throw new InvalidRRule("BYDAY ungültig");
  }
  // UNTIL ist UTC; in Wanduhrsemantik als Ortszeit der Zone vergleichen
  if (opts.until) {
    const local = DateTime.fromJSDate(opts.until, { zone: "utc" }).setZone(zone).toFormat(LOCAL_FMT);
    opts.until = floating(local);
  }
  try {
    return new RRule({ ...opts, dtstart: floating(dtstartLocal) } as Options);
  } catch (e) {
    throw new InvalidRRule(String(e instanceof Error ? e.message : e));
  }
}

export interface Occurrence { starts_at: Date; ends_at: Date }

/** Dehnt die Serie im Fenster [from, to) aus; höchstens `limit` Vorkommen, nach Beginn sortiert. */
export function expand(
  s: { rrule: string; dtstart: string; timezone: string; duration_minutes: number; exdates: string[] },
  from: Date,
  to: Date,
  limit = 1000,
): Occurrence[] {
  const rule = parseRule(s.rrule, s.dtstart, s.timezone);
  const ex = new Set(s.exdates);
  const out: Occurrence[] = [];
  const upper = to.getTime() + 36 * 3600_000; // Ortszeit weicht höchstens um Stunden von UTC ab
  rule.all((d) => {
    if (d.getTime() > upper || out.length >= limit) return false;
    const local = d.toISOString().slice(0, 19);
    if (ex.has(local)) return true;
    const start = DateTime.fromISO(local, { zone: s.timezone }).toUTC();
    const t = start.toMillis();
    if (t >= from.getTime() && t < to.getTime()) {
      out.push({ starts_at: start.toJSDate(), ends_at: start.plus({ minutes: s.duration_minutes }).toJSDate() });
    }
    return true;
  });
  out.sort((a, b) => a.starts_at.getTime() - b.starts_at.getTime());
  return out.slice(0, limit);
}
// EIGENBAU:END
