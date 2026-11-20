#!/usr/bin/env bash
# S-9: Das Modul der Fachbereiche (src/domain) darf das Modul der Kanäle (src/channels) und dessen Bibliotheken nicht kennen.
# Exit 0 = Regel eingehalten, 1 = Verstoß (mit Datei:Zeile).
set -u
cd "$(dirname "$0")/.."
pattern='(crate::|super::|self::|^|[^A-Za-z_])channels(::|;|[ ,{}]|$)|mod[[:space:]]+channels|ChannelKind|\b(lettre|web_push|webpush)\b|crate::worker|use[[:space:]]+crate::\{[^}]*channels'
hits=$(grep -rnE "$pattern" src/domain --include='*.rs' | grep -vE '^[^:]+:[0-9]+:[[:space:]]*//' || true)
if [ -n "$hits" ]; then
  echo "ARCHITEKTURVERSTOSS: src/domain darf das Kanal-Modul nicht kennen:" >&2
  echo "$hits" >&2
  exit 1
fi
echo "arch-check: ok (src/domain kennt src/channels nicht)"
