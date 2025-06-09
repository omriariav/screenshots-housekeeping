"""Cost calculation and tracking for OpenAI API usage."""

import math
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from PIL import Image

@dataclass
class CostEstimate:
    """Cost estimation for processing screenshots."""
    total_images: int
    estimated_image_cost: float
    estimated_token_cost: float
    total_estimated_cost: float
    avg_image_size_mb: float
    
    def __str__(self) -> str:
        return (
            f"Cost Estimate:\n"
            f"  Images: {self.total_images} × ${self.estimated_image_cost/self.total_images:.4f} = ${self.estimated_image_cost:.4f}\n"
            f"  Tokens: ~{self.total_images * 50} × $0.00003 = ${self.estimated_token_cost:.4f}\n"
            f"  Total: ${self.total_estimated_cost:.4f}"
        )

@dataclass
class ActualCosts:
    """Tracking of actual API usage and costs."""
    successful_requests: int = 0
    failed_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost: float = 0.0
    
    def add_request(self, success: bool, input_tokens: int = 0, output_tokens: int = 0):
        """Add a request to the cost tracking."""
        if success:
            self.successful_requests += 1
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            # Estimate cost (OpenAI doesn't provide exact usage in response)
            # GPT-4 Vision: ~$0.01 per image + token costs
            self.estimated_cost += 0.01  # Base image cost
            self.estimated_cost += (output_tokens * 0.00003)  # ~$0.03 per 1K output tokens
        else:
            self.failed_requests += 1
    
    @property
    def total_requests(self) -> int:
        return self.successful_requests + self.failed_requests
    
    def __str__(self) -> str:
        return (
            f"Actual Usage:\n"
            f"  Successful requests: {self.successful_requests}\n"
            f"  Failed requests: {self.failed_requests}\n"
            f"  Estimated tokens: ~{self.total_output_tokens or self.successful_requests * 15}\n"
            f"  Estimated cost: ${self.estimated_cost:.4f}"
        )

class CostCalculator:
    """Calculates and tracks OpenAI API costs for screenshot processing."""
    
    # OpenAI GPT-4 Vision pricing (approximate, as of Jan 2025)
    COST_PER_IMAGE_BASE = 0.01  # Base cost per image
    COST_PER_1K_OUTPUT_TOKENS = 0.03  # Cost per 1K output tokens
    AVERAGE_TOKENS_PER_RESPONSE = 15  # Estimated tokens for 4-5 word responses
    
    def __init__(self):
        self.actual_costs = ActualCosts()
    
    def estimate_costs(self, screenshot_paths: List[Path]) -> CostEstimate:
        """Estimate costs for processing a list of screenshots."""
        if not screenshot_paths:
            return CostEstimate(0, 0.0, 0.0, 0.0, 0.0)
        
        total_images = len(screenshot_paths)
        
        # Calculate average image size (for reference)
        total_size_mb = 0.0
        valid_images = 0
        
        for path in screenshot_paths[:min(5, len(screenshot_paths))]:  # Sample first 5 for estimation
            try:
                size_mb = path.stat().st_size / (1024 * 1024)
                total_size_mb += size_mb
                valid_images += 1
            except Exception:
                continue
        
        avg_image_size_mb = total_size_mb / valid_images if valid_images > 0 else 1.0
        
        # Estimate costs
        estimated_image_cost = total_images * self.COST_PER_IMAGE_BASE
        estimated_tokens = total_images * self.AVERAGE_TOKENS_PER_RESPONSE
        estimated_token_cost = (estimated_tokens / 1000) * self.COST_PER_1K_OUTPUT_TOKENS
        total_estimated_cost = estimated_image_cost + estimated_token_cost
        
        return CostEstimate(
            total_images=total_images,
            estimated_image_cost=estimated_image_cost,
            estimated_token_cost=estimated_token_cost,
            total_estimated_cost=total_estimated_cost,
            avg_image_size_mb=avg_image_size_mb
        )
    
    def estimate_costs_grouped(self, screenshots_by_timestamp: dict) -> CostEstimate:
        """Estimate costs for processing screenshots grouped by timestamp."""
        if not screenshots_by_timestamp:
            return CostEstimate(0, 0.0, 0.0, 0.0, 0.0)
        
        # Count unique timestamps (API calls needed) vs total files
        unique_timestamps = len(screenshots_by_timestamp)
        total_images = sum(len(group) for group in screenshots_by_timestamp.values())
        
        # Calculate average image size from representative files
        total_size_mb = 0.0
        valid_images = 0
        sample_paths = []
        
        for group in list(screenshots_by_timestamp.values())[:5]:  # Sample from first 5 groups
            if group:
                sample_paths.append(group[0].path)  # Use representative file from each group
        
        for path in sample_paths:
            try:
                size_mb = path.stat().st_size / (1024 * 1024)
                total_size_mb += size_mb
                valid_images += 1
            except Exception:
                continue
        
        avg_image_size_mb = total_size_mb / valid_images if valid_images > 0 else 1.0
        
        # Estimate costs based on unique API calls (one per timestamp group)
        estimated_image_cost = unique_timestamps * self.COST_PER_IMAGE_BASE
        estimated_tokens = unique_timestamps * self.AVERAGE_TOKENS_PER_RESPONSE
        estimated_token_cost = (estimated_tokens / 1000) * self.COST_PER_1K_OUTPUT_TOKENS
        total_estimated_cost = estimated_image_cost + estimated_token_cost
        
        return CostEstimate(
            total_images=unique_timestamps,  # Show API calls, not total files
            estimated_image_cost=estimated_image_cost,
            estimated_token_cost=estimated_token_cost,
            total_estimated_cost=total_estimated_cost,
            avg_image_size_mb=avg_image_size_mb
        )
    
    def track_request(self, success: bool, response_text: str = ""):
        """Track an API request for cost calculation."""
        # Estimate tokens in response (rough approximation)
        estimated_tokens = len(response_text.split()) * 1.3 if response_text else self.AVERAGE_TOKENS_PER_RESPONSE
        self.actual_costs.add_request(success, 0, int(estimated_tokens))
    
    def get_actual_costs(self) -> ActualCosts:
        """Get the actual costs incurred during processing."""
        return self.actual_costs
    
    def get_cost_summary(self) -> dict:
        """Get a summary of costs for logging."""
        return {
            'successful_requests': self.actual_costs.successful_requests,
            'failed_requests': self.actual_costs.failed_requests,
            'estimated_cost_usd': self.actual_costs.estimated_cost,
            'total_requests': self.actual_costs.total_requests
        }
    
    def reset(self):
        """Reset cost tracking for a new session."""
        self.actual_costs = ActualCosts() 