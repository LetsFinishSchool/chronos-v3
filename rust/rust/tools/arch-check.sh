#!/usr/bin/env bash
# S-9: Das Modul der Fachbereiche (src/domain) darf das Modul der Kanäle (src/channels) nicht kennen und nicht davon abhängen.
# Geprüft wird (1) kein Verweis auf channels/Kanal-Bibliotheken, (2) Positivliste: domain darf nur crate::core, crate::error,
# crate::register und das eigene Modul benutzen (damit auch indirekte Wege über notify/worker/web/auth auffallen).
# Exit 0 = Regel eingehalten, 1 = Verstoß (mit Datei:Zeile).
set -u
cd "$(dirname "$0")/.."
code() { grep -rnE "$1" src/domain --include='*.rs' | grep -vE '^[^:]+:[0-9]+:[[:space:]]*//' || true; }
direct=$(code '(^|[^A-Za-z_])channels([^A-Za-z_]|$)|ChannelKind|\b(lettre|web_push|webpush)\b')
indirect=$(code 'crate::' | grep -vE 'crate::(core|error|register|domain)\b' | grep -vE 'crate::\{(core|error|register|domain)(::[A-Za-z_{},: ]*)?(, *(core|error|register|domain)[A-Za-z_{}:, ]*)*\}' || true)
if [ -n "$direct$indirect" ]; then
  echo "ARCHITEKTURVERSTOSS: src/domain darf das Kanal-Modul nicht kennen:" >&2
  [ -n "$direct" ] && echo "$direct" >&2
  [ -n "$indirect" ] && echo "$indirect" >&2
  exit 1
fi
echo "arch-check: ok (src/domain kennt src/channels nicht)"
