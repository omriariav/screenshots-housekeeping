#!/bin/zsh

# Run this file from an Automator Folder Action attached to the Desktop folder.
# It resolves the project directory from its own location, so the repository can
# be installed anywhere without hard-coding a username or checkout path.

set -u

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
PYTHON="$PROJECT_DIR/.venv/bin/python"
LOG_FILE="$PROJECT_DIR/automator.log"

# Folder Actions can fire before macOS has completely written the screenshot.
sleep 2

if [[ ! -x "$PYTHON" ]]; then
    print -r -- "Missing virtual environment: $PYTHON" >> "$LOG_FILE"
    print -r -- "Run: python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt" >> "$LOG_FILE"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1
exec "$PYTHON" scripts/automator_runner.py "$LOG_FILE"
