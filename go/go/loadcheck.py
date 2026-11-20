#!/usr/bin/env python3
"""S-8 Selbstkontrolle: kurzer Lastlauf (nur Standardbibliothek). Aufruf mit gesetzten BASE_URL/KEYCLOAK_URL (stack.sh env)."""
import json, os, sys, threading, time, urllib.request, urllib.parse, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common", "acceptance"))
from spikelib import alice, make_team, make_appointment, register_all  # noqa: E402

register_all()
a = alice()
team = make_team(a)
lat, errs = [], []
end = time.time() + float(os.environ.get("SECONDS", "30"))

def worker():
    while time.time() < end:
        t0 = time.time()
        r = make_appointment(a, team) if len(lat) % 2 else a.op("team.effective_teams")
        lat.append(time.time() - t0)
        if r.status != 200:
            errs.append(r.status)

ts = [threading.Thread(target=worker) for _ in range(int(os.environ.get("THREADS", "16")))]
[t.start() for t in ts]; [t.join() for t in ts]
lat.sort()
print(f"{len(lat)} Anfragen, {len(lat)/float(os.environ.get('SECONDS','30')):.0f}/s, Fehler: {len(errs)}, p50 {lat[len(lat)//2]*1000:.0f} ms, p95 {lat[int(len(lat)*.95)]*1000:.0f} ms, max {lat[-1]*1000:.0f} ms")
