#!/usr/bin/env python3
"""Test script to verify grouped screenshot functionality."""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_manager import FileManager

def test_grouped_scanning():
    """Test the grouped scanning functionality."""
    # Test the grouped scanning functionality
    fm = FileManager(Path('/Users/omri.a/Desktop'))
    screenshots = fm.scan_screenshots()

    print('Found screenshots:')
    for s in screenshots:
        print(f'  {s.original_name} -> timestamp: {s.timestamp_part}, number: {s.number_suffix}')

    print(f'\nGrouped by timestamp:')
    groups = fm.group_screenshots_by_timestamp(screenshots)
    for timestamp, group in groups.items():
        print(f'  {timestamp}: {len(group)} files')
        for s in group:
            print(f'    - {s.original_name}')

if __name__ == "__main__":
    test_grouped_scanning() 