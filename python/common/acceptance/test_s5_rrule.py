"""S-5 / K2: RRULE-Katalog (Erwartungswerte aus golden/rrule_cases.json)."""
import json
import os
import unittest
from datetime import timedelta

from spikelib import *

GOLDEN = json.load(open(os.path.join(HERE, "golden", "rrule_cases.json"), encoding="utf-8"))


class K2Rrule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_all()
        cls.a = alice()
        cls.team = make_team(cls.a)

    def series(self, rrule, dtstart="2026-03-02T18:00:00", tz="Europe/Berlin", exdates=None, duration=60):
        p = {"team_id": self.team, "title": uid("serie-"), "rrule": rrule, "dtstart": dtstart, "timezone": tz,
             "duration_minutes": duration}
        if exdates:
            p["exdates"] = exdates
        return self.a.ok("series.create", p)["series_id"]

    def test_K2_zz_limit_1000_and_sorted(self):
        sid = self.series("FREQ=DAILY", dtstart="2026-01-01T08:00:00")
        occ = self.a.ok("series.occurrences", {"series_id": sid, "from": "2026-01-01T00:00:00Z",
                                                "to": "2031-01-01T00:00:00Z"})["occurrences"]
        self.assertEqual(len(occ), 1000)
        self.assertEqual(occ[0]["starts_at"], "2026-01-01T07:00:00Z")
        starts = [o["starts_at"] for o in occ]
        self.assertEqual(starts, sorted(starts))

    def test_K2_zz_requires_membership(self):
        sid = self.series("FREQ=WEEKLY;COUNT=2")
        carol().err("series.occurrences", {"series_id": sid, "from": "2026-01-01T00:00:00Z",
                                           "to": "2027-01-01T00:00:00Z"}, 403, "forbidden")


def _valid(case):
    def t(self):
        sid = self.series(case["rrule"], case["dtstart"], case["timezone"], case["exdates"], case["duration_minutes"])
        occ = self.a.ok("series.occurrences", {"series_id": sid, "from": case["from"], "to": case["to"]})["occurrences"]
        self.assertEqual([o["starts_at"] for o in occ], case["expected_starts_at"], case["description"])
        for o in occ:
            self.assertEqual(parse_utc(o["ends_at"]) - parse_utc(o["starts_at"]), timedelta(minutes=case["duration_minutes"]))
    return t


def _invalid(case):
    def t(self):
        self.a.err("series.create", {"team_id": self.team, "title": "x", "rrule": case["rrule"],
                                     "dtstart": "2026-03-02T18:00:00", "timezone": "Europe/Berlin",
                                     "duration_minutes": 60}, 422, "invalid_rrule")
    return t


for _c in GOLDEN["valid"]:
    setattr(K2Rrule, f"test_K2_valid_{_c['id']}", _valid(_c))
for _c in GOLDEN["invalid"]:
    setattr(K2Rrule, f"test_K2_{_c['id'].replace('-', '_')}", _invalid(_c))

if __name__ == "__main__":
    unittest.main()
