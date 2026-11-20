#!/usr/bin/env bash
# One command for the KaamSetu prototype: API on 8421, web on 4317.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt

if [[ "${1:-}" == "test" ]]; then
  .venv/bin/pytest -q
  exit 0
fi

if [[ ! -f data/kaamsetu.sqlite || "${1:-}" == "--reset" ]]; then
  .venv/bin/python -m app.seed --reset
fi

.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${KAAMSETU_PORT:-8421}" &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT

cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm install
fi
echo "KaamSetu web:  http://127.0.0.1:${KAAMSETU_WEB_PORT:-4317}"
echo "KaamSetu API:  http://127.0.0.1:${KAAMSETU_PORT:-8421}/api/health"
npm run dev -- --hostname 0.0.0.0 --port "${KAAMSETU_WEB_PORT:-4317}"
