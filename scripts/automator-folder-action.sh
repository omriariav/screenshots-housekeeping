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
LOCK_PID="$LOCK_DIR/pid"

# Folder Actions can fire before macOS has completely written the screenshot.
sleep 2

# Wait for an active run instead of dropping this Folder Action event. Recover
# a lock whose owner no longer exists, such as after a crash or forced shutdown.
attempts=0
until mkdir "$LOCK_DIR" 2>/dev/null; do
    if [[ -r "$LOCK_PID" ]]; then
        owner_pid="$(<"$LOCK_PID")"
        if [[ "$owner_pid" == <-> ]] && ! kill -0 "$owner_pid" 2>/dev/null; then
            rm -f "$LOCK_PID"
            rmdir "$LOCK_DIR" 2>/dev/null
            continue
        fi
    elif (( attempts >= 2 )); then
        # Recover if a process died between creating the directory and PID file.
        rmdir "$LOCK_DIR" 2>/dev/null && continue
    fi

    (( attempts >= 300 )) && exit 1
    sleep 2
    (( attempts++ ))
done

print -r -- "$$" > "$LOCK_PID"
trap 'rm -f "$LOCK_PID"; rmdir "$LOCK_DIR" 2>/dev/null' EXIT INT TERM

if [[ ! -x "$PYTHON" ]]; then
    print -r -- "Missing virtual environment: $PYTHON" >> "$LOG_FILE"
    print -r -- "Run: python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt" >> "$LOG_FILE"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1
"$PYTHON" screenshot_renamer.py --auto >> "$LOG_FILE" 2>&1
