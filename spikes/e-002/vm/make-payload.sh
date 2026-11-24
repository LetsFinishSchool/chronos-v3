#!/usr/bin/env bash
# Packt die vorbereiteten Arbeitsbereiche und den KI-Schlüssel für die VM (landet in payload/, nicht versioniert).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
ws=${SPIKE_WS:-$HOME/spikes/e-002}
mkdir -p "$here/payload"
for l in typescript go rust; do
  [ -d "$ws/$l/.git" ] || { echo "Arbeitsbereich fehlt: $ws/$l (prepare_workspace.sh ausführen)" >&2; exit 1; }
  [ "$(git -C "$ws/$l" rev-list --count HEAD)" = 1 ] || { echo "$l enthält schon Arbeit, nicht verpacken" >&2; exit 1; }
done
tar -C "$ws" -czf "$here/payload/spikes.tgz" typescript go rust
( umask 077
  src="$HOME/.config/chronos-spike/anthropic.env"
  if [ -f "$src" ]; then cp "$src" "$here/payload/anthropic.env"; else : > "$here/payload/anthropic.env"; fi )
echo "Nutzlast: $(du -h "$here/payload/spikes.tgz" | cut -f1), Schlüsseldatei $( [ -s "$here/payload/anthropic.env" ] && echo vorhanden || echo LEER )"
