#!/usr/bin/env python3
"""Erzeugt rrule_cases.json (Erwartungswerte für K2) mit python-dateutil als Referenz.

Nur einmalig und mit Sichtprüfung ausführen; die erzeugte Datei wird eingecheckt.
    python3 -m venv /tmp/v && /tmp/v/bin/pip install python-dateutil
    /tmp/v/bin/python generate_rrule_golden.py > rrule_cases.json

Semantik: Der Beginn gilt als Ortszeit (Wanduhr) in `timezone`. Vorkommen behalten die Ortszeit über
Sommerzeitwechsel hinweg, ausgegeben wird UTC. Nicht existente Ortszeiten (Lücke beim Umstellen) und
untertägige Frequenzen sind bewusst nicht im Katalog (uneinheitliche Semantik).
"""
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from dateutil import rrule as rr

BERLIN = "Europe/Berlin"
WIDE = ("2026-01-01T00:00:00Z", "2041-01-01T00:00:00Z")

CASES = [
    # id, rrule, dtstart (Ortszeit), von/bis (UTC), exdates (Ortszeit), Beschreibung
    ("wk-mo-spring-dst", "FREQ=WEEKLY;BYDAY=MO;COUNT=8", "2026-03-02T18:00:00", WIDE, [], "Wochentermin über Umstellung auf Sommerzeit (29.03.2026)"),
    ("wk-tu-autumn-dst", "FREQ=WEEKLY;BYDAY=TU;COUNT=8", "2026-10-06T18:00:00", WIDE, [], "Wochentermin über Umstellung auf Winterzeit (25.10.2026)"),
    ("daily-interval2", "FREQ=DAILY;INTERVAL=2;COUNT=10", "2026-03-20T12:00:00", WIDE, [], "Alle zwei Tage, über Sommerzeit"),
    ("wk-mo-we-fr", "FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=12", "2026-06-01T09:30:00", WIDE, [], "Mehrere Wochentage"),
    ("wk-interval2-th", "FREQ=WEEKLY;INTERVAL=2;BYDAY=TH;COUNT=6", "2026-09-03T19:00:00", WIDE, [], "Alle zwei Wochen donnerstags"),
    ("mo-last-day", "FREQ=MONTHLY;BYMONTHDAY=-1;COUNT=6", "2026-01-31T18:00:00", WIDE, [], "Letzter Tag des Monats"),
    ("mo-day31-skips", "FREQ=MONTHLY;BYMONTHDAY=31;COUNT=6", "2026-01-31T18:00:00", WIDE, [], "31. fällt in Monaten ohne 31. aus"),
    ("mo-first-monday", "FREQ=MONTHLY;BYDAY=MO;BYSETPOS=1;COUNT=6", "2026-01-05T18:00:00", WIDE, [], "Erster Montag (BYSETPOS=1)"),
    ("mo-last-friday", "FREQ=MONTHLY;BYDAY=FR;BYSETPOS=-1;COUNT=6", "2026-01-30T18:00:00", WIDE, [], "Letzter Freitag (BYSETPOS=-1)"),
    ("mo-second-tuesday", "FREQ=MONTHLY;BYDAY=2TU;COUNT=6", "2026-01-13T18:00:00", WIDE, [], "Zweiter Dienstag (Ordinalzahl)"),
    ("yr-feb29", "FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=29;COUNT=3", "2028-02-29T18:00:00", WIDE, [], "29. Februar nur in Schaltjahren"),
    ("until-inclusive", "FREQ=DAILY;UNTIL=20260310T170000Z", "2026-03-05T18:00:00", WIDE, [], "UNTIL in UTC, Endzeitpunkt eingeschlossen (18:00 MEZ = 17:00Z)"),
    ("count-1", "FREQ=WEEKLY;COUNT=1", "2026-05-04T18:00:00", WIDE, [], "Genau ein Vorkommen"),
    ("wkst-mo", "FREQ=WEEKLY;INTERVAL=2;COUNT=4;BYDAY=TU,SU;WKST=MO", "2026-08-04T18:00:00", WIDE, [], "Wochenbeginn Montag (RFC-5545-Beispiel)"),
    ("wkst-su", "FREQ=WEEKLY;INTERVAL=2;COUNT=4;BYDAY=TU,SU;WKST=SU", "2026-08-04T18:00:00", WIDE, [], "Wochenbeginn Sonntag: andere Folge als wkst-mo"),
    ("mo-last-weekday", "FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1;COUNT=6", "2026-01-30T18:00:00", WIDE, [], "Letzter Werktag des Monats"),
    ("exdate-weekly", "FREQ=WEEKLY;BYDAY=WE;COUNT=6", "2026-09-02T18:00:00", WIDE, ["2026-09-16T18:00:00"], "Ausgenommenes Vorkommen (EXDATE, Ortszeit)"),
    ("yr-yearday", "FREQ=YEARLY;BYYEARDAY=1,100,200;COUNT=6", "2026-01-01T10:00:00", WIDE, [], "Jahrestage"),
    ("yr-weekno", "FREQ=YEARLY;BYWEEKNO=20;BYDAY=MO;COUNT=3", "2026-05-11T18:00:00", WIDE, [], "Kalenderwoche 20, Montag"),
    ("window-infinite-weekly", "FREQ=WEEKLY;BYDAY=MO", "2026-03-02T18:00:00", ("2026-03-23T00:00:00Z", "2026-04-20T00:00:00Z"), [], "Unbegrenzt, Zeitfenster über Sommerzeitwechsel (von eingeschlossen, bis ausgeschlossen)"),
    ("window-infinite-monthly", "FREQ=MONTHLY;BYMONTHDAY=15", "2026-01-15T18:00:00", ("2026-11-01T00:00:00Z", "2027-03-01T00:00:00Z"), [], "Unbegrenzt, Fenster über Jahreswechsel"),
]

