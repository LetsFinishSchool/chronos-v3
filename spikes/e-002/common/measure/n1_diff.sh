#!/usr/bin/env bash
# M-11: Berührte Dateien der Zusatzaufgabe N-1. Voraussetzung: Der Agent hat Phase 1 mit der Commit-Nachricht
# "PHASE-1-FERTIG" abgeschlossen und N-1 danach committet.
#   ./n1_diff.sh <arbeitsverzeichnis>
set -euo pipefail
cd "${1:?Arbeitsverzeichnis}"
base=$(git log --format=%H --grep='^PHASE-1-FERTIG' -n1)
echo "Berührte Dateien seit Phase 1 (ohne generierte, Doku, Protokolle):"
git diff --name-only "$base"..HEAD | grep -Ev '(^|/)(generated|node_modules|target|vendor)/|(^|/)(README|PROTOKOLL)\.md$|\.lock$|go\.sum$' | tee /dev/stderr | wc -l | awk '{print "M-11 berührte Dateien: " $1}'
