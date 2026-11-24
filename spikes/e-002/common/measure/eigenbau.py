#!/usr/bin/env python3
"""M-9: Eigenbau-Anteil. Zählt Zeilen zwischen den Markierungen EIGENBAU:BEGIN und EIGENBAU:END (beliebiges Kommentarzeichen)
im Verzeichnis des Kandidaten, geteilt durch alle Quellzeilen (ohne generierte Dateien, Tests, Abhängigkeiten).
    python3 eigenbau.py <kandidatenverzeichnis>
"""
import os, re, sys
root = sys.argv[1]
SKIP = {"node_modules", "target", "vendor", ".git", "generated", "dist", "bridge", ".venv", "venv", "__pycache__", "tests"}
EXT = (".ts", ".go", ".rs", ".sql", ".py")
total = own = 0
for d, dirs, files in os.walk(root):
    dirs[:] = [x for x in dirs if x not in SKIP]
    for f in files:
        if not f.endswith(EXT) or re.search(r"(_test\.go|\.test\.ts|\.spec\.ts|_test\.py|^test_.*\.py|^conftest\.py)$", f):
            continue
        inside = False
        for line in open(os.path.join(d, f), encoding="utf-8", errors="replace"):
            if not line.strip():
                continue
            if "EIGENBAU:BEGIN" in line:
                inside = True
                continue
            if "EIGENBAU:END" in line:
                inside = False
                continue
            total += 1
            own += inside
print(f"Eigenbau {own} von {total} Zeilen = {100 * own / total if total else 0:.1f} %  (M-9)")
