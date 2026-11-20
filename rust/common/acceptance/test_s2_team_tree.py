"""S-2: Team-Baum, Vererbung nach oben, Berechtigung an einer Stelle."""
import unittest

from spikelib import *


class S2TeamTree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_all()

    def setUp(self):
        self.a, self.b, self.c = alice(), bob(), carol()
        self.t0 = make_team(self.a, "S2-Wurzel-" + uid())
        self.t1 = make_team(self.a, "S2-Mitte-" + uid(), self.t0)
        self.t2 = make_team(self.a, "S2-Blatt-" + uid(), self.t1)
        self.a.ok("team.add_member", {"team_id": self.t2, "person_id": self.b.sub})  # Bob nur im Blatt
        self.a.ok("team.add_member", {"team_id": self.t0, "person_id": self.c.sub})  # Carol nur an der Wurzel

    def members(self, api, team):
        return [m["person_id"] for m in api.ok("team.effective_members", {"team_id": team})["members"]]

    def test_S2_effective_members_include_descendants(self):
        self.assertEqual(sorted(self.members(self.a, self.t0)), sorted([self.a.sub, self.b.sub, self.c.sub]))
        self.assertEqual(sorted(self.members(self.a, self.t1)), sorted([self.a.sub, self.b.sub]))
        self.assertEqual(sorted(self.members(self.a, self.t2)), sorted([self.a.sub, self.b.sub]))
        ms = self.members(self.a, self.t0)
        self.assertEqual(ms, sorted(ms), "nicht nach person_id sortiert")
        self.assertEqual(len(ms), len(set(ms)), "Duplikate")

    def test_S2_effective_teams_include_ancestors(self):
        ids = lambda api: {t["team_id"] for t in api.ok("team.effective_teams")["teams"]}
        self.assertTrue({self.t0, self.t1, self.t2} <= ids(self.b), "Bob muss das ganze Gerüst nach oben erben")
        self.assertIn(self.t0, ids(self.c))
        self.assertNotIn(self.t1, ids(self.c), "Mitgliedschaft erbt nicht nach unten")
        teams = self.b.ok("team.effective_teams")["teams"]
        self.assertEqual(teams, sorted(teams, key=lambda t: (t["name"], t["team_id"])))
        parent = {t["team_id"]: t["parent_id"] for t in teams}
        self.assertEqual(parent[self.t2], self.t1)
        self.assertEqual(parent[self.t1], self.t0)

    def test_S2_permissions(self):
        self.c.err("team.effective_members", {"team_id": self.t1}, 403, "forbidden")  # Carol: nur Wurzel
        self.c.err("team.create", {"name": "x", "parent_id": self.t1}, 403, "forbidden")
        self.c.err("team.add_member", {"team_id": self.t1, "person_id": self.c.sub}, 403, "forbidden")
        self.b.err("team.effective_teams", {"person_id": self.a.sub}, 403, "forbidden")
        self.a.err("team.effective_members", {"team_id": "00000000-0000-4000-8000-000000000000"}, 404, "not_found")
        self.a.err("team.add_member", {"team_id": self.t0, "person_id": "unbekannte-person"}, 404, "not_found")

    def test_S2_member_of_subteam_may_read_parent_appointments(self):
        appt = make_appointment(self.a, self.t0).json["result"]["appointment_id"]
        got = self.b.ok("appointment.get", {"appointment_id": appt})["appointment"]
        self.assertEqual(got["team_id"], self.t0)
        self.assertIn(appt, [x["id"] for x in self.b.ok("appointment.list", {"team_id": self.t0})["appointments"]])

    def test_S2_deep_tree_recursion(self):
        parent, chain = None, []
        for i in range(15):
            parent = make_team(self.a, f"S2-tief-{i:02d}-{uid()}", parent)
            chain.append(parent)
        self.a.ok("team.add_member", {"team_id": chain[-1], "person_id": self.b.sub})
        ids = {t["team_id"] for t in self.b.ok("team.effective_teams")["teams"]}
        self.assertTrue(set(chain) <= ids, "nicht alle 15 Ebenen nach oben aufgelöst")
        self.assertIn(self.b.sub, self.members(self.a, chain[0]))

    def test_S2_duplicate_add_member_is_noop(self):
        self.a.ok("team.add_member", {"team_id": self.t2, "person_id": self.b.sub})
        self.assertEqual(self.members(self.a, self.t2).count(self.b.sub), 1)


if __name__ == "__main__":
    unittest.main()
