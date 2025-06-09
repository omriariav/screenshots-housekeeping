# Screenshot Renaming Tool

An intelligent Python script that automatically renames Mac screenshot files by adding meaningful descriptions using AI vision analysis. Transform cluttered desktop screenshots from generic timestamps into descriptive, searchable filenames.

## Features

- **AI-Powered Analysis**: Uses OpenAI's GPT-4 Vision to analyze screenshot content
- **Smart Descriptions**: Generates concise 4-5 word descriptions of screenshot content  
- **Timestamp Preservation**: Keeps original timestamps for chronological reference
- **Batch Processing**: Handles multiple screenshots efficiently with rate limiting
- **Comprehensive Logging**: Detailed logs of all operations and errors
- **Safe Operations**: No data loss - files are renamed, not modified
- **Privacy Focused**: Images are compressed before API transmission

## Example

**Before**: `Screenshot 2025-01-15 at 14.30.22.png`  
**After**: `Web browser article reading 2025-01-15 at 14.30.22.png`

## Requirements

- macOS (tested on Ventura+)
- Python 3.8+
- OpenAI API key with GPT-4 Vision access

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd screenshots-housekeeping
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API key**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Interactive Mode (Recommended)
```bash
python screenshot_renamer.py
```
This mode will:
- Show you how many screenshots were found
- Ask for confirmation before proceeding
- Display progress during processing
- Show a summary when complete

### Automatic Mode
```bash
python screenshot_renamer.py --auto
```
Processes all screenshots without user interaction (useful for automation).

## Configuration Options

Edit your `.env` file to customize behavior:

```bash
# API Configuration
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4-vision-preview  # or other vision-capable model

# Processing Settings
DESCRIPTION_LENGTH=5        # Target number of words in description
BATCH_SIZE=5               # Number of files to process per batch
MAX_RETRIES=3              # API retry attempts per file
API_TIMEOUT=30             # Seconds to wait for API response

# Performance Tuning
MAX_TOKENS=50              # Maximum tokens in API response
```

## Output

### Renamed Files
Screenshots are renamed with the pattern:
```
[Description] [Original Timestamp].png
```

### Log File
A detailed log is saved to `~/Desktop/screenshot_rename_log.txt` containing:
- Processing summary and statistics
- Individual file operations (analysis, rename)
- Error details and troubleshooting information
- Performance metrics

### Console Output
Real-time feedback showing:
- Files found and processing progress
- Success/failure for each operation
- Final summary with statistics

## Privacy & Security

**Data Handling:**
- Images are resized and compressed before API transmission
- Only visual content is sent to OpenAI - no metadata or file paths
- API requests use secure HTTPS connections
- No data is stored by the application

**API Usage:**
- Implements rate limiting and retry logic
- Respects OpenAI's usage policies
- Minimal data transmission through image compression

## Error Handling

The tool gracefully handles common issues:
- **API Failures**: Retries with exponential backoff
- **File Permission Issues**: Skips inaccessible files with logging
- **Invalid Images**: Continues processing remaining files
- **Network Timeouts**: Implements robust retry logic
- **Filename Conflicts**: Adds incremental suffixes

## Troubleshooting

**"No screenshot files found"**
- Ensure screenshots follow standard macOS naming: `Screenshot YYYY-MM-DD at HH.MM.SS.png`
- Check that files are located on the desktop

**"API key not found"**
- Verify `.env` file exists and contains `OPENAI_API_KEY=your_key`
- Ensure the API key is valid and has GPT-4 Vision access

**"Permission denied"**
- Check file permissions on desktop directory
- Ensure no files are currently open in other applications

**Poor description quality**
- Adjust `DESCRIPTION_LENGTH` in `.env` for longer/shorter descriptions
- Screenshots with complex or unclear content may get generic descriptions

## Architecture

The application uses a modular design:

- **`config.py`**: Configuration management and environment validation
- **`file_manager.py`**: File system operations and screenshot detection
- **`vision_analyzer.py`**: OpenAI API integration and image analysis
- **`logger.py`**: Logging, progress tracking, and reporting
- **`screenshot_renamer.py`**: Main application controller

## Contributing

This tool was developed as a productivity enhancement for macOS users with cluttered screenshot collections. Contributions for additional features, LLM providers, or platform support are welcome.

## License

See LICENSE file for details.

---

**Note**: This tool requires an active OpenAI API subscription. API costs are typically minimal for personal use (estimated $0.01-0.05 per screenshot depending on image size and complexity). 