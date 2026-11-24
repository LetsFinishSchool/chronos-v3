#!/usr/bin/env bash
# Prüft die Ablaufdaten der Ausnahmen in deny.toml (ADR-013).
# Datum im Format "bis JJJJ-MM-TT". Überschritten: Exit-Code 1.
# Ab 14 Tagen vorher: Warnung, Exit-Code 0.
# DENY_TODAY=JJJJ-MM-TT ersetzt das heutige Datum (für Tests).
set -euo pipefail

file="${1:-$(dirname "$0")/../deny.toml}"
warn_days=14
today="${DENY_TODAY:-$(date -u +%F)}"
today_s=$(date -u -d "$today" +%s)
failed=0

summary() {
    echo "$1"
    if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
        echo "$1" >> "$GITHUB_STEP_SUMMARY"
    fi
}

while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ bis[[:space:]]+([0-9]{4}-[0-9]{2}-[0-9]{2}) ]] || continue
    date="${BASH_REMATCH[1]}"
    if ! expiry_s=$(date -u -d "$date" +%s 2>/dev/null); then
        summary "FEHLER: ungültiges Datum $date in: $line"
        failed=1
        continue
    fi
    days=$(( (expiry_s - today_s) / 86400 ))
    if (( days < 0 )); then
        summary "FEHLER: Ausnahme abgelaufen am $date: $line"
        failed=1
    elif (( days <= warn_days )); then
        summary "WARNUNG: Ausnahme läuft in $days Tagen ab ($date): $line"
    fi
done < "$file"

exit "$failed"
