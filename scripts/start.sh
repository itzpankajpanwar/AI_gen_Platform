#!/usr/bin/env bash
# Start the whole platform locally: API + UI.
#
#   ./scripts/start.sh
#
# Ctrl-C stops both. `caffeinate` keeps the machine awake so a long batch
# is not interrupted by the lid closing or the display sleeping.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${API_PORT:-8200}"
UI_PORT="${UI_PORT:-3200}"

if [ ! -x "$ROOT/backend/.venv/bin/python" ]; then
  echo "Backend venv missing. Run:"
  echo "  cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "Frontend deps missing. Run:  cd frontend && npm install"
  exit 1
fi

cleanup() {
  echo ""
  echo "Stopping…"
  kill 0 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "API  → http://localhost:$API_PORT"
echo "UI   → http://localhost:$UI_PORT"
echo ""

cd "$ROOT/backend"
caffeinate -i .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "$API_PORT" &

cd "$ROOT/frontend"
npm run dev -- --port "$UI_PORT" &

wait
