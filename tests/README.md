# Test Suite for Screenshot Renaming Tool

This directory contains tests and utilities for verifying the screenshot renaming tool functionality.

## Test Files

### `test_installation.py`
**Purpose**: Validates the environment setup and dependencies
- Checks Python version compatibility
- Verifies all required packages are installed
- Tests OpenAI API configuration
- Validates desktop directory access

**Usage**: `python3 test_installation.py`

### `test_grouping.py`
**Purpose**: Tests the screenshot grouping functionality
- Scans desktop for screenshot files
- Demonstrates timestamp parsing
- Shows how files are grouped by timestamp
- Validates the sorting logic (non-numbered first, then by number)

**Usage**: `python3 test_grouping.py`

### `test_rename_grouping.py`
**Purpose**: Demonstrates the grouped renaming functionality
- Shows how multiple screenshots with the same timestamp share descriptions
- Simulates the rename output format without actual file operations
- Validates the new naming convention: `Screenshot TIMESTAMP - DESCRIPTION [NUMBER].png`

**Usage**: `python3 test_rename_grouping.py`

### `test_cost_estimation.py`
**Purpose**: Tests cost calculation and estimation features
- Demonstrates cost estimation for screenshot processing
- Shows both individual and grouped cost calculations
- Validates cost tracking functionality

**Usage**: `python3 test_cost_estimation.py`

### `run_tests.py`
**Purpose**: Test runner that executes all tests
- Runs all test files in sequence
- Provides a summary of pass/fail status
- Suitable for CI/CD integration

**Usage**: `python3 run_tests.py`

## Key Features Tested

### Timestamp Grouping
The new functionality groups screenshots by their timestamp, so:
- `Screenshot 2025-01-15 at 14.30.22.png`
- `Screenshot 2025-01-15 at 14.30.22 (1).png` 
- `Screenshot 2025-01-15 at 14.30.22 (2).png`

All get the same AI description but maintain their numbering:
- `Screenshot 2025-01-15 at 14.30.22 - Web browser article.png`
- `Screenshot 2025-01-15 at 14.30.22 - Web browser article (1).png`
- `Screenshot 2025-01-15 at 14.30.22 - Web browser article (2).png`

### Cost Optimization
The grouped processing reduces API costs significantly:
- **Before**: 3 API calls for 3 screenshots = ~$0.03
- **After**: 1 API call for 3 screenshots = ~$0.01

### Benefits
1. **Cost Efficiency**: Fewer API calls for multiple screenshots taken at the same time
2. **Consistency**: All related screenshots get the same descriptive name
3. **Preservation**: Original numbering system (1), (2), (3) is maintained
4. **User Experience**: Logical grouping makes file management easier

## Running the Full Test Suite

To run all tests at once:

```bash
cd /path/to/screenshots-housekeeing
python3 tests/run_tests.py
```

This will execute all tests and provide a comprehensive report of the tool's functionality. 