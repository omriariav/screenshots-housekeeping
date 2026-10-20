#!/usr/bin/env python3
"""Tests for SCREENSHOT_PREFIX, which lets Macs sharing a Desktop rename only their own screenshots."""

import os
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager
from file_manager import FileManager

TIMESTAMP = "2026-10-20 at 9.15.24"


class PrefixTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.desktop = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def touch(self, *names):
        for name in names:
            (self.desktop / name).write_bytes(b"")

    def scanned_names(self, prefix=None):
        return sorted(s.original_name for s in FileManager(self.desktop, prefix).scan_screenshots())


class TestScanning(PrefixTestCase):
    def test_default_prefixes_when_unset(self):
        self.touch(
            f"Screenshot {TIMESTAMP}.png",
            f"Screen Shot {TIMESTAMP} (1).png",
            f"Work Screenshot {TIMESTAMP}.png",
        )
        self.assertEqual(self.scanned_names(), [
            f"Screen Shot {TIMESTAMP} (1).png",
            f"Screenshot {TIMESTAMP}.png",
        ])

    def test_custom_prefix_matches_only_its_own_files(self):
        self.touch(
            f"Work Screenshot {TIMESTAMP}.png",
            f"Work Screenshot {TIMESTAMP} (2).png",
            f"Personal Screenshot {TIMESTAMP}.png",
            f"Screenshot {TIMESTAMP}.png",
            f"Screen Shot {TIMESTAMP}.png",
            f"Work Screenshot {TIMESTAMP} - Already renamed.png",
        )
        self.assertEqual(self.scanned_names("Work Screenshot"), [
            f"Work Screenshot {TIMESTAMP} (2).png",
            f"Work Screenshot {TIMESTAMP}.png",
        ])

    def test_default_prefix_does_not_match_longer_custom_prefix(self):
        self.touch(f"Screenshot Work {TIMESTAMP}.png")
        self.assertEqual(self.scanned_names(), [])
        self.assertEqual(self.scanned_names("Screenshot Work"), [f"Screenshot Work {TIMESTAMP}.png"])

    def test_regex_metacharacters_in_prefix_are_literal(self):
        self.touch(f"Shot (W). {TIMESTAMP}.png", f"Shot (W)x {TIMESTAMP}.png", f"[x] {TIMESTAMP}.png")
        self.assertEqual(self.scanned_names("Shot (W)."), [f"Shot (W). {TIMESTAMP}.png"])
        self.assertEqual(self.scanned_names("[x]"), [f"[x] {TIMESTAMP}.png"])

    def test_decomposed_filename_matches_composed_prefix(self):
        prefix = unicodedata.normalize("NFC", "Écran")
        fm = FileManager(self.desktop, prefix)
        nfd_name = unicodedata.normalize("NFD", f"{prefix} {TIMESTAMP}.png")
        parsed = fm._parse_screenshot_filename(nfd_name, self.desktop / nfd_name)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.timestamp_part, TIMESTAMP)


class TestRenaming(PrefixTestCase):
    def test_rename_keeps_custom_prefix_and_number(self):
        self.touch(f"Work Screenshot {TIMESTAMP}.png", f"Work Screenshot {TIMESTAMP} (1).png")
        fm = FileManager(self.desktop, "Work Screenshot")
        group = fm.group_screenshots_by_timestamp(fm.scan_screenshots())[TIMESTAMP]

        results = fm.rename_screenshot_group(group, "code editor")

        self.assertTrue(all(r.success for r in results))
        self.assertEqual(sorted(r.new_path.name for r in results), [
            f"Work Screenshot {TIMESTAMP} - Code editor (1).png",
            f"Work Screenshot {TIMESTAMP} - Code editor.png",
        ])

    def test_rename_keeps_legacy_prefix(self):
        self.touch(f"Screen Shot {TIMESTAMP}.png")
        fm = FileManager(self.desktop)
        results = fm.rename_screenshot_group(fm.scan_screenshots(), "dashboard")
        self.assertEqual(results[0].new_path.name, f"Screen Shot {TIMESTAMP} - Dashboard.png")

    def test_rename_conflict_keeps_custom_prefix(self):
        self.touch(f"Work Screenshot {TIMESTAMP}.png", f"Work Screenshot {TIMESTAMP} - Dashboard.png")
        fm = FileManager(self.desktop, "Work Screenshot")
        results = fm.rename_screenshot_group(fm.scan_screenshots(), "dashboard")
        self.assertEqual(results[0].new_path.name, f"Work Screenshot {TIMESTAMP} - Dashboard (1).png")


class TestConfig(unittest.TestCase):
    def prefix_from_env(self, value):
        with patch.dict(os.environ, {"SCREENSHOT_PREFIX": value, "LLM_PROVIDER": "ollama"}):
            return ConfigManager().get_config().screenshot_prefix

    def test_reads_and_strips_prefix(self):
        self.assertEqual(self.prefix_from_env("  Work Screenshot "), "Work Screenshot")

    def test_blank_prefix_means_unset(self):
        self.assertIsNone(self.prefix_from_env("   "))

    def test_rejects_path_separators(self):
        for value in ("Work/Screenshot", "Work:Screenshot"):
            with self.assertRaises(ValueError):
                self.prefix_from_env(value)


if __name__ == "__main__":
    unittest.main()
