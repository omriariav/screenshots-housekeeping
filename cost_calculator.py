"""Provider-aware request tracking and cost estimation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass
class CostEstimate:
    """Request estimate for processing screenshots."""

    total_images: int
    estimated_image_cost: float
    estimated_token_cost: float
    total_estimated_cost: float
    avg_image_size_mb: float
    provider: str = "openai"

    @property
    def is_local(self) -> bool:
        """Whether this estimate is for the Ollama provider."""
        return self.provider == "ollama"

    def __str__(self) -> str:
        if self.is_local:
            return (
                "Ollama Model Estimate:\n"
                f"  Model requests: {self.total_images}\n"
                f"  Billed API cost: ${self.total_estimated_cost:.4f}\n"
                f"  Average image size: {self.avg_image_size_mb:.2f} MB"
            )

        per_image = self.estimated_image_cost / self.total_images if self.total_images else 0
        return (
            "Cost Estimate:\n"
            f"  Images: {self.total_images} × ${per_image:.4f} = ${self.estimated_image_cost:.4f}\n"
            f"  Tokens: ~{self.total_images * 50} × $0.00003 = ${self.estimated_token_cost:.4f}\n"
            f"  Total: ${self.total_estimated_cost:.4f}"
        )


@dataclass
class ActualCosts:
    """Tracking of provider requests and billed API cost."""

    successful_requests: int = 0
    failed_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost: float = 0.0
    provider: str = "openai"

    @property
    def is_local(self) -> bool:
        """Whether these counts are for the Ollama provider."""
        return self.provider == "ollama"

    def add_request(self, success: bool, input_tokens: int = 0, output_tokens: int = 0):
        """Add a provider request to usage tracking."""
        if success:
            self.successful_requests += 1
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            if not self.is_local:
                self.estimated_cost += 0.01
                self.estimated_cost += output_tokens * 0.00003
        else:
            self.failed_requests += 1

    @property
    def total_requests(self) -> int:
        return self.successful_requests + self.failed_requests

    def __str__(self) -> str:
        heading = "Ollama Model Usage" if self.is_local else "Actual Usage"
        cost_label = "Billed API cost" if self.is_local else "Estimated cost"
        return (
            f"{heading}:\n"
            f"  Successful requests: {self.successful_requests}\n"
            f"  Failed requests: {self.failed_requests}\n"
            f"  Estimated tokens: ~{self.total_output_tokens or self.successful_requests * 15}\n"
            f"  {cost_label}: ${self.estimated_cost:.4f}"
        )


class CostCalculator:
    """Estimate OpenAI billed cost or track Ollama model requests."""

    COST_PER_IMAGE_BASE = 0.01
    COST_PER_1K_OUTPUT_TOKENS = 0.03
    AVERAGE_TOKENS_PER_RESPONSE = 15

    def __init__(self, provider: str = "openai"):
        self.provider = provider.lower()
        if self.provider not in {"openai", "ollama"}:
            raise ValueError(f"Unsupported model provider: {provider}")
        self.actual_costs = ActualCosts(provider=self.provider)

    @property
    def is_local(self) -> bool:
        """Whether this calculator tracks the Ollama provider."""
        return self.provider == "ollama"

    def _average_image_size(self, screenshot_paths: List[Path]) -> float:
        total_size_mb = 0.0
        valid_images = 0
        for path in screenshot_paths[:5]:
            try:
                total_size_mb += path.stat().st_size / (1024 * 1024)
                valid_images += 1
            except OSError:
                continue
        return total_size_mb / valid_images if valid_images else 1.0

    def _estimate_price(self, request_count: int) -> Tuple[float, float, float]:
        if self.is_local:
            return 0.0, 0.0, 0.0
        image_cost = request_count * self.COST_PER_IMAGE_BASE
        token_cost = (
            request_count * self.AVERAGE_TOKENS_PER_RESPONSE / 1000
        ) * self.COST_PER_1K_OUTPUT_TOKENS
        return image_cost, token_cost, image_cost + token_cost

    def estimate_costs(self, screenshot_paths: List[Path]) -> CostEstimate:
        """Estimate provider requests for a list of screenshots."""
        if not screenshot_paths:
            return CostEstimate(0, 0.0, 0.0, 0.0, 0.0, self.provider)

        request_count = len(screenshot_paths)
        image_cost, token_cost, total_cost = self._estimate_price(request_count)
        return CostEstimate(
            total_images=request_count,
            estimated_image_cost=image_cost,
            estimated_token_cost=token_cost,
            total_estimated_cost=total_cost,
            avg_image_size_mb=self._average_image_size(screenshot_paths),
            provider=self.provider,
        )

    def estimate_costs_grouped(self, screenshots_by_timestamp: dict) -> CostEstimate:
        """Estimate one provider request for each timestamp group."""
        if not screenshots_by_timestamp:
            return CostEstimate(0, 0.0, 0.0, 0.0, 0.0, self.provider)

        representative_paths = [
            group[0].path for group in list(screenshots_by_timestamp.values())[:5] if group
        ]
        request_count = len(screenshots_by_timestamp)
        image_cost, token_cost, total_cost = self._estimate_price(request_count)
        return CostEstimate(
            total_images=request_count,
            estimated_image_cost=image_cost,
            estimated_token_cost=token_cost,
            total_estimated_cost=total_cost,
            avg_image_size_mb=self._average_image_size(representative_paths),
            provider=self.provider,
        )

    def track_request(self, success: bool, response_text: str = ""):
        """Track a model-provider request."""
        estimated_tokens = (
            len(response_text.split()) * 1.3
            if response_text
            else self.AVERAGE_TOKENS_PER_RESPONSE
        )
        self.actual_costs.add_request(success, 0, int(estimated_tokens))

    def get_actual_costs(self) -> ActualCosts:
        """Get actual provider request counts and cost."""
        return self.actual_costs

    def get_cost_summary(self) -> dict:
        """Get provider usage while retaining legacy cost-summary keys."""
        return {
            "successful_requests": self.actual_costs.successful_requests,
            "failed_requests": self.actual_costs.failed_requests,
            "estimated_cost_usd": self.actual_costs.estimated_cost,
            "total_requests": self.actual_costs.total_requests,
        }

    def reset(self):
        """Reset provider usage tracking for a new session."""
        self.actual_costs = ActualCosts(provider=self.provider)
