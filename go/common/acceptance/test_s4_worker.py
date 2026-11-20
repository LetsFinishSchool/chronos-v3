"""S-4: Worker, Kanäle, Wiederholung, Ersatzkanal, Zustellprotokoll, Kosten, Logs. Zählt zu M-14 und M-15."""
import time
import unittest

from spikelib import *


class S4Worker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_all()

    def setUp(self):
        mock_reset()
        self.a, self.b = alice(), bob()
        self.team = make_team(self.a)
        self.a.ok("team.add_member", {"team_id": self.team, "person_id": self.b.sub})

    def trigger(self, corr):
        r = make_appointment(self.a, self.team, corr=corr)
        self.assertEqual(r.status, 200, r)

    def rows(self, corr):
        return self.a.ok("notification.list", {"correlation_id": corr, "limit": 500})["deliveries"]

    def test_M14_worker_health(self):
        r = http("GET", WORKER_HEALTH_URL + "/healthz")
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json.get("status"), "ok")
        self.assertEqual(http("GET", BASE_URL + "/healthz").status, 200)

    def test_M14_async_delivery_does_not_block_operation(self):
        self.b.ok("notification.set_channels", {"channels": ["mock"]})
        mock_reset(latency_ms=800)
        t0 = time.time()
        self.trigger(uid("s4-async-"))
        self.assertLess(time.time() - t0, 0.7, "Operation wartete offenbar auf die Zustellung")

    def test_M14_delivery_via_mock_once(self):
        self.b.ok("notification.set_channels", {"channels": ["mock"]})
        corr = uid("s4-mock-")
        self.trigger(corr)
        wait_for(lambda: any(d["result"] == "success" for d in self.rows(corr)), what="Zustellung über Mock")
        time.sleep(1.5)
        ok = [d for d in self.rows(corr) if d["result"] == "success"]
        self.assertEqual(len(ok), 1, ok)
        stats = mock("GET", "/stats").json
        self.assertEqual(stats["keys"].get(ok[0]["idempotency_key"]), 1)

    def test_M14_retry_then_fallback_channel_with_cost(self):
        self.b.ok("notification.set_channels", {"channels": ["mock", "email"]})
        mock_reset(fail_for=[self.b.sub])
        corr = uid("s4-fallback-")
        self.trigger(corr)
        rows = wait_for(lambda: (lambda r: r if any(d["channel"] == "email" and d["result"] == "success" for d in r) else None)(self.rows(corr)),
                        timeout=30, what="Ersatzkanal E-Mail")
        failed = [d for d in rows if d["channel"] == "mock" and d["result"] == "failed"]
        self.assertEqual(len(failed), 3, f"3 Versuche auf dem ersten Kanal erwartet: {rows}")
        self.assertEqual([d for d in rows if d["channel"] == "mock" and d["result"] == "success"], [])
        mail = [m for m in mailpit_messages_to(USERS["bob"])
                if corr in (mailpit_headers(m["ID"]).get("X-Chronos-Correlation-Id") or [])]
        self.assertEqual(len(mail), 1, "genau eine E-Mail mit dieser Korrelations-ID erwartet")
        h = mailpit_headers(mail[0]["ID"])
        key = next(d["idempotency_key"] for d in rows if d["channel"] == "email" and d["result"] == "success")
        self.assertEqual(h.get("X-Chronos-Idempotency-Key"), [key])
        costs = [c for c in self.a.ok("cost.list", {"limit": 500})["entries"]
                 if c["provider"] == "smtp" and c["trigger"]["correlation_id"] == corr]
        self.assertEqual(len(costs), 1, "genau ein Kostenposten für die E-Mail erwartet")
        self.assertEqual(costs[0]["amount_micro_eur"], EMAIL_PRICE_MICRO_EUR)
        self.assertEqual(costs[0]["quantity"], {"messages": 1})
        self.assertEqual(costs[0]["person_id"], self.a.sub, "Verursacher ist der Auslöser")
        mock_reset()

    def test_M14_skipped_without_precondition(self):
        self.b.ok("notification.set_channels", {"channels": ["webpush", "mock"]})
        corr = uid("s4-skip-")
        self.trigger(corr)
        rows = wait_for(lambda: (lambda r: r if any(d["channel"] == "mock" and d["result"] == "success" for d in r) else None)(self.rows(corr)),
                        what="Zustellung über Mock nach Überspringen")
        self.assertTrue(any(d["channel"] == "webpush" and d["result"] == "skipped" for d in rows), rows)

    def test_M14_all_channels_fail_is_final(self):
        self.b.ok("notification.set_channels", {"channels": ["mock"]})
        mock_reset(fail_for=[self.b.sub])
        corr = uid("s4-allfail-")
        self.trigger(corr)
        wait_for(lambda: len([d for d in self.rows(corr) if d["result"] == "failed"]) >= 3, timeout=30, what="3 Fehlversuche")
        time.sleep(max(3.0, RETRY_BASE_MS * 8 / 1000))
        rows = self.rows(corr)
        self.assertEqual(len([d for d in rows if d["result"] == "failed"]), 3, "es wird endlos wiederholt")
        self.assertEqual([d for d in rows if d["result"] == "success"], [])
        mock_reset()

    def test_M15_correlation_id_in_logs_of_web_and_worker(self):
        self.b.ok("notification.set_channels", {"channels": ["mock"]})
        corr = uid("s4-log-")
        self.trigger(corr)
        wait_for(lambda: any(d["result"] == "success" for d in self.rows(corr)), what="Zustellung")
        time.sleep(1)
        out = compose("logs", "--no-color", "--since", "5m", "web", "worker")
        seen = {}
        for line in out.splitlines():
            m = re.match(r"^(\S+?)(?:-\d+)?\s+\| (.*)$", line)
            if not m:
                continue
            try:
                j = json.loads(m.group(2))
            except ValueError:
                continue
            if j.get("correlation_id") == corr:
                seen.setdefault(m.group(1), []).append(j)
        self.assertTrue(any(k.endswith("web") for k in seen), f"keine Logzeile des Web mit {corr}: {list(seen)}")
        w = [j for k, v in seen.items() if k.endswith("worker") for j in v]
        self.assertTrue(w, f"keine Logzeile des Worker mit {corr}")
        for j in [j for v in seen.values() for j in v]:
            for f in ("ts", "level", "msg"):
                self.assertIn(f, j)
        self.assertTrue(any("event_id" in j for j in w), "Worker-Zeile ohne event_id")


if __name__ == "__main__":
    unittest.main()
