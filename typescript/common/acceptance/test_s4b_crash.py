"""K5: SIGKILL des Workers während des Versands; kein Verlust, wirksam höchstens einmal je Schlüssel."""
import time
import unittest

from spikelib import *

N = 100


class K5Crash(unittest.TestCase):
    def test_K5_kill_worker_no_loss_no_duplicates(self):
        register_all()
        a, b, c = alice(), bob(), carol()
        for p in (a, b, c):
            p.ok("notification.set_channels", {"channels": ["mock"]})
        team = make_team(a)
        for p in (b, c):
            a.ok("team.add_member", {"team_id": team, "person_id": p.sub})
        mock_reset(latency_ms=200)
        compose("stop", "worker")  # Rückstau erzeugen, damit der Abbruch sicher mitten im Versand liegt
        run = uid("k5-")
        expected = set()
        for i in range(N):
            corr = f"{run}-{i}"
            r = make_appointment(a, team, corr=corr, days=40 + i)
            self.assertEqual(r.status, 200, r)
            expected |= {(corr, b.sub), (corr, c.sub)}
        compose("start", "worker")
        wait_for(lambda: mock("GET", "/stats").json["effective"] >= 10, timeout=60, what="erste Zustellungen")
        compose("kill", "-s", "SIGKILL", "worker")
        at_kill = mock("GET", "/stats").json["effective"]
        self.assertLess(at_kill, 2 * N, "Worker war schon fertig, Test nicht aussagekräftig (Mock-Latenz erhöhen)")
        note("K5_wirksam_beim_Abbruch", at_kill)
        time.sleep(1)
        compose("start", "worker")
        stats = wait_for(lambda: (lambda s: s if len(s["deliveries"]) >= 2 * N else None)(mock("GET", "/stats").json),
                         timeout=300, interval=1, what="Abarbeitung aller Zustellungen nach Neustart")
        pairs = [(d["correlation_id"], d["recipient"]) for d in stats["deliveries"]]
        self.assertEqual(len(pairs), len(set(pairs)), "wirksame Zustellung mehrfach")
        self.assertEqual(set(pairs), expected, "Zustellungen verloren oder fremde Zustellungen")
        note("K5_Duplikat_Versuche", stats["duplicates"])
        missing = []
        for i in range(N):
            corr = f"{run}-{i}"
            ok = {d["recipient"] for d in a.ok("notification.list", {"correlation_id": corr})["deliveries"] if d["result"] == "success"}
            if ok != {b.sub, c.sub}:
                missing.append(corr)
        self.assertFalse(missing, f"Zustellprotokoll ohne Erfolgszeile: {missing[:5]}")


if __name__ == "__main__":
    unittest.main()
