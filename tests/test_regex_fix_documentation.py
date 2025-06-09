#!/usr/bin/env python3
"""Test documenting the regex fix for single-digit hours in screenshot detection."""

import sys
import re
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_regex_patterns():
    """Test old vs new regex patterns to show the fix."""
    
    # Old patterns (broken for single-digit hours)
    old_screenshot_pattern = re.compile(r'^Screenshot (\d{4}-\d{2}-\d{2} at \d{2}\.\d{2}\.\d{2})\.png$')
    old_numbered_pattern = re.compile(r'^Screenshot (\d{4}-\d{2}-\d{2} at \d{2}\.\d{2}\.\d{2}) \((\d+)\)\.png$')
    
    # New patterns (works for both single and double-digit hours)  
    new_screenshot_pattern = re.compile(r'^Screenshot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2})\.png$')
    new_numbered_pattern = re.compile(r'^Screenshot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2}) \((\d+)\)\.png$')
    
    test_files = [
        'Screenshot 2025-06-09 at 9.15.24.png',   # Single digit hour
        'Screenshot 2025-06-09 at 14.30.22.png',  # Double digit hour
        'Screenshot 2023-08-02 at 8.07.51.png',   # Single digit hour
        'Screenshot 2025-06-09 at 9.15.24 (1).png'  # Numbered with single digit hour
    ]
    
    print("=== REGEX PATTERN FIX TEST ===")
    print("Issue: macOS creates screenshots with single-digit hours (9 AM)")
    print("Old regex expected exactly 2 digits: \\d{2}")
    print("New regex accepts 1-2 digits: \\d{1,2}")
    print()
    
    fixed_count = 0
    
    for filename in test_files:
        # Test against old patterns
        old_match = old_screenshot_pattern.match(filename) or old_numbered_pattern.match(filename)
        # Test against new patterns  
        new_match = new_screenshot_pattern.match(filename) or new_numbered_pattern.match(filename)
        
        print(f"File: {filename}")
        print(f"  Old regex (\\d{{2}}): {'✅ MATCH' if old_match else '❌ NO MATCH'}")
        print(f"  New regex (\\d{{1,2}}): {'✅ MATCH' if new_match else '❌ NO MATCH'}")
        
        if new_match and not old_match:
            print(f"  🎯 FIXED by new regex!")
            fixed_count += 1
        print()
    
    print(f"Summary: {fixed_count}/{len(test_files)} files fixed by the regex update")
    print("\nResult: Screenshots with single-digit hours are now detected! 📸")

if __name__ == "__main__":
    test_regex_patterns() 