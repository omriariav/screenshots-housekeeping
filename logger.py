"""Logging and reporting functionality for screenshot renaming operations."""

import datetime
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field

from file_manager import RenameResult
from vision_analyzer import AnalysisResult
from cost_calculator import CostEstimate, ActualCosts

@dataclass
class ProcessingSummary:
    """Summary of the entire processing session."""
    total_files: int = 0
    successful_renames: int = 0
    failed_renames: int = 0
    api_failures: int = 0
    start_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    end_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    errors: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    
    @property
    def duration(self) -> datetime.timedelta:
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.successful_renames / self.total_files) * 100

class ActionLogger:
    """Handles logging and reporting of all screenshot processing operations."""
    
    def __init__(self, log_file_path: Path):
        self.log_file_path = log_file_path
        self.session_log: List[str] = []
        self.summary = ProcessingSummary()
        
        # Initialize log file with session header
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize a new logging session."""
        self.summary.start_time = datetime.datetime.now()
        header = f"\n{'='*60}\nScreenshot Renaming Session - {self.summary.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n"
        self.session_log.append(header)
    
    def log_scan_results(self, total_files: int):
        """Log the results of the initial file scan."""
        self.summary.total_files = total_files
        message = f"Found {total_files} screenshot files to process"
        print(message)
        self.session_log.append(f"[SCAN] {message}")
    
    def log_cost_estimate(self, estimate: CostEstimate):
        """Log the cost estimate before processing."""
        self.summary.estimated_cost = estimate.total_estimated_cost
        message = f"Estimated cost: ${estimate.total_estimated_cost:.4f} ({estimate.total_images} images)"
        print(f"\n💰 {message}")
        print(f"   • Image processing: ${estimate.estimated_image_cost:.4f}")
        print(f"   • Token generation: ${estimate.estimated_token_cost:.4f}")
        print(f"   • Average image size: {estimate.avg_image_size_mb:.2f} MB")
        self.session_log.append(f"[COST_ESTIMATE] {estimate}")
    
    def log_actual_costs(self, actual_costs: ActualCosts):
        """Log the actual costs after processing."""
        self.summary.actual_cost = actual_costs.estimated_cost
        message = f"Actual cost: ${actual_costs.estimated_cost:.4f}"
        print(f"\n💳 {message}")
        self.session_log.append(f"[ACTUAL_COSTS] {actual_costs}")
    
    def log_analysis_start(self, filename: str):
        """Log the start of image analysis."""
        message = f"Analyzing: {filename}"
        print(f"  {message}")
        self.session_log.append(f"[ANALYSIS] {message}")
    
    def log_analysis_result(self, filename: str, result: AnalysisResult):
        """Log the result of image analysis."""
        if result.success:
            message = f"Generated description for {filename}: '{result.description}'"
            if result.retry_count > 0:
                message += f" (after {result.retry_count} retries)"
        else:
            message = f"Failed to analyze {filename}: {result.error_message}"
            if result.error_details:
                message += f"\n    Details: {result.error_details}"
            self.summary.api_failures += 1
            full_error = f"Analysis failed for {filename}: {result.error_message}"
            if result.error_details:
                full_error += f" | {result.error_details}"
            self.summary.errors.append(full_error)
        
        self.session_log.append(f"[ANALYSIS] {message}")
    
    def log_rename_result(self, result: RenameResult):
        """Log the result of a file rename operation."""
        if result.success:
            message = f"✓ Renamed: {result.original_path.name} → {result.new_path.name}"
            self.summary.successful_renames += 1
            print(f"  {message}")
        else:
            message = f"✗ Failed to rename {result.original_path.name}: {result.error_message}"
            self.summary.failed_renames += 1
            self.summary.errors.append(f"Rename failed for {result.original_path.name}: {result.error_message}")
            print(f"  {message}")
        
        self.session_log.append(f"[RENAME] {message}")
    
    def log_progress(self, current: int, total: int):
        """Log processing progress."""
        percentage = (current / total) * 100 if total > 0 else 0
        message = f"Progress: {current}/{total} ({percentage:.1f}%)"
        print(f"\n{message}")
        self.session_log.append(f"[PROGRESS] {message}")
    
    def log_error(self, error_message: str, context: str = ""):
        """Log an error with optional context."""
        full_message = f"ERROR: {error_message}"
        if context:
            full_message += f" (Context: {context})"
        
        print(f"  {full_message}")
        self.session_log.append(f"[ERROR] {full_message}")
        self.summary.errors.append(full_message)
    
    def generate_summary(self) -> ProcessingSummary:
        """Generate and log the final processing summary."""
        self.summary.end_time = datetime.datetime.now()
        
        summary_text = f"""
Processing Summary:
------------------
Total files found: {self.summary.total_files}
Successful renames: {self.summary.successful_renames}
Failed renames: {self.summary.failed_renames}
API failures: {self.summary.api_failures}
Success rate: {self.summary.success_rate:.1f}%
Duration: {self.summary.duration}

Cost Information:
-----------------
Estimated cost: ${self.summary.estimated_cost:.4f}
Actual cost: ${self.summary.actual_cost:.4f}
Cost per file: ${self.summary.actual_cost/max(self.summary.successful_renames, 1):.4f}

"""
        
        if self.summary.errors:
            summary_text += f"Errors ({len(self.summary.errors)}):\n"
            for i, error in enumerate(self.summary.errors, 1):
                summary_text += f"  {i}. {error}\n"
        
        print(summary_text)
        self.session_log.append(f"[SUMMARY] {summary_text}")
        
        return self.summary
    
    def save_log(self):
        """Save the session log to file."""
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                for entry in self.session_log:
                    f.write(entry + '\n')
            
            print(f"\nLog saved to: {self.log_file_path}")
            
        except Exception as e:
            print(f"Failed to save log file: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return {
            'total_files': self.summary.total_files,
            'successful_renames': self.summary.successful_renames,
            'failed_renames': self.summary.failed_renames,
            'api_failures': self.summary.api_failures,
            'success_rate': self.summary.success_rate,
            'duration': str(self.summary.duration),
            'errors_count': len(self.summary.errors)
        } 