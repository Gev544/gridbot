#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.sample .env
  echo "[i] Created .env from sample. Edit keys and set DRY_RUN=false to go live."
fi

# Alias to bot entrypoint for convenience
python -m src.bot.main "$@"
