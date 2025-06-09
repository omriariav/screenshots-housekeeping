# Screenshot Renaming Tool

An intelligent Python script that automatically renames Mac screenshot files by adding meaningful descriptions using AI vision analysis. Transform cluttered desktop screenshots from generic timestamps into descriptive, searchable filenames.

## Features

- Uses OpenAI's GPT-4 Vision to analyze screenshot content
- Generates concise 4-5 word descriptions of screenshot content  
- Keeps original timestamps for chronological reference
- Shows estimated costs before processing and tracks actual usage
- Handles multiple screenshots efficiently with rate limiting
- Automatically skips screenshots that trigger AI safety responses (e.g., images with children)

## Example

**Before**: `Screenshot 2025-01-15 at 14.30.22.png`  
**After**: `Screenshot 2025-01-15 at 14.30.22 - Web browser article reading.png`

### Real Results

![Screenshot of renamed files](screenshot.png)

*Example of processed screenshots showing AI-generated descriptions for various content types including marketing analysis, privacy policies, project management, and more.*

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
python3 screenshot_renamer.py
```
This mode will:
- Show you how many screenshots were found
- Display estimated API costs before processing
- Ask for confirmation before proceeding
- Show real-time progress during processing
- Display final summary with actual costs and statistics

### Automatic Mode
```bash
python3 screenshot_renamer.py --auto
```
Processes all screenshots without user interaction (useful for automation). Shows cost estimates and final usage summary.

## Automation Setup

### Setting Up Automatic Screenshot Processing

To automatically process new screenshots as they're created, you can set up macOS Folder Actions using Automator. This will run the script whenever new screenshots appear on your Desktop.

#### Method 1: Automator + Folder Actions (Recommended)

**Step 1: Create the Automator Workflow**

1. **Open Automator** (Applications → Automator)
2. **Choose "Folder Action" template**
3. **Set folder** to "Desktop" (~/Desktop)
4. **Add "Run Shell Script" action** from the Library
5. **Set Shell to `/bin/bash`**
6. **Set "Pass input" to "as arguments"**
7. **Add this script**:
   ```bash
   #!/bin/bash
   # Navigate to project directory and run with virtual environment
   cd /Users/$(whoami)/Code/screenshots-housekeeing
   ./venv-screenshots/bin/python screenshot_renamer.py --auto
   ```
   
   **Note**: If you named your virtual environment differently, update the path accordingly:
   - For `venv`: `./venv/bin/python screenshot_renamer.py --auto`
   - For `env`: `./env/bin/python screenshot_renamer.py --auto`
   - For system Python: `python3 screenshot_renamer.py --auto`
8. **Save as "Screenshot Auto Renamer"**

**Step 2: Enable Folder Actions**

1. **Find Folder Actions Setup**:
   - Press `Cmd + Space` and search "Folder Actions Setup"
   - Or go to Applications → Utilities → Script Editor → File → Open → Navigate to saved workflow

2. **Enable the Action**:
   - Check "Enable Folder Actions" at the top
   - Your Desktop folder should appear with "Screenshot Auto Renamer" attached
   - Ensure the checkbox next to your workflow is ✅ checked

**Step 3: Verify Setup**

1. **Check Folder Actions Setup**:
   ```bash
   # Open Folder Actions Setup to verify
   open -a "Folder Actions Setup"
   ```
   You should see:
   - ✅ "Enable Folder Actions" checked
   - Desktop folder listed
   - "Screenshot Auto Renamer" workflow attached and enabled

2. **Test the Automation**:
   - Take a screenshot (`Cmd + Shift + 4` or `Cmd + Shift + 3`)
   - Wait 1-3 seconds for processing
   - Check if the screenshot was renamed with an AI description

**Step 4: Monitor and Debug**

1. **Check Processing Logs**:
   ```bash
   # View the latest log file
   tail -f ~/Desktop/screenshot_rename_log.txt
   ```

2. **Common Issues & Solutions**:
   - **Nothing happens**: Check if Folder Actions are enabled in Folder Actions Setup
   - **"Python not found"**: Update the script path to use absolute paths
   - **"Module not found"**: Ensure the `cd` command points to your project directory
   - **Permissions error**: Check that Automator has folder access permissions

#### Method 2: LaunchAgent (Advanced)

For more control, you can create a LaunchAgent that monitors the Desktop folder:

1. **Create the plist file**:
   ```bash
   mkdir -p ~/Library/LaunchAgents
   
   cat > ~/Library/LaunchAgents/com.screenshots.renamer.plist << 'EOF'
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.screenshots.renamer</string>
       
       <key>ProgramArguments</key>
       <array>
           <string>/Users/$(whoami)/Code/screenshots-housekeeing/venv-screenshots/bin/python</string>
           <string>/Users/$(whoami)/Code/screenshots-housekeeing/screenshot_renamer.py</string>
           <string>--auto</string>
       </array>
       
       <key>WatchPaths</key>
       <array>
           <string>/Users/$(whoami)/Desktop</string>
       </array>
       
       <key>RunAtLoad</key>
       <true/>
       
       <key>ThrottleInterval</key>
       <integer>30</integer>
   </dict>
   </plist>
   EOF
   ```

2. **Load and start the agent**:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.screenshots.renamer.plist
   launchctl start com.screenshots.renamer
   ```

