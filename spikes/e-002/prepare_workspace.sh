#!/usr/bin/env bash
# V-5: Bereitet einen isolierten Arbeitsbereich für EINEN Spike-Agenten vor.
#   ./prepare_workspace.sh <typescript|go|rust> [zielverzeichnis]      Standard: $HOME/spikes/e-002/<name>
# Der Arbeitsbereich enthält nur: common/ (ohne measure/ und reference/), BRIEFING.md, START-PROMPT.txt, ein frisches git-Repository.
# Phase 2 wird mit ./release_phase2.sh <zielverzeichnis> bereitgestellt.
set -euo pipefail
lang=${1:?typescript|go|rust}
here=$(cd "$(dirname "$0")" && pwd)
line=$(grep -E "^$lang\|" "$here/briefing/stacks.env") || { echo "unbekannter Kandidat $lang" >&2; exit 2; }
off=$(echo "$line" | cut -d'|' -f2); stack=$(echo "$line" | cut -d'|' -f3-)
dest=${2:-$HOME/spikes/e-002/$lang}
[ -e "$dest" ] && { echo "Ziel existiert schon: $dest" >&2; exit 1; }
mkdir -p "$dest/$lang"
rsync -a --exclude 'measure' --exclude '__pycache__' "$here/common/" "$dest/common/"
python3 - "$here/briefing/BRIEFING.template.md" "$dest/BRIEFING.md" "$lang" "$off" "$stack" <<'PY'
import sys
src, dst, lang, off, stack = sys.argv[1:6]
off = int(off)
s = open(src, encoding="utf-8").read()
for k, v in {"__LANG__": lang, "__OFFSET__": str(off), "__STACK__": stack, "__PORT_WEB__": str(8080 + off),
             "__PORT_WORKER__": str(8081 + off), "__PORT_KC__": str(8180 + off), "__PORT_MAILUI__": str(8025 + off),
             "__PORT_MOCK__": str(8090 + off)}.items():
    s = s.replace(k, v)
open(dst, "w", encoding="utf-8").write(s)
PY
cat > "$dest/$lang/PROTOKOLL.md" <<EOT
# Protokoll $lang

Start (UTC): _hier eintragen: \`date -u\`_

| Aufgabe | Beginn (UTC) | Ende (UTC) | Anmerkung |
|---|---|---|---|

## Korrekturschleifen

_Eine Zeile je Schleife mit Kurzgrund._
EOT
echo "Lies BRIEFING.md in diesem Verzeichnis vollständig und setze es um. Beginne sofort und höre erst auf, wenn FERTIG im Protokoll steht." > "$dest/START-PROMPT.txt"
printf '.stack/\nnode_modules/\ntarget/\n__pycache__/\n*.env\n' > "$dest/.gitignore"
( cd "$dest" && git init -q && git add -A && git -c user.name=spike -c user.email=spike@example.test commit -q -m "Ausgangslage" )
echo "Arbeitsbereich bereit: $dest (Portversatz $off)"
echo "Agent starten mit Arbeitsverzeichnis $dest; erster Auftrag: Inhalt von START-PROMPT.txt"
