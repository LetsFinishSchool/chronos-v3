#!/usr/bin/env bash
# Manueller Web-Push-Test K3 (siehe common/acceptance/manual/K3-webpush.md).
#   ./k3-test.sh typescript|go|rust|rust-wpn|python
# Startet den Stack des Kandidaten in der VM, gibt ein Token für alice aus und leitet den Web-Port auf diesen Rechner.
# Der Tunnel läuft im Vordergrund, mit Strg+C beenden. Danach den Stack wieder stoppen: ./k3-test.sh stop <kandidat>
set -euo pipefail
cd "$(dirname "$0")"
cmd=${1:?typescript|go|rust|stop|token}
if [ "$cmd" = stop ] || [ "$cmd" = token ]; then n=${2:?Kandidat}; else n=$cmd; fi
case $n in typescript) off=0;; go) off=1000;; rust) off=2000;; rust-wpn) off=4000;; python) off=5000;; *) echo "Kandidat: typescript, go, rust, rust-wpn oder python" >&2; exit 2;; esac
vagrant status 2>/dev/null | grep -q "running (virtualbox)" || vagrant up
if [ "$cmd" = stop ]; then
  vagrant ssh -c "sudo -u agent bash -c 'cd ~/eval/common/env && ./stack.sh down $n $off'" >/dev/null 2>&1 || true; echo "Stack $n gestoppt."; exit 0
fi
web=$((8080+off)); kc=$((8180+off)); lp=$web
# 10080 sperren Chrome und Firefox als unsicheren Port (Amanda): lokal auf 12080 ausweichen
[ "$web" = 10080 ] && lp=12080
if [ "$cmd" = token ]; then vagrant ssh -c "sudo -u agent bash -s -- $kc" < k3-token.sh; exit 0; fi
vagrant ssh -c "sudo -u agent bash -s -- $n $off" < k3-remote.sh
vagrant ssh -c "sudo -u agent bash -s -- $kc" < k3-token.sh > /tmp/k3-token.txt
key=$(vagrant ssh -c "sudo -u agent bash -c 'grep ^VAPID_PUBLIC_KEY= ~/eval/.stack/$n/secrets.env | cut -d= -f2'" | tr -d '\r')
cat <<TXT

Bereit. Im Browser öffnen:  http://localhost:$lp/static/push-test.html?key=$key
1. Benachrichtigungen für localhost erlauben, wenn der Browser fragt.
2. Das Token unten in das Textfeld einfügen (gilt wenige Minuten; neues: ./k3-test.sh token $n).
3. "Abo anlegen" -> erwartet "Abo gespeichert". Dann "Test-Push senden" -> Benachrichtigung innerhalb von 10 s.
4. Dasselbe in Firefox und Chrome. Ergebnis in die Ergebnisseite bei K3 eintragen.

Token (alice):
$(cat /tmp/k3-token.txt)

Tunnel von Port $lp auf Port $web in der VM läuft jetzt (Strg+C beendet ihn).
TXT
exec vagrant ssh -- -N -L "$lp:localhost:$web"