3. **Verify it's running**:
   ```bash
   launchctl list | grep screenshots
   ```

**Note**: Update the Python path in the plist file if you used a different virtual environment name:
- Replace `venv-screenshots` with your actual virtual environment name
- For system Python, use `/usr/bin/python3` instead

### Verification Checklist

✅ **Folder Actions Setup shows**:
- "Enable Folder Actions" is checked
- Desktop folder is listed
- Your workflow is attached and enabled

✅ **Test screenshot**:
- Take a new screenshot
- Wait 30 seconds
- File should be renamed with AI description

✅ **Check logs**:
- `~/Desktop/screenshot_rename_log.txt` shows recent processing
- No error messages in the log

✅ **Performance**:
- Script runs quickly (under 30 seconds per screenshot)
- No system slowdown or high CPU usage

### Troubleshooting Automation

**Folder Actions not triggering**:
1. Restart Folder Actions: `sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.fseventsd.plist && sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.fseventsd.plist`
2. Re-save your Automator workflow
3. Check Console.app for error messages

**Script errors in automation**:
1. Test manually: `python3 screenshot_renamer.py --auto`
2. Check virtual environment path in the script
3. Verify all file paths are absolute, not relative

**High API costs from automation**:
- The script only processes new screenshots, not existing ones
- Each screenshot typically costs $0.01-0.02
- Check logs for actual usage: `grep "Actual cost" ~/Desktop/screenshot_rename_log.txt`

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
[Original Filename] - [AI Description].png
```
Example: `Screenshot 2025-01-15 at 14.30.22 - Code editor Python file.png`

**Benefits of this format:**
- Preserves chronological sorting by timestamp
- Maintains clear screenshot identification
- Easy to distinguish original vs processed files
- Descriptive context without losing file history

### Log File
A detailed log is saved to `~/Desktop/screenshot_rename_log.txt` containing:
- Processing summary and statistics
- Cost estimates and actual API usage
- Individual file operations (analysis, rename)
- Error details and troubleshooting information
- Performance metrics and timing data

### Console Output
Real-time feedback showing:
- Files found and cost estimates
- Processing progress with batch updates
- Success/failure for each operation
- Final summary with cost breakdown and statistics

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

## Safety & Content Filtering

**AI Safety Filters:**
- GPT-4 Vision has built-in safety filters that may refuse to analyze certain content
- Common refusal cases include images with children, sensitive content, or unclear images
- When AI responds with "I'm sorry, I can't help" or similar refusal messages, the tool automatically skips renaming that file

**Automatic Handling:**
- Files triggering safety filters are left with original names (no harm done)
- Processing continues with remaining files
- Clear logging indicates when files are skipped due to safety filters
- No manual intervention required

**User Control:**
- You can manually rename skipped files later if desired
- The tool never forces processing of content the AI deems inappropriate
- Original files remain completely unchanged

## Cost Information

### Cost Transparency
The tool provides full transparency about API usage costs:

**Pre-Processing Estimate:**
```
💰 Estimated cost: $0.0345 (3 images)
   • Image processing: $0.0300
   • Token generation: $0.0045
   • Average image size: 2.34 MB
```

**Post-Processing Summary:**
```
💳 Actual cost: $0.0318

Cost Information:
-----------------
Estimated cost: $0.0345
Actual cost: $0.0318
Cost per file: $0.0106
```

### Pricing Model (Approximate)
- **Base image analysis**: ~$0.01 per image
- **Token generation**: ~$0.03 per 1,000 output tokens  
- **Average response**: ~15 tokens (4-5 word descriptions)
- **Typical cost**: $0.01-0.02 per screenshot

### Cost Testing
```bash
python3 test_cost_estimation.py
```
Run this to see cost estimation in action with sample data.

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
- **`cost_calculator.py`**: API cost estimation and usage tracking
- **`logger.py`**: Logging, progress tracking, and reporting
- **`screenshot_renamer.py`**: Main application controller

### Testing & Validation
- **`test_installation.py`**: Validates environment setup and dependencies
- **`test_cost_estimation.py`**: Demonstrates cost calculation features

## Contributing

This tool was developed as a productivity enhancement for macOS users with cluttered screenshot collections. Contributions for additional features, LLM providers, or platform support are welcome.

## License

See LICENSE file for details.

---

**Note**: This tool requires an active OpenAI API subscription. The built-in cost tracking helps you monitor usage - typical costs are $0.01-0.02 per screenshot for personal use. The tool shows estimated costs before processing and actual costs after completion. 