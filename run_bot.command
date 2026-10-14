#!/bin/bash
# Double-click in Finder (or run in a terminal) to start the bot overlay.
# Extra options: ./run_bot.command --help
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || ./setup.sh
exec .venv/bin/python -m tetrisbot "$@"
