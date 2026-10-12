#!/bin/bash
# Bring-up helper — run AFTER Dograh is up (README step 1).
# Starts the tools server, waits for Dograh, creates the Maya agent.
#
#   DOGRAH_API_KEY=dg_... ./setup.sh
#
# The API key comes from the Dograh dashboard after you create your account.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
: "${DOGRAH_API_KEY:?Set DOGRAH_API_KEY first (Dograh dashboard -> API keys)}"

export DOGRAH_API_URL="${DOGRAH_API_URL:-http://localhost:3010/api/v1}"
export TOOLS_PUBLIC_URL="${TOOLS_PUBLIC_URL:-http://host.docker.internal:8090}"
UI_URL="${DOGRAH_API_URL%/api/v1}/"

echo "==> waiting for Dograh at $UI_URL ..."
for _ in $(seq 1 60); do
  if curl -sf -o /dev/null "$UI_URL"; then break; fi
  sleep 5
done
curl -sf -o /dev/null "$UI_URL" || { echo "Dograh not reachable at $UI_URL"; exit 1; }

echo "==> starting tools server..."
cd "$ROOT"
docker compose up -d --build
curl -sf http://localhost:8090/health > /dev/null \
  && echo "tools OK: http://localhost:8090/health" \
  || { echo "tools server failed to start"; exit 1; }

echo "==> creating Maya agent..."
DOGRAH_API_URL="$DOGRAH_API_URL" DOGRAH_API_KEY="$DOGRAH_API_KEY" \
  TOOLS_PUBLIC_URL="$TOOLS_PUBLIC_URL" python3 agent/create_agent.py
