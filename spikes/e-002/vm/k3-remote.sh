#!/usr/bin/env bash
# Läuft in der VM als Benutzer agent (aufgerufen von k3-test.sh): startet den Stack eines Kandidaten für den manuellen Web-Push-Test K3.
set -u
n=$1; off=$2
source ~/.cargo/env 2>/dev/null || true
export PATH="$PATH:/usr/local/go/bin:$HOME/go/bin"
cd ~/eval/common/env
./stack.sh down "$n" "$off" >/dev/null 2>&1 || true
image=chronos-spike-$n
if [ "$n" = rust ]; then
  # Eigenes Tag, damit ein laufendes Jiff-Experiment (Image chronos-spike-rust) nicht gestört wird
  image=chronos-spike-rust-orig
  (cd ~/spikes/e-002/rust/rust && docker build -t "$image" . >/tmp/k3-rust-build.log 2>&1) || { echo "Rust-Build fehlgeschlagen (siehe /tmp/k3-rust-build.log in der VM)" >&2; exit 1; }
fi
./stack.sh up "$n" "$off" "$image" >/dev/null 2>&1 || echo "(stack up meldete einen Fehler, prüfe /healthz)" >&2
web=$((8080+off)); kc=$((8180+off))
for i in $(seq 1 60); do curl -sf "http://localhost:$web/healthz" >/dev/null && break; sleep 2; done
curl -sf "http://localhost:$web/healthz" >/dev/null || { echo "Web antwortet nicht auf Port $web" >&2; exit 1; }
echo "STACK_OK web=$web keycloak=$kc"
