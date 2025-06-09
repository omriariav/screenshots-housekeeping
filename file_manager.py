"""File management operations for screenshot renaming."""

import os
import re
from pathlib import Path
from typing import List, NamedTuple, Optional, Dict
from dataclasses import dataclass
from collections import defaultdict

class ScreenshotFile(NamedTuple):
    """Represents a screenshot file with its metadata."""
    path: Path
    original_name: str
    timestamp_part: str
    number_suffix: Optional[int] = None

@dataclass
class RenameResult:
    """Result of a file rename operation."""
    success: bool
    original_path: Path
    new_path: Optional[Path] = None
    error_message: Optional[str] = None

class FileManager:
    """Handles file system operations for screenshot management."""
    
    def __init__(self, desktop_path: Path):
        self.desktop_path = desktop_path
        # Modern "Screenshot" patterns (current macOS)
        self.screenshot_pattern = re.compile(r'^Screenshot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2})\.png$')
        self.numbered_pattern = re.compile(r'^Screenshot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2}) \((\d+)\)\.png$')
        
        # Legacy "Screen Shot" patterns (older macOS)
        self.legacy_screenshot_pattern = re.compile(r'^Screen Shot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2})\.png$')
        self.legacy_numbered_pattern = re.compile(r'^Screen Shot (\d{4}-\d{2}-\d{2} at \d{1,2}\.\d{1,2}\.\d{2}) \((\d+)\)\.png$')
    
    def scan_screenshots(self) -> List[ScreenshotFile]:
        """Scan desktop directory for screenshot files."""
        screenshots = []
        
        try:
            # Scan for modern "Screenshot" files
            for file_path in self.desktop_path.glob("Screenshot*.png"):
                if self._is_screenshot_file(file_path.name):
                    screenshot_info = self._parse_screenshot_filename(file_path.name, file_path)
                    if screenshot_info:
                        screenshots.append(screenshot_info)
            
            # Scan for legacy "Screen Shot" files
            for file_path in self.desktop_path.glob("Screen Shot*.png"):
                if self._is_legacy_screenshot_file(file_path.name):
                    screenshot_info = self._parse_screenshot_filename(file_path.name, file_path)
                    if screenshot_info:
                        screenshots.append(screenshot_info)
                        
        except Exception as e:
            print(f"Error scanning screenshots: {e}")
        
        return screenshots
    
    def _parse_screenshot_filename(self, filename: str, file_path: Path) -> Optional[ScreenshotFile]:
        """Parse a screenshot filename to extract timestamp and number suffix."""
        
        # Try modern numbered pattern first
        numbered_match = self.numbered_pattern.match(filename)
        if numbered_match:
            timestamp_part = numbered_match.group(1)
            number_suffix = int(numbered_match.group(2))
            return ScreenshotFile(
                path=file_path,
                original_name=filename,
                timestamp_part=timestamp_part,
                number_suffix=number_suffix
            )
        
        # Try legacy numbered pattern
        legacy_numbered_match = self.legacy_numbered_pattern.match(filename)
        if legacy_numbered_match:
            timestamp_part = legacy_numbered_match.group(1)
            number_suffix = int(legacy_numbered_match.group(2))
            return ScreenshotFile(
                path=file_path,
                original_name=filename,
                timestamp_part=timestamp_part,
                number_suffix=number_suffix
            )
        
        # Try modern regular pattern
        timestamp_match = self.screenshot_pattern.match(filename)
        if timestamp_match:
            timestamp_part = timestamp_match.group(1)
            return ScreenshotFile(
                path=file_path,
                original_name=filename,
                timestamp_part=timestamp_part,
                number_suffix=None
            )
        
        # Try legacy regular pattern
        legacy_timestamp_match = self.legacy_screenshot_pattern.match(filename)
        if legacy_timestamp_match:
            timestamp_part = legacy_timestamp_match.group(1)
            return ScreenshotFile(
                path=file_path,
                original_name=filename,
                timestamp_part=timestamp_part,
                number_suffix=None
            )
        
        return None
    
    def group_screenshots_by_timestamp(self, screenshots: List[ScreenshotFile]) -> Dict[str, List[ScreenshotFile]]:
        """Group screenshots by their timestamp."""
        groups = defaultdict(list)
        for screenshot in screenshots:
            groups[screenshot.timestamp_part].append(screenshot)
        
        # Sort each group: non-numbered first, then by number
        for timestamp, group in groups.items():
            groups[timestamp] = sorted(group, key=lambda s: (s.number_suffix or 0))
        
        return dict(groups)
    
    def rename_screenshot_group(self, screenshots: List[ScreenshotFile], description: str) -> List[RenameResult]:
        """Rename a group of screenshots with the same description."""
        results = []
        
        for screenshot in screenshots:
            try:
                # Sanitize the description
                clean_description = self._sanitize_filename(description)
                
                # Determine the format prefix (Screenshot vs Screen Shot)
                prefix = "Screen Shot" if self._is_legacy_format(screenshot.original_name) else "Screenshot"
                
                # Create new filename format: [prefix] TIMESTAMP - DESCRIPTION [NUMBER].png
                base_name = f"{prefix} {screenshot.timestamp_part} - {clean_description}"
                
                if screenshot.number_suffix is not None:
                    new_name = f"{base_name} ({screenshot.number_suffix}).png"
                else:
                    new_name = f"{base_name}.png"
                
                new_path = screenshot.path.parent / new_name
                
                # Handle conflicts
                final_path = self._resolve_conflicts(new_path)
                
                # Perform the rename
                screenshot.path.rename(final_path)
                
                results.append(RenameResult(
                    success=True,
                    original_path=screenshot.path,
                    new_path=final_path
                ))
                
            except Exception as e:
                results.append(RenameResult(
                    success=False,
                    original_path=screenshot.path,
                    error_message=str(e)
                ))
        
        return results
    
    def rename_file(self, screenshot: ScreenshotFile, description: str) -> RenameResult:
        """Rename a screenshot file with the provided description."""
        try:
            # Sanitize the description
            clean_description = self._sanitize_filename(description)
            
            # Create new filename by appending description to original name
            # Remove .png extension, add description, then add .png back
            original_without_ext = screenshot.original_name[:-4]  # Remove .png
            new_name = f"{original_without_ext} - {clean_description}.png"
            new_path = screenshot.path.parent / new_name
            
            # Handle conflicts
            final_path = self._resolve_conflicts(new_path)
            
            # Perform the rename
            screenshot.path.rename(final_path)
            
            return RenameResult(
                success=True,
                original_path=screenshot.path,
                new_path=final_path
            )
            
        except Exception as e:
            return RenameResult(
                success=False,
                original_path=screenshot.path,
                error_message=str(e)
            )
    
    def _is_screenshot_file(self, filename: str) -> bool:
        """Check if a file matches the modern screenshot naming pattern."""
        return bool(self.screenshot_pattern.match(filename)) or bool(self.numbered_pattern.match(filename))
    
    def _is_legacy_screenshot_file(self, filename: str) -> bool:
        """Check if a file matches the legacy Screen Shot naming pattern."""
        return bool(self.legacy_screenshot_pattern.match(filename)) or bool(self.legacy_numbered_pattern.match(filename))
    
    def _is_legacy_format(self, filename: str) -> bool:
        """Check if a filename uses the legacy 'Screen Shot' format."""
        return filename.startswith("Screen Shot")
    
    def _sanitize_filename(self, description: str) -> str:
        """Sanitize description to create a valid filename."""
        # Remove or replace invalid characters (including dots)
        invalid_chars = '<>:"/\\|?*.'
        for char in invalid_chars:
            description = description.replace(char, '')
        
        # Replace multiple spaces with single space
        description = re.sub(r'\s+', ' ', description)
        
        # Trim and capitalize first letter
        description = description.strip().capitalize()
        
        # Limit length to prevent overly long filenames
        max_length = 50
        if len(description) > max_length:
            description = description[:max_length].rsplit(' ', 1)[0]
        
        return description
    
    def _resolve_conflicts(self, target_path: Path) -> Path:
        """Resolve filename conflicts by adding incremental suffix."""
        if not target_path.exists():
            return target_path
        
        base = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        
        counter = 1
        while True:
            new_name = f"{base} ({counter}){suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def get_file_count(self) -> int:
        """Get the total number of screenshot files on desktop."""
        return len(self.scan_screenshots())
    
    def validate_file_access(self, file_path: Path) -> bool:
        """Validate that a file can be read and renamed."""
        try:
            return (
                file_path.exists() and 
                os.access(file_path, os.R_OK) and 
                os.access(file_path.parent, os.W_OK)
            )
        except Exception:
            return False 