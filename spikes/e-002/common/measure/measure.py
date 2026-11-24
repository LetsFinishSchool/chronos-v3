#!/usr/bin/env python3
"""V-3: Messung der automatisch messbaren Metriken (M-1..M-6, M-13) und der K1-Prüfung gegen die laufende Umgebung.

    eval "$(../env/stack.sh env <name> <offset>)"
    python3 measure.py --image chronos-spike-<name> [--runs 3] [--duration 600] [--idle 300] [--connections 50]
                       [--rps 20] [--burst 1000] [--out ../../reports/<name>]

Nicht enthalten (manuell/anderes Werkzeug, siehe README): M-7, M-8, M-9, M-10, M-11, M-12, M-15, Q-1..Q-5.
"""
import argparse
import http.client
import json
import os
import queue
import statistics
import subprocess
import sys
import threading
import time
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "acceptance"))
import spikelib as sl  # noqa: E402

UNITS = {"B": 1, "KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3, "kB": 1000, "MB": 1000 ** 2, "GB": 1000 ** 3}


def mib(txt):
    n, u = txt.split()[0], ""
    for unit in sorted(UNITS, key=len, reverse=True):
        if n.endswith(unit):
            u = unit
            n = n[: -len(unit)]
            break
    return float(n) * UNITS[u or "B"] / 1024 ** 2


def stats(project):
    """Speicher (MiB, working set laut docker stats) und CPU (mCPU) von web und worker."""
    out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{json .}}", f"{project}-web-1", f"{project}-worker-1"],
                         capture_output=True, text=True).stdout
    res = {}
    for line in out.splitlines():
        j = json.loads(line)
        svc = "web" if "-web-" in j["Name"] else "worker"
        res[svc] = {"mem": mib(j["MemUsage"].split("/")[0]), "cpu": float(j["CPUPerc"].strip("%")) * 10}  # 100 % = 1 Kern = 1000 mCPU
    return res


def pg_connections(container, port):
    out = subprocess.run(["docker", "exec", container, "psql", "-p", str(port), "-U", "chronos", "-d", "chronos", "-tAc",
                          "select count(*) from pg_stat_activity where datname='chronos'"], capture_output=True, text=True).stdout
    try:
        return int(out.strip())
    except ValueError:
        return 0


class Sampler(threading.Thread):
    def __init__(self, project, pg, port):
        super().__init__(daemon=True)
        self.project, self.pg, self.port, self.stop, self.samples = project, pg, port, threading.Event(), []

    def run(self):
        while not self.stop.is_set():
            t = time.time()
            try:
                s = stats(self.project)
                s["pg"] = pg_connections(self.pg, self.port)
                s["t"] = t
                self.samples.append(s)
            except Exception:
                pass
            self.stop.wait(max(0, 2 - (time.time() - t)))


def percentile(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))]


def summed(samples, key):
    return [sum(s[svc][key] for svc in ("web", "worker") if svc in s) for s in samples if "web" in s and "worker" in s]


# ------------------------------------------------------------------ Last
class Conn:
    """Eine dauerhafte HTTP-Verbindung je Lastfaden."""
    def __init__(self, user):
        u = urllib.parse.urlparse(sl.BASE_URL)
        self.c = http.client.HTTPConnection(u.hostname, u.port, timeout=30)
        self.user = user

    def op(self, name, params):
        body = json.dumps({"params": params})
        for attempt in (1, 2):
            try:
                self.c.request("POST", f"/api/v1/operations/{name}", body=body,
                               headers={"Content-Type": "application/json", "Authorization": f"Bearer {sl.token(self.user)}"})
                r = self.c.getresponse()
                data = r.read()
                return r.status, data
            except (http.client.HTTPException, OSError):
                self.c.close()
                u = urllib.parse.urlparse(sl.BASE_URL)
                self.c = http.client.HTTPConnection(u.hostname, u.port, timeout=30)
        return 0, b""


