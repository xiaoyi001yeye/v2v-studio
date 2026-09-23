#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi

. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Setup complete. Edit .env and set ARK_API_KEY, then run ./start.sh"
