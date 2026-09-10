#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
export PORT="${PORT:-8790}"
export LISTEN_HOST="${LISTEN_HOST:-127.0.0.1}"
export PUBLIC_BASE="${PUBLIC_BASE:-https://disinfective-unmeditated-rhoda.ngrok-free.dev}"
export DATA_DIR="${DATA_DIR:-$DIR/data}"
mkdir -p "$DATA_DIR"

PROXY_PID=""
cleanup() {
  if [[ -n "${PROXY_PID}" ]]; then
    kill "$PROXY_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Reuse healthy proxy if already listening; otherwise start one.
if curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
  echo "proxy already up on ${LISTEN_HOST}:${PORT}"
else
  # Clear stale listener on this port (orphan from prior failed run).
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
    sleep 0.3
  fi
  python3 "$DIR/server.py" &
  PROXY_PID=$!
  for _ in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
      break
    fi
    sleep 0.2
  done
  if ! curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
    echo "proxy failed to become healthy on ${PORT}" >&2
    exit 1
  fi
fi

CONFIG="${NGROK_CONFIG:-$DIR/ngrok.yml}"
# Pooling is config-only (pooling_enabled in ngrok.yml). No --pooling-enabled flag on ngrok 3.39+.
exec ngrok start oauth --config "$CONFIG" --log=stdout
