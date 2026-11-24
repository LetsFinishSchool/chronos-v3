"""S-1: Operationsbeschreibung, Validierung, Vorschau, Korrelations-ID."""
import time
import unittest

from spikelib import *

MUTATING = {"team.create", "team.add_member", "appointment.create", "appointment.cancel", "history.undo",
            "series.create", "notification.set_channels", "notification.subscribe_push", "notification.test_push"}
READING = {"team.effective_members", "team.effective_teams", "appointment.get", "appointment.list", "history.list",
           "series.occurrences", "notification.list", "cost.list", "ai.ask"}


class S1Operations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_all()
        r = http("GET", BASE_URL + "/api/v1/operations")
        assert r.status == 200, r
        cls.ops = {o["name"]: o for o in r.json["operations"]}

    def test_S1_required_operations_present(self):
        missing = (MUTATING | READING) - set(self.ops)
        self.assertFalse(missing, f"fehlende Operationen: {missing}")

    def test_S1_descriptors_complete(self):
        for name, o in self.ops.items():
            with self.subTest(op=name):
                for k in ("description", "mutating", "preview_supported", "params_schema", "result_schema"):
                    self.assertIn(k, o)
                self.assertEqual(o["params_schema"].get("type"), "object")
                self.assertIs(o["params_schema"].get("additionalProperties"), False)
                self.assertEqual(o["result_schema"].get("type"), "object")
        for n in MUTATING & {"appointment.cancel", "history.undo"}:
            self.assertTrue(self.ops[n]["preview_supported"], n)
        for n in MUTATING:
            self.assertIs(self.ops[n]["mutating"], True, n)
        for n in READING - {"ai.ask"}:
            self.assertIs(self.ops[n]["mutating"], False, n)

    def test_S1_ai_tools_derived_from_operations(self):
        r = http("GET", BASE_URL + "/api/v1/ai/tools")
        self.assertEqual(r.status, 200, r)
        tools = {t["name"]: t for t in r.json["tools"]}
        self.assertEqual(set(tools), {n.replace(".", "_") for n in self.ops}, "Werkzeugliste weicht von Operationen ab")
        for n, o in self.ops.items():
            t = tools[n.replace(".", "_")]
            self.assertEqual(t["input_schema"], o["params_schema"], n)
            self.assertTrue(t["description"], n)

    def test_S1_validation_errors(self):
        a = alice()
        a.err("team.create", {}, 422, "validation_error")
        a.err("team.create", {"name": 42}, 422, "validation_error")
        a.err("team.create", {"name": "x", "unbekannt": 1}, 422, "validation_error")
        a.err("team.create", {"name": ""}, 422, "validation_error")

    def test_S1_unknown_operation_and_auth(self):
        a = alice()
        a.err("gibt.es.nicht", {}, 404, "not_found")
        a.err("team.effective_teams", {}, 401, "unauthenticated", bearer=False)
        r = http("POST", BASE_URL + "/api/v1/operations/team.effective_teams",
                 headers={"Authorization": "Bearer ungueltig"}, body={"params": {}})
        self.assertEqual(r.status, 401, r)

    def test_S1_correlation_id_echo_and_generated(self):
        r = alice().op("team.effective_teams", corr="s1-echo-1")
        self.assertEqual(r.headers.get("X-Correlation-Id"), "s1-echo-1")
        r2 = alice().op("team.effective_teams")
        self.assertTrue(r2.headers.get("X-Correlation-Id"), "keine Korrelations-ID erzeugt")

    def test_S1_preview_has_no_effect(self):
        a, b = alice(), bob()
        team = make_team(a)
        a.ok("team.add_member", {"team_id": team, "person_id": b.sub})
        b.ok("notification.set_channels", {"channels": ["mock"]})
        mock_reset()
        appt = make_appointment(a, team).json["result"]["appointment_id"]
        before = len(a.ok("history.list", {"object_id": appt})["entries"])
        corr = uid("preview-")
        pv = a.ok("appointment.cancel", {"appointment_id": appt}, preview=True, corr=corr)
        self.assertEqual(pv["count"], 1)
        self.assertEqual(pv["affected"][0]["id"], appt)
        self.assertEqual(a.ok("appointment.get", {"appointment_id": appt})["appointment"]["status"], "geplant")
        self.assertEqual(len(a.ok("history.list", {"object_id": appt})["entries"]), before, "Vorschau schrieb Verlauf")
        time.sleep(2)
        self.assertEqual(a.ok("notification.list", {"correlation_id": corr})["deliveries"], [],
                         "Vorschau erzeugte Zustellungen")


if __name__ == "__main__":
    unittest.main()
