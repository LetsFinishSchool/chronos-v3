"""S-10: Frontend-Brücke. Typisierter Client aus der Operationsbeschreibung (Q-5)."""
import os
import shutil
import subprocess
import unittest

from spikelib import *

CHECK = os.path.join(os.path.dirname(HERE), "bridge-check")
TSC = os.environ.get("TSC", "npx --yes -p typescript@5.6 tsc").split()


@unittest.skipUnless(CANDIDATE_DIR, "CANDIDATE_DIR nicht gesetzt")
class S10Bridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = subprocess.run(["make", "-C", CANDIDATE_DIR, "bridge"], capture_output=True, text=True,
                             env={**os.environ, "BASE_URL": BASE_URL})
        assert out.returncode == 0, f"make bridge fehlgeschlagen:\n{out.stdout}\n{out.stderr}"
        cls.bridge = os.path.join(CANDIDATE_DIR, "bridge")
        assert os.path.isfile(os.path.join(cls.bridge, "client.ts")), "bridge/client.ts fehlt"
        assert os.path.isdir(os.path.join(cls.bridge, "generated")), "bridge/generated fehlt"

    def compile_with(self, name):
        dst = os.path.join(self.bridge, "check_" + name)
        shutil.copy(os.path.join(CHECK, name), dst)
        try:
            return subprocess.run(TSC + ["--noEmit", "-p", self.bridge], capture_output=True, text=True,
                                  cwd=CANDIDATE_DIR)
        finally:
            os.remove(dst)

    def test_S10_baseline_compiles(self):
        r = subprocess.run(TSC + ["--noEmit", "-p", self.bridge], capture_output=True, text=True, cwd=CANDIDATE_DIR)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_S10_good_call_compiles(self):
        # good.ts importiert "./client": die Kopie liegt im selben Verzeichnis
        r = self.compile_with("good.ts")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_S10_bad_calls_fail(self):
        for f in ("bad-param-type.ts", "bad-missing-param.ts", "bad-unknown-op.ts"):
            with self.subTest(f):
                r = self.compile_with(f)
                self.assertNotEqual(r.returncode, 0, f"{f} wurde fälschlich akzeptiert")
                # Der Fehler muss aus der Prüfdatei stammen (nicht z. B. aus fehlendem Compiler oder kaputtem Client)
                self.assertIn("check_" + f, r.stdout, "Übersetzungsfehler stammt nicht aus der Prüfdatei:\n" + r.stdout + r.stderr)
                self.assertRegex(r.stdout, r"error TS\d+")


if __name__ == "__main__":
    unittest.main()