INVALID = [
    ("invalid-freq", "FREQ=FOO"),
    ("invalid-byday", "FREQ=WEEKLY;BYDAY=XX"),
    ("invalid-count-and-until", "FREQ=WEEKLY;COUNT=3;UNTIL=20270101T000000Z"),
    ("invalid-bymonthday-0", "FREQ=MONTHLY;BYMONTHDAY=0"),
    ("invalid-interval-0", "FREQ=DAILY;INTERVAL=0"),
    ("invalid-missing-freq", "INTERVAL=2;COUNT=3"),
]

def parse_utc(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def fmt(d):
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def expand(rule, dtstart_local, tzname, frm, to, exdates):
    tz = ZoneInfo(tzname)
    start = datetime.fromisoformat(dtstart_local).replace(tzinfo=tz)
    r = rr.rrulestr(rule, dtstart=start)
    ex = {datetime.fromisoformat(e).replace(tzinfo=tz) for e in exdates}
    out = []
    for occ in r:
        occ_utc = occ.astimezone(timezone.utc)
        if occ_utc >= to:
            break
        if occ in ex or occ_utc < frm:
            continue
        out.append(occ_utc)
        if len(out) >= 1000:
            break
    return out

def main():
    cases = []
    for cid, rule, start, (frm, to), ex, desc in CASES:
        occ = expand(rule, start, BERLIN, parse_utc(frm), parse_utc(to), ex)
        assert occ, cid
        cases.append({"id": cid, "description": desc, "rrule": rule, "dtstart": start, "timezone": BERLIN,
                      "duration_minutes": 60, "exdates": ex, "from": frm, "to": to,
                      "expected_starts_at": [fmt(o) for o in occ]})
    print(json.dumps({"generated_with": "python-dateutil, Europe/Berlin, Wanduhrsemantik",
                      "valid": cases,
                      "invalid": [{"id": i, "rrule": r} for i, r in INVALID]}, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
