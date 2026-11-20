#!/usr/bin/env bash
# Wartet (höchstens 2 h), bis Claude Code in der VM angemeldet ist, und startet dann die Agenten.
#   ./wait-and-start.sh <MODELL>
set -uo pipefail
model=${1:?Modellkennung}
here=$(cd "$(dirname "$0")" && pwd); cd "$here"
for i in $(seq 1 240); do
  out=$(vagrant ssh -c "sudo -u agent bash -lc 'cd ~ && timeout 90 claude -p \"antworte nur mit: ok\" --model $model 2>&1 | head -2'" 2>/dev/null)
  if echo "$out" | grep -qi "^ok"; then
    echo "$(date -u +%T) Anmeldung erkannt, starte Agenten ($model)"
    vagrant ssh -c "sudo -u agent bash -lc '~/start-agents.sh $model'"
    exit $?
  fi
  echo "$(date -u +%T) noch nicht angemeldet ($(echo "$out" | head -1 | cut -c1-60))"
  sleep 30
done
echo "Zeitüberschreitung: keine Anmeldung in 2 h" >&2; exit 1
