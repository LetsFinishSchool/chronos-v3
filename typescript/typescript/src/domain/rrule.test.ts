import { readFileSync } from "node:fs";
import { expect, test } from "vitest";
import { expand, parseRule } from "./rrule.js";

const golden = JSON.parse(readFileSync(new URL("../../../common/acceptance/golden/rrule_cases.json", import.meta.url), "utf8"));

for (const c of golden.valid) {
  test(`rrule ${c.id}`, () => {
    const occ = expand({ rrule: c.rrule, dtstart: c.dtstart, timezone: c.timezone, duration_minutes: c.duration_minutes, exdates: c.exdates }, new Date(c.from), new Date(c.to));
    expect(occ.map((o) => o.starts_at.toISOString().replace(".000Z", "Z"))).toEqual(c.expected_starts_at);
  });
}
for (const c of golden.invalid) {
  test(`rrule ungültig ${c.id}`, () => {
    expect(() => parseRule(c.rrule, "2026-03-02T18:00:00", "Europe/Berlin")).toThrow();
  });
}
