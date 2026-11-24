#!/usr/bin/env python3
"""Führt die Abnahmesuite aus und schreibt einen Bericht (JSON + Tabelle).

    python3 run_acceptance.py [--phase 1|2] [--only K2,K5] [--json bericht.json] [--list]

Phase 1: S-1..S-10 (ohne N-1). Phase 2: nur N-1.
Kennzeichnung der Tests im Namen: test_<Tag>_...  Tags: S1 S2 S3 K2 K4 K5 K6 M14 M15 S10 N1.
Nicht Teil dieser Suite: K1 (Budget, V-3), K3 (Web Push, manuell, siehe manual/K3-webpush.md), K7 (Image/Start, V-4).
"""
import argparse
import json
import os
import re
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spikelib  # noqa: E402

PHASE2 = {"N1"}
ORDER = ["S1", "S2", "S3", "K4", "K2", "K6", "M14", "M15", "S10", "K5", "N1"]  # K5 zuletzt (beendet den Worker)


def tag_of(test_id):
    m = re.search(r"\.test_([A-Za-z]+\d+)_", test_id) or re.search(r"\.([A-Z]+\d+)[A-Z]", test_id)
    return m.group(1) if m else "?"


class Result(unittest.TextTestResult):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.records = []
        self._t0 = {}

    def startTest(self, test):
        self._t0[test.id()] = time.time()
        super().startTest(test)

    def _rec(self, test, status, msg=""):
        self.records.append({"id": test.id(), "tag": tag_of(test.id()), "status": status, "msg": msg.strip()[-1500:],
                             "seconds": round(time.time() - self._t0.get(test.id(), time.time()), 2)})

    def addSuccess(self, test):
        super().addSuccess(test); self._rec(test, "pass")

    def addFailure(self, test, err):
        super().addFailure(test, err); self._rec(test, "fail", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err); self._rec(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason); self._rec(test, "skip", reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._rec(subtest, "fail", self._exc_info_to_string(err, test))


def collect(only, phase):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    here = os.path.dirname(os.path.abspath(__file__))
    tests = []
    for mod in sorted(f[:-3] for f in os.listdir(here) if re.match(r"test_.*\.py$", f)):
        for t in _flatten(loader.loadTestsFromName(mod)):
            tg = tag_of(t.id())
            if only and tg not in only:
                continue
            if (phase == 2) != (tg in PHASE2):
                continue
            tests.append((ORDER.index(tg) if tg in ORDER else 99, t.id(), t))
    for _, _, t in sorted(tests, key=lambda x: (x[0], x[1])):
        suite.addTest(t)
    return suite


def _flatten(s):
    for x in s:
        if isinstance(x, unittest.TestSuite):
            yield from _flatten(x)
        else:
            yield x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, default=1, choices=(1, 2))
    ap.add_argument("--only", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    suite = collect(only, args.phase)
    if args.list:
        for t in suite:
            print(t.id())
        return 0
    res = unittest.TextTestRunner(resultclass=Result, verbosity=1, stream=sys.stderr).run(suite)
    by = {}
    for r in res.records:
        by.setdefault(r["tag"], []).append(r)
    print("\n== Bericht ==")
    print(f"{'Tag':6} {'bestanden':>9} {'gesamt':>7}   Kriterium")
    names = {"S1": "Operationsbeschreibung (M-11/S-1)", "S2": "Team-Baum", "S3": "Transaktion, Verlauf, Rückgängig",
             "K2": "K2 RRULE", "K4": "K4 OIDC/Keycloak", "K5": "K5 Worker-Absturz", "K6": "K6 KI-Anbindung",
             "M14": "M-14 Worker-Robustheit", "M15": "M-15 Korrelations-ID", "S10": "S-10 Frontend-Brücke (Q-5)",
             "N1": "N-1 neue Operation (M-11)"}
    for tg in sorted(by, key=lambda x: ORDER.index(x) if x in ORDER else 99):
        rs = by[tg]
        p = sum(1 for r in rs if r["status"] == "pass")
        sk = sum(1 for r in rs if r["status"] == "skip")
        print(f"{tg:6} {p:>9} {len(rs) - sk:>7}   {names.get(tg, '')}" + (f"  ({sk} übersprungen)" if sk else ""))
    m14 = by.get("M14", [])
    if m14:
        done = [r for r in m14 if r["status"] != "skip"]
        print(f"\nM-14: {sum(r['status']=='pass' for r in done)}/{len(done)} Fälle bestanden "
              "(zusätzlich K5 und Duplikatzahl in den Hinweisen)")
    if spikelib.NOTES:
        print("Hinweise:", json.dumps(spikelib.NOTES, ensure_ascii=False))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"records": res.records, "notes": spikelib.NOTES}, f, indent=1, ensure_ascii=False)
    return 0 if res.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
