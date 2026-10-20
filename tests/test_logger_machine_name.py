#!/usr/bin/env python3
"""Tests that each log session records which Mac ran it."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from logger import ActionLogger, get_machine_name


class TestMachineName(unittest.TestCase):
    def test_uses_macos_computer_name(self):
        result = Mock(stdout="Work MacBook\n")
        with patch("logger.subprocess.run", return_value=result):
            self.assertEqual(get_machine_name(), "Work MacBook")

    def test_falls_back_to_hostname_when_scutil_fails(self):
        with patch("logger.subprocess.run", side_effect=subprocess.CalledProcessError(1, "scutil")), \
                patch("logger.platform.node", return_value="personal-mac.local"):
            self.assertEqual(get_machine_name(), "personal-mac.local")

    def test_sessions_from_two_macs_append_to_same_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "screenshot_rename_log.txt"
            for name in ("Work MacBook", "Personal MacBook"):
                with patch("logger.get_machine_name", return_value=name):
                    logger = ActionLogger(log_path, "ollama")
                logger.log_scan_results(0)
                logger.save_log()

            content = log_path.read_text(encoding="utf-8")
            self.assertIn("Machine: Work MacBook", content)
            self.assertIn("Machine: Personal MacBook", content)
            self.assertLess(content.index("Work MacBook"), content.index("Personal MacBook"))


if __name__ == "__main__":
    unittest.main()
