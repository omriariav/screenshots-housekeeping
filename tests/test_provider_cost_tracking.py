#!/usr/bin/env python3
"""Tests for provider-aware cost and request tracking."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cost_calculator import CostCalculator


class TestProviderCostTracking(unittest.TestCase):
    def test_openai_keeps_existing_price_estimate(self):
        estimate = CostCalculator("openai").estimate_costs([
            Path("first.png"),
            Path("second.png"),
        ])

        self.assertFalse(estimate.is_local)
        self.assertGreater(estimate.total_estimated_cost, 0)
        self.assertEqual(estimate.estimated_image_cost, 0.02)

    def test_ollama_has_no_billed_api_cost(self):
        calculator = CostCalculator("ollama")
        estimate = calculator.estimate_costs([
            Path("first.png"),
            Path("second.png"),
        ])
        calculator.track_request(True, "Web browser article")
        calculator.track_request(False)

        self.assertTrue(estimate.is_local)
        self.assertEqual(estimate.total_estimated_cost, 0.0)
        self.assertEqual(estimate.estimated_image_cost, 0.0)
        self.assertEqual(estimate.estimated_token_cost, 0.0)
        self.assertEqual(calculator.get_actual_costs().estimated_cost, 0.0)
        self.assertEqual(calculator.get_actual_costs().total_requests, 2)

    def test_grouped_ollama_estimate_counts_one_request_per_group(self):
        screenshot = type("Screenshot", (), {"path": Path("first.png")})()
        estimate = CostCalculator("ollama").estimate_costs_grouped({
            "first": [screenshot],
            "second": [screenshot],
        })

        self.assertEqual(estimate.total_images, 2)
        self.assertEqual(estimate.total_estimated_cost, 0.0)


if __name__ == "__main__":
    unittest.main()
