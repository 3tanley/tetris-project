#!/bin/bash
# One-time setup: creates .venv and installs dependencies.
set -e
cd "$(dirname "$0")"
PY=$(command -v python3.14 || command -v python3)
"$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
echo "Setup done. Start the bot with ./run_bot.command"
