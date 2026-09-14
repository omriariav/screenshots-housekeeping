#!/bin/zsh

# Run this file from an Automator Folder Action attached to the Desktop folder.
# It resolves the project directory from its own location, so the repository can
# be installed anywhere without hard-coding a username or checkout path.

set -u

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
PYTHON="$PROJECT_DIR/.venv/bin/python"
LOG_FILE="$PROJECT_DIR/automator.log"
LOCK_DIR="${TMPDIR:-/tmp}/screenshots-housekeeping-automator.lock"

# Folder Actions can fire before macOS has completely written the screenshot.
sleep 2

# Several screenshots may arrive together; one scan will process all of them.
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT INT TERM

if [[ ! -x "$PYTHON" ]]; then
    print -r -- "Missing virtual environment: $PYTHON" >> "$LOG_FILE"
    print -r -- "Run: python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt" >> "$LOG_FILE"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1
"$PYTHON" screenshot_renamer.py --auto >> "$LOG_FILE" 2>&1
