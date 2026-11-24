#!/usr/bin/env bash
# V-4: Startet/stoppt die Spike-Umgebung für EINEN Kandidaten.
#   ./stack.sh up   <name> <port-offset> <image>   z. B. ./stack.sh up typescript 0 chronos-spike-typescript
#   ./stack.sh down <name> <port-offset>
#   ./stack.sh env  <name> <port-offset>           gibt Exportzeilen für die Abnahmesuite aus
#   ./stack.sh restart-app <name> <port-offset> <image>   nur web/worker neu erstellen (nach neuem Image)
# Portversätze für parallele Kandidaten: typescript 0, go 1000, rust 2000.
# Zugangsdaten entstehen in ../../.stack/<name>/ (nicht im Repository, Modus 600). Der Anthropic-Schlüssel wird
# nur aus der aufrufenden Umgebung (ANTHROPIC_API_KEY) übernommen und nie ins Repository geschrieben.
set -euo pipefail
cmd=${1:?up|down|env|restart-app}; name=${2:?Name}; off=${3:?Portversatz}; image=${4:-chronos-spike-$name}
here=$(cd "$(dirname "$0")" && pwd)
gen="$here/../../.stack/$name"
mkdir -p "$gen"; chmod 700 "$gen"

p() { echo $(( $1 + off )); }
PORT_WEB=$(p 8080); PORT_WORKER=$(p 8081); PORT_KC=$(p 8180); PORT_KC_MGMT=$(p 9000)
PORT_AI=$(p 8099); PORT_SMTP=$(p 1025); PORT_MAIL_UI=$(p 8025); PORT_MOCK=$(p 8090); PORT_PG=$(p 5432)

if [ ! -f "$gen/secrets.env" ]; then
  oidc=$(head -c 24 /dev/urandom | base64 | tr -d '/+=' )
  if python3 -c "import cryptography" 2>/dev/null; then vapid=$(python3 "$here/gen_vapid.py")
  else vapid=$(docker run --rm -i python:3.13-slim sh -c 'pip install -q cryptography 2>/dev/null && python -' < "$here/gen_vapid.py"); fi
  umask 077; { echo "OIDC_CLIENT_SECRET=$oidc"; echo "$vapid"; } > "$gen/secrets.env"
fi
set -a; . "$gen/secrets.env"; set +a
# V-6: KI-Schlüssel aus der Umgebung oder aus ~/.config/chronos-spike/anthropic.env (nie im Repository)
if [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -f "$HOME/.config/chronos-spike/anthropic.env" ]; then
  set -a; . "$HOME/.config/chronos-spike/anthropic.env"; set +a
fi

render() {
  umask 077
  sed "s/__OIDC_CLIENT_SECRET__/$OIDC_CLIENT_SECRET/" "$here/realm.template.json" > "$gen/realm.json"
  chmod 644 "$gen/realm.json"   # rootless Docker: der Keycloak-Benutzer im Container braucht Leserecht (Verzeichnis bleibt 700)
  cat > "$gen/compose.env" <<EOT
COMPOSE_PROJECT_NAME=chronos-spike-$name
GEN_DIR=$gen
SPIKE_IMAGE=$image
PORT_PG=$PORT_PG
PORT_KC=$PORT_KC
PORT_KC_MGMT=$PORT_KC_MGMT
PORT_SMTP=$PORT_SMTP
PORT_MAIL_UI=$PORT_MAIL_UI
PORT_MOCK=$PORT_MOCK
EOT
  cat > "$gen/guard.env" <<EOT
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
ANTHROPIC_MODEL=${ANTHROPIC_MODEL:-claude-haiku-5-5}
AI_GUARD_PORT=$PORT_AI
EOT
  cat > "$gen/app.env" <<EOT
DATABASE_URL=postgres://chronos:chronos@localhost:$PORT_PG/chronos
PORT=$PORT_WEB
WORKER_HEALTH_PORT=$PORT_WORKER
OIDC_ISSUER_URL=http://localhost:$PORT_KC/realms/chronos-spike
OIDC_CLIENT_ID=chronos-spike-web
OIDC_CLIENT_SECRET=$OIDC_CLIENT_SECRET
OIDC_REDIRECT_URL=http://localhost:$PORT_WEB/auth/callback
SMTP_HOST=localhost
SMTP_PORT=$PORT_SMTP
VAPID_PUBLIC_KEY=$VAPID_PUBLIC_KEY
VAPID_PRIVATE_KEY=$VAPID_PRIVATE_KEY
VAPID_SUBJECT=mailto:spike@example.test
MOCK_CHANNEL_URL=http://localhost:$PORT_MOCK
# Die Anwendungen kennen den echten Schlüssel nie: Sie sprechen mit dem Schutz-Proxy (ai-guard), der ihn hält und Grenzen erzwingt.
ANTHROPIC_BASE_URL=http://localhost:$PORT_AI
ANTHROPIC_API_KEY=guarded-by-proxy
ANTHROPIC_MODEL=${ANTHROPIC_MODEL:-claude-haiku-5-5}
AI_PRICE_IN_MICRO_EUR_PER_MTOK=1000000
AI_PRICE_OUT_MICRO_EUR_PER_MTOK=5000000
EMAIL_PRICE_MICRO_EUR=1000
RETRY_BASE_MS=200
STATIC_DIR=/static
SPIKE_FAULTS=1
LOG_FORMAT=json
EOT
}
dc() { docker compose --env-file "$gen/compose.env" -f "$here/compose.yaml" "$@"; }

case "$cmd" in
  up)          render; (cd "$here" && dc up -d --wait) ;;
  restart-app) render; (cd "$here" && dc up -d --force-recreate --no-deps web worker) ;;
  down)        render; (cd "$here" && dc down -v --remove-orphans) ;;
  env)         cat <<EOT
export BASE_URL=http://localhost:$PORT_WEB WORKER_HEALTH_URL=http://localhost:$PORT_WORKER
export KEYCLOAK_URL=http://localhost:$PORT_KC MAILPIT_URL=http://localhost:$PORT_MAIL_UI MOCK_URL=http://localhost:$PORT_MOCK
export COMPOSE="docker compose --env-file $gen/compose.env -f $here/compose.yaml"
export AI_GUARD_URL=http://localhost:$PORT_AI PG_CONTAINER=chronos-spike-$name-postgres-1 PORT_PG=$PORT_PG SPIKE_NAME=$name
EOT
  ;;
  *) echo "unbekannter Befehl $cmd" >&2; exit 2 ;;
esac
