# Product Requirements Document: Screenshot Renaming Script

## 1. Overview
### 1.1 Purpose
To create a Python script that automatically renames screenshot files on a Mac desktop by adding a concise, meaningful description (4-5 words) to the existing timestamp, improving file organization and context recall.

### 1.2 Problem Statement
Users take frequent screenshots on their Mac, which are automatically named with timestamps (e.g., "Screenshot 2025-06-09 at 09.24.15.png"). Over time, the desktop becomes cluttered with dozens of screenshots, and users cannot easily recall the context of each file based on the timestamp alone.

### 1.3 Goals
- Automate the process of analyzing and renaming screenshot files.
- Generate concise, meaningful descriptions (4-5 words) for each screenshot using an LLM.
- Retain the original timestamp in the filename for chronological reference.
- Improve desktop organization and screenshot context identification.

## 2. Requirements
### 2.1 Functional Requirements
- **Screenshot Detection**:
  - Identify all screenshot files on the Mac desktop (files starting with "Screenshot" and ending with ".png").
  - Support common screenshot formats (e.g., PNG).
- **Image Analysis**:
  - Use an LLM with vision capabilities (e.g., a model accessible via an API) to analyze the content of each screenshot.
  - Generate a 4-5 word description summarizing the screenshot’s content (e.g., "Web browser with article").
- **File Renaming**:
  - Rename each screenshot by combining the generated description with the original timestamp (e.g., "Web browser with article 2025-06-09 at 09.24.15.png").
  - Ensure filenames are valid and do not exceed system limits or include illegal characters.
- **Execution**:
  - Script runs manually via command line or a simple GUI trigger.
  - Process all screenshots in a single run, with error handling for failed analyses or renames.
- **Output**:
  - Log all renaming actions (e.g., original name, new name) to a text file for user review.
  - Notify user of completion and any errors (e.g., via console or GUI).

### 2.2 Non-Functional Requirements
- **Performance**:
  - Process up to 100 screenshots in under 5 minutes, assuming reasonable LLM API response times.
- **Reliability**:
  - Handle errors gracefully (e.g., LLM API failures, invalid images, or permission issues).
  - Avoid overwriting existing files or creating duplicate filenames.
- **Compatibility**:
  - Compatible with macOS (tested on macOS Ventura or later).
  - Use Python 3.8+ for broad compatibility.
- **Security**:
  - Use secure API calls for LLM processing.
  - Do not modify or delete original screenshot files without renaming success.
- **Usability**:
  - Simple setup with minimal dependencies.
  - Clear logging and error messages for non-technical users.

## 3. Scope
### 3.1 In-Scope
- Scanning the desktop directory for screenshot files.
- Using an LLM to generate descriptions.
- Renaming files with description and timestamp.
- Logging actions and errors.
- Basic command-line interface for execution.

### 3.2 Out-of-Scope
- Real-time screenshot monitoring or automatic renaming on capture.
- Advanced GUI for configuration or preview.
- Support for non-PNG screenshot formats (e.g., JPEG).
- Integration with cloud storage or other directories beyond the desktop.
- Modifying screenshot metadata or content.

## 4. User Stories
- As a Mac user, I want my screenshots to be renamed with a short description so I can quickly understand their content without opening them.
- As a user with many screenshots, I want a script to process all desktop screenshots at once so I can organize my desktop efficiently.
- As a non-technical user, I want clear instructions and logs to confirm what was renamed and identify any issues.

## 5. Technical Specifications
- **Language**: Python 3.8+
- **Dependencies**:
  - `os` and `pathlib` for file handling.
  - `PIL` (Pillow) for image processing.
  - LLM API (e.g., xAI’s Grok API with vision capabilities or similar) for content analysis.
  - `requests` for API calls.
- **Execution Flow**:
  1. Scan `~/Desktop` for files matching "Screenshot*.png".
  2. For each screenshot:
     - Read the image file.
     - Send to LLM API to generate a 4-5 word description.
     - Combine description with original timestamp for new filename.
     - Rename the file.
     - Log the action (original name, new name, status).
  3. Handle errors (e.g., API timeout, invalid image) and continue processing.
  4. Save log to `~/Desktop/screenshot_rename_log.txt`.
- **Error Handling**:
  - Skip files that fail LLM analysis or renaming.
  - Log errors with details (e.g., file name, error message).
- **Sample Filename**:
  - Original: `Screenshot 2025-06-09 at 09.24.15.png`
  - New: `Web browser with article 2025-06-09 at 09.24.15.png`

## 6. Assumptions
- Users have Python installed on their Mac.
- Users have access to an LLM API with vision capabilities (e.g., xAI’s API; see https://x.ai/api for details).
- Screenshots follow the default macOS naming convention ("Screenshot [date] at [time].png").
- Desktop directory is accessible and writable.

## 7. Risks and Mitigations
- **Risk**: LLM API rate limits or downtime.
  - **Mitigation**: Implement retry logic and user notification for API failures.
- **Risk**: Filename conflicts or invalid characters.
  - **Mitigation**: Sanitize descriptions to remove special characters and check for existing files before renaming.
- **Risk**: Slow performance with many screenshots.
  - **Mitigation**: Optimize API calls (e.g., batch processing if supported) and provide progress feedback.
- **Risk**: Incorrect or vague descriptions from LLM.
  - **Mitigation**: Allow user to review logs and manually adjust names if needed.

## 8. Milestones
- **Phase 1**: Develop core script (file scanning, LLM integration, renaming, logging) – 1 week.
- **Phase 2**: Test with sample screenshots and refine LLM prompts for accurate descriptions – 1 week.
- **Phase 3**: Add error handling and user feedback (logs, console output) – 3 days.
- **Phase 4**: User testing and documentation – 2 days.

## 9. Success Criteria
- Script successfully renames at least 95% of screenshots with accurate, concise descriptions.
- No data loss (original screenshots remain intact if renaming fails).
- Log file is clear and lists all actions and errors.
- User can run the script with minimal setup (e.g., install dependencies, provide API key).

## 10. Future Enhancements
- Add a GUI for easier execution and configuration.
- Support scheduling to run the script periodically.
- Allow users to customize description length or target directories.
- Integrate with macOS notifications for completion alerts.