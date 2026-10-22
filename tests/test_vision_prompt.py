#!/usr/bin/env python3
"""Tests for the screenshot naming prompt and cleanup of the model's reply."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import APIConfig
from cost_calculator import CostCalculator
from vision_analyzer import VisionAnalyzer


def make_analyzer(description_length=5):
    config = APIConfig(provider="ollama", base_url="http://localhost:11434",
                       model="qwen2.5vl:7b", max_retries=0)
    return VisionAnalyzer(config, CostCalculator(), description_length)


def reply(text):
    return {"message": {"content": text}}


class TestPrompt(unittest.TestCase):
    def test_prompt_uses_configured_word_limit(self):
        self.assertIn("at most 3 words", make_analyzer(3)._build_prompt())
        self.assertIn("at most 7 words", make_analyzer(7)._build_prompt())

    def test_default_word_limit_is_five(self):
        config = APIConfig(provider="ollama", base_url="http://localhost:11434", model="m")
        self.assertIn("at most 5 words", VisionAnalyzer(config, CostCalculator())._build_prompt())

    def test_request_sends_built_prompt(self):
        analyzer = make_analyzer(4)
        response = Mock()
        response.json.return_value = reply("x")
        with patch.object(analyzer.session, "post", return_value=response) as post:
            analyzer._make_api_request("img")
        sent = post.call_args.kwargs["json"]["messages"][0]["content"]
        self.assertEqual(sent, analyzer._build_prompt())


class TestReplyCleanup(unittest.TestCase):
    def test_strips_quote_followed_by_period(self):
        # qwen2.5vl returned exactly this; the old cleanup left a stray quote.
        self.assertEqual(
            make_analyzer()._parse_description(reply("Computer repair service advertisement'.")),
            "Computer repair service advertisement",
        )

    def test_strips_wrapping_quotes_and_trailing_punctuation(self):
        self.assertEqual(make_analyzer()._parse_description(reply('"Slack user token scopes."')),
                         "Slack user token scopes")

    def test_truncates_to_configured_word_limit(self):
        self.assertEqual(make_analyzer(3)._parse_description(reply("one two three four five")),
                         "one two three")

    def test_keeps_reply_within_limit(self):
        self.assertEqual(make_analyzer(5)._parse_description(reply("Snowflake role selection")),
                         "Snowflake role selection")

    def test_punctuation_only_reply_falls_back(self):
        self.assertEqual(make_analyzer()._parse_description(reply("'.")), "Screenshot content")


if __name__ == "__main__":
    unittest.main()
