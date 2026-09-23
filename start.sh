#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  echo "Virtual environment not found. Run ./setup.sh first."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env. Set ARK_API_KEY before starting."
  exit 1
fi

exec .venv/bin/python app.py
