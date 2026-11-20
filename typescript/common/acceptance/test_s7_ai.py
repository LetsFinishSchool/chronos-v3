"""S-7 / K6: echter KI-Aufruf mit Werkzeugschema aus der Operationsbeschreibung; Kostenposten."""
import unittest

from spikelib import *


@unittest.skipIf(SKIP_AI, "SKIP_AI=1 gesetzt")
class K6Ai(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_all()
        cls.ops = {o["name"]: o for o in http("GET", BASE_URL + "/api/v1/operations").json["operations"]}

    def ask(self, team, corr):
        prompt = (f"Lege im Team {team} einen Termin mit dem Titel 'KI-Test' für den 1. Dezember 2026 von 18:00 bis "
                  f"19:00 Uhr in der Zeitzone Europe/Berlin an. Gib die Zeiten in UTC an.")
        return alice().op("ai.ask", {"prompt": prompt, "team_id": team}, corr=corr)

    def test_K6_tool_call_matches_schema_and_costs_recorded(self):
        a = alice()
        team = make_team(a)
        last = None
        for attempt in range(3):  # Modellverhalten ist nicht deterministisch
            corr = uid("k6-")
            r = self.ask(team, corr)
            self.assertEqual(r.status, 200, r)
            calls = [c for c in r.json["result"]["proposed_calls"] if c["name"] == "appointment.create"]
            if calls:
                last = (corr, r.json["result"], calls[0])
                break
        self.assertTrue(last, "kein Vorschlag appointment.create in 3 Versuchen")
        corr, res, call = last
        errs = schema_errors(self.ops["appointment.create"]["params_schema"], call["input"])
        self.assertFalse(errs, f"Werkzeugeingabe passt nicht zum Schema: {errs}")
        self.assertEqual(call["input"]["team_id"], team)
        self.assertIn("KI-Test", call["input"]["title"])
        self.assertEqual(call["input"]["starts_at"], "2026-12-01T17:00:00Z")
        self.assertEqual(call["input"]["ends_at"], "2026-12-01T18:00:00Z")
        self.assertEqual(call["input"]["timezone"], "Europe/Berlin")
        self.assertGreater(res["usage"]["input_tokens"], 0)
        self.assertGreater(res["usage"]["output_tokens"], 0)
        # nichts wurde ausgeführt
        self.assertEqual(a.ok("appointment.list", {"team_id": team})["appointments"], [])
        costs = [c for c in a.ok("cost.list", {"limit": 500})["entries"]
                 if c["provider"] == "anthropic" and c["trigger"]["correlation_id"] == corr]
        self.assertEqual(len(costs), 1, costs)
        self.assertEqual(costs[0]["quantity"], {"input_tokens": res["usage"]["input_tokens"],
                                                "output_tokens": res["usage"]["output_tokens"]})
        self.assertIsInstance(costs[0]["amount_micro_eur"], int)
        self.assertEqual(costs[0]["person_id"], a.sub)


if __name__ == "__main__":
    unittest.main()
