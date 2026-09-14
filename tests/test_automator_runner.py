"""Tests for the serialized macOS Automator runner."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


RUNNER_PATH = Path(__file__).parent.parent / "scripts" / "automator_runner.py"
SPEC = importlib.util.spec_from_file_location("automator_runner", RUNNER_PATH)
automator_runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(automator_runner)


class TestAutomatorRunner(unittest.TestCase):
    def test_takes_blocking_os_lock_before_running_renamer(self):
        completed = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "automator.log"
            with (
                patch.dict(os.environ, {"TMPDIR": temp_dir}),
                patch.object(sys, "argv", [str(RUNNER_PATH), str(log_file)]),
                patch.object(automator_runner.fcntl, "flock") as flock,
                patch.object(automator_runner.subprocess, "run", return_value=completed) as run,
            ):
                result = automator_runner.main()

        self.assertEqual(result, 0)
        flock.assert_called_once()
        self.assertEqual(flock.call_args.args[1], automator_runner.fcntl.LOCK_EX)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][-2:], ["screenshot_renamer.py", "--auto"])
        self.assertEqual(len(run.call_args.kwargs["pass_fds"]), 1)


if __name__ == "__main__":
    unittest.main()
