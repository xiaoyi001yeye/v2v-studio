#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

mkdir -p data outputs logs

if pgrep -f ".venv/bin/python app.py" >/dev/null 2>&1; then
  echo "V2V Studio is already running."
  exit 0
fi

nohup .venv/bin/python app.py > logs/codespaces.log 2>&1 &
echo "V2V Studio is starting on port 7860."
echo "Log: logs/codespaces.log"