def setup_data():
    sl.register_all()
    a, b, c = sl.alice(), sl.bob(), sl.carol()
    for p in (b, c):
        p.ok("notification.set_channels", {"channels": ["mock"]})
    root = sl.make_team(a, "Last-Wurzel-" + sl.uid())
    subs = [sl.make_team(a, f"Last-Unter-{i}", root) for i in range(3)]
    for t in [root] + subs:
        for p in (b, c):
            a.ok("team.add_member", {"team_id": t, "person_id": p.sub})
    appts = []
    for i in range(60):
        r = sl.make_appointment(a, subs[i % 3], days=100 + i)
        appts.append(r.json["result"]["appointment_id"])
    time.sleep(3)
    return root, subs, appts


def run_load(args, root, subs, appts):
    lat = {"read": [], "write": []}
    errors = [0]
    writes = [0]
    lock = threading.Lock()
    tokens = queue.Queue(maxsize=args.rps * 5)
    stop = threading.Event()

    def feeder():
        i = 0
        t0 = time.time()
        while not stop.is_set():
            tokens.put(i)
            i += 1
            delay = t0 + i / args.rps - time.time()
            if delay > 0:
                time.sleep(delay)

    def worker(n):
        conn = Conn("alice")
        k = 0
        while not stop.is_set():
            try:
                tokens.get(timeout=0.5)
            except queue.Empty:
                continue
            k += 1
            if k % 10 == 0:
                s = sl.future(300 + (k % 90))
                p = {"team_id": subs[k % 3], "title": f"L-{n}-{k}", "starts_at": sl.iso(s), "ends_at": sl.iso(s.replace(hour=(s.hour + 1) % 24)), "timezone": "Europe/Berlin"}
                kind, call = "write", ("appointment.create", p)
            else:
                kind = "read"
                call = [("appointment.list", {"team_id": subs[k % 3]}), ("team.effective_members", {"team_id": root}),
                        ("team.effective_teams", {}), ("appointment.get", {"appointment_id": appts[k % len(appts)]})][k % 4]
            t = time.time()
            status, _ = conn.op(*call)
            ms = (time.time() - t) * 1000
            with lock:
                lat[kind].append(ms)
                if status != 200:
                    errors[0] += 1
                elif kind == "write":
                    writes[0] += 1

    def burst(n, count):
        conn = Conn("alice")
        for i in range(count):
            s = sl.future(400 + i % 60)
            status, _ = conn.op("appointment.create", {"team_id": subs[i % 3], "title": f"B-{n}-{i}", "starts_at": sl.iso(s),
                                                       "ends_at": sl.iso(s.replace(hour=(s.hour + 1) % 24)), "timezone": "Europe/Berlin"})
            with lock:
                if status == 200:
                    writes[0] += 1
                else:
                    errors[0] += 1

    threads = [threading.Thread(target=feeder, daemon=True)] + [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(args.connections)]
    for t in threads:
        t.start()
    per = max(1, args.burst // 8)
    bthreads = [threading.Thread(target=burst, args=(i, per), daemon=True) for i in range(8)]
    for t in bthreads:
        t.start()
    time.sleep(args.duration)
    stop.set()
    for t in threads:
        t.join(timeout=5)
    for t in bthreads:
        t.join(timeout=120)
    return lat, errors[0], writes[0]


def one_run(args, project, pg, port):
    sl.mock_reset(latency_ms=50)
    root, subs, appts = setup_data()
    time.sleep(args.idle)
    idle = [stats(project) for _ in range(5)]
    idle_mem = statistics.median(sum(s[x]["mem"] for x in ("web", "worker")) for s in idle)
    sampler = Sampler(project, pg, port)
    sampler.start()
    t_start = time.time()
    lat, errors, writes = run_load(args, root, subs, appts)
    t_load_end = time.time()
    expected = writes * 2 + 120  # 2 Empfänger je Termin, plus Vorbereitung (60 Termine mit 2 Empfängern)
    drain = None
    deadline = time.time() + 300
    while time.time() < deadline:
        if sl.mock("GET", "/stats").json["effective"] >= expected:
            drain = time.time() - t_load_end
            break
        time.sleep(1)
    sampler.stop.set()
    sampler.join(timeout=5)
    during = [s for s in sampler.samples if t_start <= s["t"] <= t_load_end + 30]
    mems, cpus = summed(during, "mem"), summed(during, "cpu")
    allr = lat["read"] + lat["write"]
    return {
        "M1_idle_mem_mib": round(idle_mem, 1),
        "M2_peak_mem_mib": round(max(mems), 1) if mems else None,
        "M2_peak_web_mib": round(max(s["web"]["mem"] for s in during if "web" in s), 1) if during else None,
        "M2_peak_worker_mib": round(max(s["worker"]["mem"] for s in during if "worker" in s), 1) if during else None,
        "M3_mean_cpu_mcpu": round(statistics.mean(cpus), 1) if cpus else None,
        "M3_peak_cpu_mcpu": round(max(cpus), 1) if cpus else None,
        "M4_p50_ms": round(percentile(allr, 50), 1), "M4_p95_ms": round(percentile(allr, 95), 1), "M4_p99_ms": round(percentile(allr, 99), 1),
        "M4_read_p95_ms": round(percentile(lat["read"], 95), 1) if lat["read"] else None,
        "M4_write_p95_ms": round(percentile(lat["write"], 95), 1) if lat["write"] else None,
        "M13_pg_connections_max": max((s["pg"] for s in during), default=None),
        "requests": len(allr), "errors": errors, "writes": writes, "deliveries_expected": expected,
        "drain_seconds": round(drain, 1) if drain is not None else None,
    }


def startup_times(n=3):
    out = []
    for _ in range(n):
        sl.compose("stop", "web")
        t = time.time()
        sl.compose("start", "web")
        def ready():
            try:
                return sl.http("GET", sl.BASE_URL + "/healthz", timeout=2).status == 200
            except OSError:
                return False
        sl.wait_for(ready, timeout=120, interval=0.05, what="healthz")
        out.append(time.time() - t)
    return statistics.median(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--duration", type=int, default=600)
    ap.add_argument("--idle", type=int, default=300)
    ap.add_argument("--connections", type=int, default=50)
    ap.add_argument("--rps", type=int, default=20)
    ap.add_argument("--burst", type=int, default=1000)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    name = os.environ["SPIKE_NAME"]
    project, pg, port = f"chronos-spike-{name}", os.environ["PG_CONTAINER"], int(os.environ["PORT_PG"])
    runs = []
    for i in range(args.runs):
        print(f"== Lauf {i + 1}/{args.runs}", flush=True)
        runs.append(one_run(args, project, pg, port))
        print(json.dumps(runs[-1]), flush=True)
    med = {k: (round(statistics.median(r[k] for r in runs if r[k] is not None), 1) if any(r[k] is not None for r in runs) else None)
           for k in runs[0] if isinstance(runs[0][k], (int, float)) or runs[0][k] is None}
    med["M5_startup_seconds"] = round(startup_times(), 2)
    size = subprocess.run(["docker", "image", "inspect", args.image, "--format", "{{.Size}}"], capture_output=True, text=True).stdout.strip()
    med["M6_image_mb"] = round(int(size) / 1e6, 1) if size.isdigit() else None
    med["K1_pass"] = bool(med["M2_peak_mem_mib"] is not None and med["M2_peak_mem_mib"] <= 512 and med["M3_mean_cpu_mcpu"] <= 500)
    result = {"name": name, "image": args.image, "args": vars(args), "median": med, "runs": runs}
    print("\n== Median ==\n" + json.dumps(med, indent=1))
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "measure.json"), "w") as f:
            json.dump(result, f, indent=1)


if __name__ == "__main__":
    main()
