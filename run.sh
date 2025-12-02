#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# copy .env.sample to .env if not exists
if [ ! -f .env ]; then
  cp .env.sample .env
  echo "[i] Created .env from sample. Fill your keys before live trading."
fi

python -m src.main
