#!/usr/bin/env python3
"""Test script to demonstrate grouped renaming functionality."""

import sys
from pathlib import Path

# Add parent directory to path to import modules  
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_manager import FileManager

def test_grouped_renaming():
    """Test the grouped renaming functionality."""
    fm = FileManager(Path('/Users/omri.a/Desktop'))
    screenshots = fm.scan_screenshots()
    
    # Focus on the 14.30.22 group
    target_timestamp = "2025-01-15 at 14.30.22"
    groups = fm.group_screenshots_by_timestamp(screenshots)
    
    if target_timestamp in groups:
        group = groups[target_timestamp]
        print(f"Testing group: {target_timestamp}")
        print(f"Found {len(group)} files:")
        for s in group:
            print(f"  - {s.original_name}")
        
        # Simulate what the rename would produce
        test_description = "Web browser article"
        print(f"\nWith description '{test_description}', files would become:")
        
        for screenshot in group:
            clean_description = fm._sanitize_filename(test_description)
            base_name = f"Screenshot {screenshot.timestamp_part} - {clean_description}"
            
            if screenshot.number_suffix is not None:
                new_name = f"{base_name} ({screenshot.number_suffix}).png"
            else:
                new_name = f"{base_name}.png"
            
            print(f"  {screenshot.original_name} -> {new_name}")
    else:
        print(f"Target timestamp {target_timestamp} not found")

if __name__ == "__main__":
    test_grouped_renaming() 