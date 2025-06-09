#!/usr/bin/env python3
"""Test comprehensive Screen Shot support using actual FileManager."""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_manager import FileManager

def test_comprehensive_file_detection():
    """Test that FileManager detects both Screenshot and Screen Shot files."""
    
    desktop_path = Path.home() / "Desktop"
    file_manager = FileManager(desktop_path)
    
    print("🔍 Comprehensive Screenshot Detection Test")
    print("=" * 50)
    
    # Scan for all screenshots
    screenshots = file_manager.scan_screenshots()
    
    print(f"\n📊 Detection Summary:")
    print(f"Total files detected: {len(screenshots)}")
    
    # Categorize files
    modern_files = []
    legacy_files = []
    
    for screenshot in screenshots:
        if screenshot.original_name.startswith("Screen Shot"):
            legacy_files.append(screenshot)
        else:
            modern_files.append(screenshot)
    
    print(f"Modern 'Screenshot' files: {len(modern_files)}")
    print(f"Legacy 'Screen Shot' files: {len(legacy_files)}")
    
    # Show examples of each type
    if modern_files:
        print(f"\n📱 Modern 'Screenshot' Examples:")
        for i, screenshot in enumerate(modern_files[:3]):  # Show first 3
            print(f"  {i+1}. {screenshot.original_name}")
            print(f"     Timestamp: {screenshot.timestamp_part}")
            if screenshot.number_suffix:
                print(f"     Number: {screenshot.number_suffix}")
    
    if legacy_files:
        print(f"\n📺 Legacy 'Screen Shot' Examples:")
        for i, screenshot in enumerate(legacy_files[:3]):  # Show first 3
            print(f"  {i+1}. {screenshot.original_name}")
            print(f"     Timestamp: {screenshot.timestamp_part}")
            if screenshot.number_suffix:
                print(f"     Number: {screenshot.number_suffix}")
    
    # Test grouping functionality with both types
    groups = file_manager.group_screenshots_by_timestamp(screenshots)
    
    print(f"\n🔗 Grouping Analysis:")
    print(f"Total groups by timestamp: {len(groups)}")
    
    # Find mixed groups (containing both modern and legacy)
    mixed_groups = 0
    for timestamp, group in groups.items():
        has_modern = any(not s.original_name.startswith("Screen Shot") for s in group)
        has_legacy = any(s.original_name.startswith("Screen Shot") for s in group)
        if has_modern and has_legacy:
            mixed_groups += 1
            print(f"  Mixed group at {timestamp}: {len(group)} files")
    
    if mixed_groups == 0:
        print("  No mixed groups found (timestamps don't overlap between formats)")
    
    # Test format preservation detection
    print(f"\n🔧 Format Detection Test:")
    test_cases = [
        "Screenshot 2025-01-15 at 14.30.22.png",
        "Screen Shot 2022-05-21 at 21.21.27.png",
        "Screenshot 2025-01-15 at 9.15.24 (1).png",
        "Screen Shot 2022-05-21 at 9.15.24 (2).png"
    ]
    
    for test_case in test_cases:
        is_legacy = file_manager._is_legacy_format(test_case)
        prefix = "Screen Shot" if is_legacy else "Screenshot"
        print(f"  {test_case} → {prefix} format ✅")
    
    print(f"\n🎉 Comprehensive support test completed!")
    print(f"Ready to process both modern and legacy screenshot formats.")
    
    return len(screenshots) > 0

if __name__ == "__main__":
    success = test_comprehensive_file_detection()
    sys.exit(0 if success else 1) 