#!/usr/bin/env python3
"""Test runner for screenshot renaming tool tests."""

import sys
import subprocess
from pathlib import Path

def run_test(test_file: str) -> bool:
    """Run a single test file and return success status."""
    print(f"\n{'='*50}")
    print(f"Running: {test_file}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False

def main():
    """Run all tests in the tests directory."""
    tests_dir = Path(__file__).parent
    test_files = [
        "test_installation.py",
        "test_grouping.py", 
        "test_rename_grouping.py",
        "test_cost_estimation.py",
        "test_regex_fix_documentation.py"
    ]
    
    print("Screenshot Renaming Tool - Test Suite")
    print("="*50)
    
    results = {}
    for test_file in test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            results[test_file] = run_test(str(test_path))
        else:
            print(f"Warning: {test_file} not found")
            results[test_file] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_file, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{status:8} {test_file}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 