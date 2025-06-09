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
  - Tests the complete rename workflow
  - Validates grouped renaming with shared descriptions
  - Demonstrates cost optimization in practice

### Pattern Detection and Compatibility Tests

- **`test_regex_fix_documentation.py`** - Single-digit hour fix test
  - Documents the regex pattern fix for single-digit hours
  - Shows before/after pattern matching improvements
  - Validates detection of `9.15.24` vs `14.30.22` formats

- **`test_screen_shot_support.py`** - Legacy format pattern test
  - Tests regex patterns for both "Screenshot" and "Screen Shot" formats
  - Validates comprehensive pattern matching
  - Shows support for older macOS screenshot naming

- **`test_screen_shot_comprehensive.py`** - Real-world detection test
  - Uses actual FileManager to scan desktop files
  - Tests detection of both modern and legacy formats
  - Validates format preservation in renaming
  - Shows grouping analysis across format types

- **`test_safety_refusal_handling.py`** - AI safety filter test
  - Tests detection of GPT-4 Vision safety refusal responses
  - Validates proper handling of "I can't help" responses
  - Ensures screenshots with children/sensitive content are skipped
  - Tests edge cases and mixed-case refusal patterns

## Pattern Support Coverage

### Modern Format (Current macOS)
```
Screenshot 2025-01-15 at 14.30.22.png
Screenshot 2025-01-15 at 9.15.24.png       # Single-digit hour
Screenshot 2025-01-15 at 14.30.22 (1).png  # Numbered
```

### Legacy Format (Older macOS)
```
Screen Shot 2022-05-21 at 21.21.27.png
Screen Shot 2022-05-21 at 9.15.24.png      # Single-digit hour  
Screen Shot 2022-05-21 at 21.21.27 (1).png # Numbered
```

## Test Runner

Use `run_tests.py` to execute the complete test suite:

```bash
python3 tests/run_tests.py
```

This will run all tests in sequence and provide a comprehensive report.

## Key Features Validated

1. **Comprehensive Format Support** - Both "Screenshot" and "Screen Shot" patterns
2. **Single-digit Hour Detection** - Fixed regex patterns for `9.15.24` format
3. **Grouped Processing** - Multiple files with same timestamp share one AI description
4. **Format Preservation** - Legacy files keep "Screen Shot" prefix after renaming  
5. **Cost Optimization** - Significant API cost reduction through grouping
6. **Safety Filter Handling** - Automatically skips files that trigger AI safety responses
7. **Error Handling** - Graceful degradation with detailed logging 