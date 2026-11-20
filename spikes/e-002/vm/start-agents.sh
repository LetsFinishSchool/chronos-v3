#!/usr/bin/env bash
# In der VM als Benutzer 'agent': startet je Kandidat einen Agenten in einer eigenen tmux-Sitzung (spike-<name>).
#   ./start-agents.sh <MODELL> [kandidat ...]       Standard: typescript go rust
# Authentifizierung von Claude Code: Umgebungsvariable ANTHROPIC_API_KEY aus ~/.config/chronos-spike/claude.env,
# oder zuvor mit 'claude' interaktiv angemeldet (vagrant ssh, dann als agent 'claude').
set -euo pipefail
model=${1:?Modellkennung}; shift || true
langs=${*:-typescript go rust}
[ -f "$HOME/.config/chronos-spike/claude.env" ] && { set -a; . "$HOME/.config/chronos-spike/claude.env"; set +a; }
source "$HOME/.cargo/env" 2>/dev/null || true
export PATH="$PATH:/usr/local/go/bin:$HOME/go/bin"
for l in $langs; do
  d="$HOME/spikes/e-002/$l"
  tmux has-session -t "spike-$l" 2>/dev/null && { echo "Sitzung spike-$l läuft schon"; continue; }
  date -u +%FT%TZ > "$d/.gestartet"
  tmux new-session -d -s "spike-$l" -c "$d" \
    "timeout 8h claude -p \"\$(cat START-PROMPT.txt)\" --model '$model' --dangerously-skip-permissions 2>&1 | tee ../$l.log; echo ENDE >> ../$l.log; sleep 86400"
  echo "gestartet: spike-$l ($d)"
done
