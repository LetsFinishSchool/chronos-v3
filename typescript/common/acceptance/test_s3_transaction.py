"""S-3: Transaktion aus Zustand, Verlauf und Ereignis; Rückgängig; Atomarität (Fehlerinjektion)."""
import time
import unittest

from spikelib import *


class S3Transaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_all()
        for p in (alice(), bob(), carol()):
            p.ok("notification.set_channels", {"channels": ["mock"]})

    def setUp(self):
        mock_reset()
        self.a, self.b = alice(), bob()
        self.team = make_team(self.a)
        self.a.ok("team.add_member", {"team_id": self.team, "person_id": self.b.sub})

    def create(self, corr=None):
        r = make_appointment(self.a, self.team, corr=corr)
        self.assertEqual(r.status, 200, r)
        return r.json["result"]["appointment_id"]

    def history(self, obj):
        return self.a.ok("history.list", {"object_id": obj})["entries"]

    def status(self, appt):
        return self.a.ok("appointment.get", {"appointment_id": appt})["appointment"]["status"]

    def test_S3_create_writes_history_and_event(self):
        corr = uid("s3-create-")
        appt = self.create(corr)
        e = self.history(appt)
        self.assertEqual(len(e), 1)
        e = e[0]
        self.assertEqual(e["action"], "appointment.create")
        self.assertIsNone(e["before"])
        self.assertEqual(e["after"]["status"], "geplant")
        self.assertEqual(e["correlation_id"], corr)
        self.assertTrue(e["bundle_id"])
        self.assertIn(self.a.sub, json.dumps(e["actor"]))
        rows = wait_for(lambda: [d for d in self.a.ok("notification.list", {"correlation_id": corr})["deliveries"]
                                 if d["result"] == "success"], what="Zustellung an Bob")
        self.assertEqual({d["recipient"] for d in rows}, {self.b.sub}, "Empfänger = alle außer dem Auslöser")
        d = rows[0]
        self.assertEqual(d["event_type"], "appointment.created")
        self.assertEqual(d["trigger"]["kind"], "person")
        self.assertEqual(d["trigger"]["actor"], self.a.sub)
        self.assertEqual(d["channel"], "mock")
        self.assertEqual(d["correlation_id"], corr)
        self.assertEqual(d["idempotency_key"], f"{d['event_id']}:{self.b.sub}:mock")

    def test_S3_cancel_and_conflict(self):
        appt = self.create()
        self.a.ok("appointment.cancel", {"appointment_id": appt})
        self.assertEqual(self.status(appt), "abgesagt")
        top = self.history(appt)[0]
        self.assertEqual(top["action"], "appointment.cancel")
        self.assertEqual(top["before"]["status"], "geplant")
        self.assertEqual(top["after"]["status"], "abgesagt")
        self.a.err("appointment.cancel", {"appointment_id": appt}, 409, "conflict")
        self.assertIn(appt, [x["id"] for x in self.a.ok("appointment.list", {"team_id": self.team})["appointments"]])

    def test_S3_undo_cancel_and_redo(self):
        appt = self.create()
        self.a.ok("appointment.cancel", {"appointment_id": appt})
        cancel_entry = self.history(appt)[0]
        pv = self.a.ok("history.undo", {"history_id": cancel_entry["id"]}, preview=True)
        self.assertGreaterEqual(pv["count"], 1)
        self.assertEqual(self.status(appt), "abgesagt", "Vorschau darf nichts ändern")
        undo_id = self.a.ok("history.undo", {"history_id": cancel_entry["id"]})["history_id"]
        self.assertEqual(self.status(appt), "geplant")
        entries = {e["id"]: e for e in self.history(appt)}
        self.assertTrue(entries[cancel_entry["id"]]["undone"])
        self.assertEqual(entries[undo_id]["action"], "history.undo")
        self.assertEqual(entries[undo_id]["undo_of"], cancel_entry["id"])
        # erneutes Rückgängig desselben Eintrags: Zustand passt nicht mehr
        self.a.err("history.undo", {"history_id": cancel_entry["id"]}, 409, "not_undoable")
        # Rückgängig des Rückgängig stellt die Absage wieder her
        self.a.ok("history.undo", {"history_id": undo_id})
        self.assertEqual(self.status(appt), "abgesagt")

    def test_S3_undo_create_deletes(self):
        appt = self.create()
        create_entry = self.history(appt)[0]
        self.a.ok("history.undo", {"history_id": create_entry["id"]})
        self.a.err("appointment.get", {"appointment_id": appt}, 404, "not_found")
        self.assertNotIn(appt, [x["id"] for x in self.a.ok("appointment.list", {"team_id": self.team})["appointments"]])

    def test_S3_undo_emits_revert_event(self):
        corr = uid("s3-undo-")
        appt = self.create()
        self.a.ok("appointment.cancel", {"appointment_id": appt})
        entry = self.history(appt)[0]
        self.a.ok("history.undo", {"history_id": entry["id"]}, corr=corr)
        rows = wait_for(lambda: self.a.ok("notification.list", {"correlation_id": corr})["deliveries"],
                        what="Ereignis change.reverted")
        self.assertEqual(rows[0]["event_type"], "change.reverted")

    def test_S3_atomic_rollback_on_fault(self):
        corr = uid("s3-fault-")
        title = uid("fault-")
        r = make_appointment(self.a, self.team, title=title, corr=corr, headers={"X-Spike-Fault": "after_history"})
        self.assertEqual(r.status, 500, f"Fehlerinjektion nicht wirksam (SPIKE_FAULTS=1 gesetzt?): {r}")
        self.assertNotIn(title, [x["title"] for x in self.a.ok("appointment.list", {"team_id": self.team})["appointments"]],
                         "Objekt blieb trotz Fehler bestehen")
        hist = self.a.ok("history.list", {"limit": 200})["entries"]
        self.assertNotIn(corr, [e["correlation_id"] for e in hist], "Verlaufseintrag blieb bestehen")
        time.sleep(2)
        self.assertEqual(self.a.ok("notification.list", {"correlation_id": corr})["deliveries"], [],
                         "Ereignis wurde trotz Fehler zugestellt")

    def test_S3_header_ignored_without_faults_flag_is_environment_check(self):
        """Nur Hinweis: ohne SPIKE_FAULTS=1 muss der Header wirkungslos sein (nicht automatisch prüfbar)."""
        self.skipTest("manuell: Dienst ohne SPIKE_FAULTS starten und Header senden, Antwort muss 200 sein")


if __name__ == "__main__":
    unittest.main()
