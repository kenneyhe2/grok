#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
export PORT="${PORT:-8790}"
export LISTEN_HOST="${LISTEN_HOST:-127.0.0.1}"
export PUBLIC_BASE="${PUBLIC_BASE:-https://disinfective-unmeditated-rhoda.ngrok-free.dev}"
export DATA_DIR="${DATA_DIR:-$DIR/data}"
mkdir -p "$DATA_DIR"

python3 "$DIR/server.py" &
PROXY_PID=$!
cleanup() { kill "$PROXY_PID" 2>/dev/null || true; }
trap cleanup EXIT

# Wait for local proxy
for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

CONFIG="${NGROK_CONFIG:-$DIR/ngrok.yml}"
exec ngrok start oauth --config "$CONFIG" --log=stdout
