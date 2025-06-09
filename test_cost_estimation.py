#!/usr/bin/env python3
"""Test script to demonstrate cost estimation functionality."""

from pathlib import Path
from cost_calculator import CostCalculator

def test_cost_estimation():
    """Test the cost estimation with sample data."""
    calculator = CostCalculator()
    
    # Simulate some screenshot files
    desktop = Path.home() / "Desktop"
    sample_paths = []
    
    # Look for actual screenshot files on desktop
    for screenshot in desktop.glob("Screenshot*.png"):
        sample_paths.append(screenshot)
        if len(sample_paths) >= 3:  # Just test with a few
            break
    
    if not sample_paths:
        # Create mock paths for demonstration
        sample_paths = [
            Path("Screenshot 2025-01-15 at 14.30.22.png"),
            Path("Screenshot 2025-01-15 at 15.45.33.png"),
            Path("Screenshot 2025-01-15 at 16.20.11.png")
        ]
        print("No actual screenshots found, using mock data for demonstration")
    
    print("Cost Estimation Demo")
    print("=" * 40)
    
    # Get cost estimate
    estimate = calculator.estimate_costs(sample_paths)
    print(estimate)
    
    print("\nSimulating API calls...")
    
    # Simulate some successful API calls
    calculator.track_request(True, "Web browser article reading")
    calculator.track_request(True, "Code editor Python file")
    calculator.track_request(False)  # One failed request
    
    actual_costs = calculator.get_actual_costs()
    print(f"\n{actual_costs}")
    
    print("\nCost Summary:")
    summary = calculator.get_cost_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_cost_estimation() 