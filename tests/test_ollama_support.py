"""Focused tests for the native Ollama provider path."""

import os
import unittest
from unittest.mock import Mock, patch

import requests

from config import APIConfig, ConfigManager
from cost_calculator import CostCalculator
from vision_analyzer import VisionAnalyzer


class TestOllamaConfiguration(unittest.TestCase):
    def test_api_config_preserves_legacy_positional_argument_order(self):
        config = APIConfig("key", "https://example.test/v1", "vision-model")

        self.assertEqual(config.api_key, "key")
        self.assertEqual(config.base_url, "https://example.test/v1")
        self.assertEqual(config.model, "vision-model")
        self.assertEqual(config.provider, "openai")

    def test_ollama_config_needs_no_api_key_and_normalizes_base_url(self):
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://localhost:11434///",
            "OLLAMA_MODEL": "llava:7b",
        }, clear=True):
            config = ConfigManager().get_config().api_config

        self.assertEqual(config.provider, "ollama")
        self.assertIsNone(config.api_key)
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertEqual(config.model, "llava:7b")

    def test_openai_remains_the_default_and_requires_its_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            config = ConfigManager().get_config().api_config

        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.base_url, "https://api.openai.com/v1")


class TestOllamaVisionAnalyzer(unittest.TestCase):
    def setUp(self):
        self.config = APIConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3.2-vision",
            max_tokens=42,
            max_retries=0,
        )
        self.analyzer = VisionAnalyzer(self.config, CostCalculator())

    def test_native_chat_payload_uses_image_array_without_authentication(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"message": {"content": "Project dashboard overview"}}

        with patch.object(self.analyzer.session, "post", return_value=response) as post:
            result = self.analyzer._make_api_request("base64-jpeg")

        self.assertEqual(result, {"message": {"content": "Project dashboard overview"}})
        self.assertNotIn("Authorization", self.analyzer.session.headers)
        url = post.call_args.args[0]
        payload = post.call_args.kwargs["json"]
        self.assertEqual(url, "http://localhost:11434/api/chat")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["messages"][0]["images"], ["base64-jpeg"])
        self.assertEqual(payload["options"]["num_predict"], 42)

    def test_parses_native_ollama_message_content(self):
        description = self.analyzer._parse_description({
            "message": {"content": "This screenshot shows Project dashboard overview"}
        })
        self.assertEqual(description, "Project dashboard overview")

    def test_connection_uses_tags_and_accepts_latest_model_alias(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"models": [{"name": "llama3.2-vision:latest"}]}

        with patch.object(self.analyzer.session, "get", return_value=response) as get:
            success, message = self.analyzer.test_connection()

        self.assertTrue(success)
        self.assertIn("Ollama connection successful", message)
        self.assertEqual(get.call_args.args[0], "http://localhost:11434/api/tags")

    def test_missing_model_gives_pull_instruction(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"models": [{"name": "other-model:latest"}]}

        with patch.object(self.analyzer.session, "get", return_value=response):
            success, message = self.analyzer.test_connection()

        self.assertFalse(success)
        self.assertIn("ollama pull llama3.2-vision", message)

    def test_connection_error_explains_how_to_start_ollama(self):
        message = self.analyzer._analyze_api_error(
            requests.exceptions.ConnectionError("connection refused")
        )

        self.assertIn("local Ollama service", message)
        self.assertIn("ollama serve", message)
        self.assertIn("OLLAMA_BASE_URL", message)

    def test_connection_preserves_non_200_response_diagnostics(self):
        response = Mock()
        response.status_code = 404
        response.json.return_value = {"error": {"message": "model not found"}}

        with patch.object(self.analyzer.session, "get", return_value=response):
            success, message = self.analyzer.test_connection()

        self.assertFalse(success)
        self.assertIn("404", message)
        self.assertIn("ollama pull llama3.2-vision", message)


if __name__ == "__main__":
    unittest.main()
