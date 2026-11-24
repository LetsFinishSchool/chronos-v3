#!/usr/bin/env bash
# V-6/RB-008: Prüft einen Arbeitsbereich (oder das Repository) auf Geheimnisse. Exit 1 bei Treffern.
# Der Platzhalter "guarded-by-proxy" (Schlüsselersatz für die Spike-Anwendungen) ist bewusst erlaubt.
set -uo pipefail
dir=${1:-.}
hits=$(grep -rIEn --exclude-dir=.stack --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=target \
   --exclude=check_no_secrets.sh \
   -e 'sk-ant-[A-Za-z0-9_-]{10,}' -e 'ANTHROPIC_API_KEY=[A-Za-z0-9_-]{12,}' -e 'VAPID_PRIVATE_KEY=[A-Za-z0-9_-]{30,}' \
   -e 'BEGIN (RSA |EC )?PRIVATE KEY' "$dir" | grep -v 'guarded-by-proxy')
if [ -n "$hits" ]; then echo "$hits"; echo "TREFFER: mögliche Geheimnisse (siehe oben)" >&2; exit 1; fi
echo "keine Geheimnisse gefunden in $dir"
