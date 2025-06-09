#!/usr/bin/env python3
"""Test documenting support for both Screenshot and Screen Shot patterns."""

import sys
import re
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_comprehensive_patterns():
    """Test comprehensive regex patterns for both Screenshot and Screen Shot."""
    
    # Modern "Screenshot" patterns (current macOS)
    screenshot_pattern = re.compile(r'^Screenshot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2})\.png$')
    numbered_pattern = re.compile(r'^Screenshot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2}) \((\d+)\)\.png$')
    
    # Legacy "Screen Shot" patterns (older macOS)
    legacy_screenshot_pattern = re.compile(r'^Screen Shot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2})\.png$')
    legacy_numbered_pattern = re.compile(r'^Screen Shot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2}) \((\d+)\)\.png$')
    
    # Test files - modern format
    modern_test_files = [
        'Screenshot 2025-06-09 at 9.15.24.png',   # Single digit hour
        'Screenshot 2025-06-09 at 14.30.22.png',  # Double digit hour  
        'Screenshot 2025-06-09 at 9.15.24 (1).png',  # Numbered single digit
        'Screenshot 2025-06-09 at 14.30.22 (2).png', # Numbered double digit
    ]
    
    # Test files - legacy format
    legacy_test_files = [
        'Screen Shot 2022-05-21 at 21.21.27.png',   # Legacy format
        'Screen Shot 2022-05-21 at 9.15.24.png',    # Legacy single digit hour
        'Screen Shot 2022-05-21 at 21.21.27 (1).png', # Legacy numbered
        'Screen Shot 2022-05-21 at 9.15.24 (2).png',  # Legacy numbered single digit
    ]
    
    print("🧪 Testing Comprehensive Screenshot Pattern Support")
    print("=" * 60)
    
    print("\n📱 Modern 'Screenshot' Format Tests:")
    print("-" * 40)
    modern_matches = 0
    for filename in modern_test_files:
        if '(' in filename:
            match = numbered_pattern.match(filename)
            if match:
                timestamp, number = match.groups()
                print(f"✅ {filename}")
                print(f"   Timestamp: {timestamp}, Number: {number}")
                modern_matches += 1
            else:
                print(f"❌ {filename}")
        else:
            match = screenshot_pattern.match(filename)
            if match:
                timestamp = match.group(1)
                print(f"✅ {filename}")
                print(f"   Timestamp: {timestamp}")
                modern_matches += 1
            else:
                print(f"❌ {filename}")
    
    print(f"\n📺 Legacy 'Screen Shot' Format Tests:")
    print("-" * 40)
    legacy_matches = 0
    for filename in legacy_test_files:
        if '(' in filename:
            match = legacy_numbered_pattern.match(filename)
            if match:
                timestamp, number = match.groups()
                print(f"✅ {filename}")
                print(f"   Timestamp: {timestamp}, Number: {number}")
                legacy_matches += 1
            else:
                print(f"❌ {filename}")
        else:
            match = legacy_screenshot_pattern.match(filename)
            if match:
                timestamp = match.group(1)
                print(f"✅ {filename}")
                print(f"   Timestamp: {timestamp}")
                legacy_matches += 1
            else:
                print(f"❌ {filename}")
    
    print(f"\n📊 Results Summary:")
    print("-" * 40)
    print(f"Modern 'Screenshot' patterns: {modern_matches}/{len(modern_test_files)} matches")
    print(f"Legacy 'Screen Shot' patterns: {legacy_matches}/{len(legacy_test_files)} matches")
    total_matches = modern_matches + legacy_matches
    total_files = len(modern_test_files) + len(legacy_test_files)
    print(f"Total comprehensive support: {total_matches}/{total_files} matches")
    
    if total_matches == total_files:
        print("🎉 All patterns working correctly!")
        return True
    else:
        print("⚠️  Some patterns need fixing!")
        return False

if __name__ == "__main__":
    success = test_comprehensive_patterns()
    sys.exit(0 if success else 1) 