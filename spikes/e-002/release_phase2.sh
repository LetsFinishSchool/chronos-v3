#!/usr/bin/env bash
# V-5: Stellt die Zusatzaufgabe bereit, NACHDEM der Agent PHASE-1-FERTIG committet hat.
set -euo pipefail
dest=${1:?Arbeitsbereich}
here=$(cd "$(dirname "$0")" && pwd)
( cd "$dest" && git log --format=%s | grep -qx 'PHASE-1-FERTIG' ) || { echo "Phase 1 noch nicht abgeschlossen (Commit PHASE-1-FERTIG fehlt)" >&2; exit 1; }
cp "$here/briefing/PHASE2.md" "$dest/PHASE2.md"
echo "PHASE2.md bereitgestellt. Agenten mit dem Satz fortsetzen: 'Phase 2 liegt in PHASE2.md. Setze sie um.'"
