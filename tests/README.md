# Test Documentation

This directory contains comprehensive tests for the screenshot renaming tool.

## Test Files

### Core Functionality Tests

- **`test_installation.py`** - Environment validation test
  - Verifies Python version compatibility
  - Checks required dependencies
  - Validates OpenAI API key configuration
  - Tests file access permissions

- **`test_cost_estimation.py`** - Cost calculation test
  - Demonstrates cost estimation for batch operations
  - Shows API call optimization through grouping
  - Validates cost transparency features

### Grouping and Detection Tests

- **`test_grouping.py`** - Screenshot grouping test
  - Tests timestamp-based grouping functionality
  - Validates detection of numbered screenshots
  - Shows cost savings through shared descriptions

- **`test_rename_grouping.py`** - End-to-end rename test
  - Tests complete grouped renaming workflow
  - Demonstrates actual file operations (dry-run mode)
  - Validates error handling and logging

### Diagnostic Tests

- **`test_regex_fix_documentation.py`** - Regex pattern fix validation
  - Documents the single-digit hour detection fix
  - Compares old vs new regex patterns
  - Demonstrates improved file detection capabilities

## Running Tests

### Individual Tests
```bash
python3 tests/test_installation.py
python3 tests/test_grouping.py
python3 tests/test_rename_grouping.py
python3 tests/test_cost_estimation.py
python3 tests/test_regex_fix_documentation.py
```

### All Tests
```bash
python3 tests/run_tests.py
```

## Test Results Expected

### Installation Test
✅ Python version compatibility
✅ Required dependencies installed
✅ API key configured
✅ File access permissions

### Grouping Test
- Detects all unprocessed screenshots on desktop
- Groups by exact timestamp matching
- Shows cost optimization potential

### Rename Test
- Processes screenshots in groups
- Maintains macOS numbering system
- Applies shared descriptions

### Cost Estimation Test
- Calculates API costs before processing
- Shows grouped vs individual processing savings
- Provides transparent cost breakdown

### Regex Fix Test
- Validates single-digit hour detection
- Shows improvement from 2 to 50+ detected files
- Confirms compatibility with both single and double-digit hours

## Regex Pattern Fix Details

**Issue**: macOS creates screenshots with single-digit hours (e.g., 9.15.24 for 9:15 AM)
**Problem**: Original regex pattern `\d{2}` required exactly 2 digits for hours
**Solution**: Updated regex pattern to `\d{1,2}` to accept 1-2 digits for hours

**Impact**: 
- Before fix: Only screenshots from 10 AM - 12 PM detected
- After fix: All screenshots (1 AM - 12 PM) detected
- Files newly detected: `Screenshot 2025-06-09 at 9.15.24.png` and similar

## Safety Features

All tests operate in safe modes:
- No actual API calls made (unless explicitly testing API)
- File operations use dry-run mode
- Comprehensive error handling
- Detailed logging for troubleshooting 