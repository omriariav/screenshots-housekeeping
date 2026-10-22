#!/usr/bin/env python3
"""Tests that sanitized descriptions keep brand-name capitalization."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from file_manager import FileManager


class TestFilenameCasing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fm = FileManager(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def clean(self, text):
        return self.fm._sanitize_filename(text)

    def test_keeps_brand_and_acronym_casing(self):
        self.assertEqual(self.clean("GitHub PR review comments"), "GitHub PR review comments")
        self.assertEqual(self.clean("Slack API token scopes"), "Slack API token scopes")
        self.assertEqual(self.clean("SonicWall device health check"), "SonicWall device health check")

    def test_capitalizes_lowercase_first_letter(self):
        self.assertEqual(self.clean("calendar yoga class"), "Calendar yoga class")

    def test_leaves_inner_capital_first_word_alone(self):
        self.assertEqual(self.clean("iPhone battery settings"), "iPhone battery settings")
        self.assertEqual(self.clean("macOS update notice"), "macOS update notice")

    def test_still_removes_invalid_characters_and_extra_spaces(self):
        self.assertEqual(self.clean('  ApiError:  "TrustScore" too low.  '), "ApiError TrustScore too low")

    def test_empty_description_stays_empty(self):
        self.assertEqual(self.clean("   "), "")


if __name__ == "__main__":
    unittest.main()
