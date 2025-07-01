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
        # Run the test file from the tests directory
        test_path = Path(__file__).parent / test_file
        result = subprocess.run([sys.executable, str(test_path)], 
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
        "test_grouping.py",
        "test_regex_fix_documentation.py",
        "test_screen_shot_support.py",
        "test_screen_shot_comprehensive.py",
        "test_safety_refusal_handling.py",
        "test_desktop_path_config.py"
    ]
    
    print("🧪 Running Screenshot Renaming Tool Test Suite")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            if run_test(test_file):
                passed += 1
                print(f"✅ {test_file} PASSED")
            else:
                failed += 1
                print(f"❌ {test_file} FAILED")
        else:
            print(f"⚠️  {test_file} NOT FOUND")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed}/{passed + failed} ({100 * passed // (passed + failed) if passed + failed > 0 else 0}%)")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 