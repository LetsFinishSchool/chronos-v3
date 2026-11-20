#!/usr/bin/env bash
# M-7: Rückkopplung. Misst fünfmal: eine Quelldatei ändern -> `make test` (inkrementell übersetzen + Tests). Ausgabe: Median in Sekunden.
#   ./feedback.sh <kandidatenverzeichnis> <quelldatei relativ>
set -euo pipefail
dir=${1:?Kandidatenverzeichnis}; file=${2:?Quelldatei}
cd "$dir"
make test >/dev/null 2>&1 || true            # Aufwärmen (Abhängigkeiten, Cache)
cp "$file" "$file.bak"; trap 'mv "$file.bak" "$file"' EXIT
times=()
for i in 1 2 3 4 5; do
  printf '\n// feedback-messung %s\n' "$i" >> "$file"
  s=$(date +%s.%N); make test >/dev/null 2>&1 || true; e=$(date +%s.%N)
  times+=("$(echo "$e - $s" | bc -l)")
done
printf '%s\n' "${times[@]}" | sort -n | sed -n 3p | awk '{printf "M-7 Median: %.1f s\n", $1}'
