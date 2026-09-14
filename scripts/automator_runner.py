#!/usr/bin/env python3
"""Serialize Automator runs with a process-managed macOS file lock."""

import fcntl
import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    project_dir = Path(__file__).resolve().parent.parent
    python = project_dir / ".venv" / "bin" / "python"
    log_file = Path(sys.argv[1]) if len(sys.argv) > 1 else project_dir / "automator.log"
    lock_file = Path(os.environ.get("TMPDIR", "/tmp")) / "screenshots-housekeeping-automator.lock"

    # This blocks until the previous Folder Action finishes. The OS releases the
    # lock automatically if this process exits or crashes, so no stale recovery
    # or timeout can race with another invocation.
    with lock_file.open("a") as lock, log_file.open("a", encoding="utf-8") as log:
        fcntl.flock(lock, fcntl.LOCK_EX)
        completed = subprocess.run(
            [str(python), "screenshot_renamer.py", "--auto"],
            cwd=project_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
            pass_fds=(lock.fileno(),),
            check=False,
        )
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
