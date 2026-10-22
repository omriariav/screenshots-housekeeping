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

    def test_one_word_over_limit_is_kept(self):
        # Same slack as before the prompt change: 6 words pass at the default of 5.
        self.assertEqual(make_analyzer(5)._parse_description(reply("one two three four five six")),
                         "one two three four five six")

    def test_truncation_drops_trailing_punctuation(self):
        self.assertEqual(make_analyzer(2)._parse_description(reply("Slack, GitHub, and Jira, Linear")),
                         "Slack, GitHub")

    def test_prefix_removed_before_quotes_and_punctuation(self):
        analyzer = make_analyzer()
        self.assertEqual(analyzer._parse_description(reply('Screenshot of "Snowflake role selection".')),
                         "Snowflake role selection")
        self.assertEqual(analyzer._parse_description(reply("This image shows: Zoom yoga class")),
                         "Zoom yoga class")

    def test_refusals_still_detected(self):
        analyzer = make_analyzer()
        self.assertIsNone(analyzer._parse_description(reply("I'm sorry, I can't help with that.")))
        self.assertIsNone(analyzer._parse_description(reply('"I cannot analyze this image."')))


class TestLimits(unittest.TestCase):
    def test_limit_below_two_is_raised_to_two(self):
        for value in (1, 0, -3):
            self.assertEqual(make_analyzer(value).description_length, 2)

    def test_examples_longer_than_limit_are_left_out(self):
        prompt = make_analyzer(3)._build_prompt()
        self.assertIn("Good: Snowflake role selection", prompt)
        self.assertNotIn("Gmail flight booking confirmation", prompt)
        self.assertIn("Gmail flight booking confirmation", make_analyzer(5)._build_prompt())


class TestOpenAIPayload(unittest.TestCase):
    def test_openai_request_sends_same_prompt_as_text_part(self):
        config = APIConfig(provider="openai", api_key="test-key",
                           base_url="https://api.openai.com/v1", model="gpt-4o", max_retries=0)
        analyzer = VisionAnalyzer(config, CostCalculator(), 4)
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": "x"}}]}
        with patch.object(analyzer.session, "post", return_value=response) as post:
            analyzer._make_api_request("img")
        content = post.call_args.kwargs["json"]["messages"][0]["content"]
        self.assertEqual(content[0], {"type": "text", "text": analyzer._build_prompt()})
        self.assertIn("at most 4 words", content[0]["text"])
        self.assertEqual(content[1]["image_url"]["url"], "data:image/jpeg;base64,img")


if __name__ == "__main__":
    unittest.main()
