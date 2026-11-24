"""N-1 (Phase 2): Operation appointment.reschedule ohne Zusatzaufwand. Erst nach Phase 1 ausführen."""
import time
import unittest

from spikelib import *


class N1Reschedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_all()
        for p in (alice(), bob()):
            p.ok("notification.set_channels", {"channels": ["mock"]})

    def test_N1_operation_in_description_and_tools(self):
        ops = {o["name"]: o for o in http("GET", BASE_URL + "/api/v1/operations").json["operations"]}
        self.assertIn("appointment.reschedule", ops)
        o = ops["appointment.reschedule"]
        self.assertTrue(o["mutating"] and o["preview_supported"])
        self.assertEqual(set(o["params_schema"]["required"]), {"appointment_id", "starts_at", "ends_at"})
        tools = {t["name"]: t for t in http("GET", BASE_URL + "/api/v1/ai/tools").json["tools"]}
        self.assertEqual(tools["appointment_reschedule"]["input_schema"], o["params_schema"])

    def test_N1_behaviour(self):
        mock_reset()
        a, b = alice(), bob()
        team = make_team(a)
        a.ok("team.add_member", {"team_id": team, "person_id": b.sub})
        appt = make_appointment(a, team).json["result"]["appointment_id"]
        s = future(60)
        params = {"appointment_id": appt, "starts_at": iso(s), "ends_at": iso(s.replace(hour=(s.hour + 2) % 24))}
        pv = a.ok("appointment.reschedule", params, preview=True)
        self.assertEqual(pv["count"], 1)
        self.assertNotEqual(a.ok("appointment.get", {"appointment_id": appt})["appointment"]["starts_at"], params["starts_at"])
        corr = uid("n1-")
        a.ok("appointment.reschedule", params, corr=corr)
        self.assertEqual(a.ok("appointment.get", {"appointment_id": appt})["appointment"]["starts_at"], params["starts_at"])
        top = a.ok("history.list", {"object_id": appt})["entries"][0]
        self.assertEqual(top["action"], "appointment.reschedule")
        rows = wait_for(lambda: [d for d in a.ok("notification.list", {"correlation_id": corr})["deliveries"]
                                 if d["result"] == "success"], what="Zustellung rescheduled")
        self.assertEqual(rows[0]["event_type"], "appointment.rescheduled")
        a.err("appointment.reschedule", {**params, "ends_at": params["starts_at"]}, 422, "validation_error")
        a.ok("history.undo", {"history_id": top["id"]})
        self.assertNotEqual(a.ok("appointment.get", {"appointment_id": appt})["appointment"]["starts_at"], params["starts_at"])


if __name__ == "__main__":
    unittest.main()
