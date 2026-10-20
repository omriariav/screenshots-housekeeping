#!/usr/bin/env python3
"""Tests that each Mac writes its own log file and each session records which Mac ran it."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager, get_machine_name
from logger import ActionLogger


class TestMachineName(unittest.TestCase):
    def test_uses_macos_computer_name(self):
        result = Mock(stdout="Work MacBook\n")
        with patch("config.subprocess.run", return_value=result):
            self.assertEqual(get_machine_name(), "Work MacBook")

    def test_falls_back_to_hostname_when_scutil_fails(self):
        with patch("config.subprocess.run", side_effect=subprocess.CalledProcessError(1, "scutil")), \
                patch("config.platform.node", return_value="personal-mac.local"):
            self.assertEqual(get_machine_name(), "personal-mac.local")


class TestPerMachineLog(unittest.TestCase):
    def log_path_for(self, machine):
        with patch.dict(os.environ, {"DESKTOP_PATH": "/shared/Desktop"}), \
                patch("config.get_machine_name", return_value=machine):
            return ConfigManager().log_file_path

    def test_each_mac_gets_its_own_log_file(self):
        self.assertEqual(self.log_path_for("Work MacBook"),
                         Path("/shared/Desktop/screenshot_rename_log - Work MacBook.txt"))
        self.assertNotEqual(self.log_path_for("Work MacBook"), self.log_path_for("Personal MacBook"))

    def test_path_separators_in_machine_name_are_replaced(self):
        self.assertEqual(self.log_path_for("Omri's Mac/Work: 2").name,
                         "screenshot_rename_log - Omri's Mac-Work- 2.txt")

    def test_session_header_records_machine(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "screenshot_rename_log - Work MacBook.txt"
            with patch("logger.get_machine_name", return_value="Work MacBook"):
                logger = ActionLogger(log_path, "ollama")
            logger.log_scan_results(0)
            logger.save_log()

            self.assertIn("Machine: Work MacBook", log_path.read_text(encoding="utf-8"))

    def test_machine_name_looked_up_once_for_path_and_config(self):
        with patch("config.get_machine_name", return_value="Work MacBook") as lookup, \
                patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
            manager = ConfigManager()
            config = manager.get_config()
        self.assertEqual(lookup.call_count, 1)
        self.assertEqual(config.machine_name, "Work MacBook")
        self.assertTrue(config.log_file_path.name.endswith("Work MacBook.txt"))


if __name__ == "__main__":
    unittest.main()
