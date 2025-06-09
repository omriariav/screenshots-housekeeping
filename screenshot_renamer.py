"""Main application controller for the Screenshot Renaming Script."""

import sys
import time
from pathlib import Path
from typing import List

from config import ConfigManager, AppConfig
from file_manager import FileManager, ScreenshotFile
from vision_analyzer import VisionAnalyzer
from logger import ActionLogger, ProcessingSummary
from cost_calculator import CostCalculator

class ScreenshotRenamer:
    """Main application controller for screenshot renaming operations."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config: AppConfig = None
        self.file_manager: FileManager = None
        self.vision_analyzer: VisionAnalyzer = None
        self.logger: ActionLogger = None
        self.cost_calculator: CostCalculator = None
    
    def initialize(self) -> bool:
        """Initialize all components and validate environment."""
        try:
            print("Screenshot Renaming Tool")
            print("=" * 40)
            
            # Validate environment
            if not self.config_manager.validate_environment():
                return False
            
            # Load configuration
            self.config = self.config_manager.get_config()
            
            # Initialize components
            self.file_manager = FileManager(self.config.desktop_path)
            self.cost_calculator = CostCalculator()
            self.vision_analyzer = VisionAnalyzer(self.config.api_config, self.cost_calculator)
            self.logger = ActionLogger(self.config.log_file_path)
            
            # Test API connection
            print("Testing API connection...")
            if not self.vision_analyzer.test_connection():
                print("Warning: Could not verify API connection. Proceeding anyway...")
            else:
                print("API connection verified ✓")
            
            return True
            
        except Exception as e:
            print(f"Initialization failed: {e}")
            return False
    
    def process_all_screenshots(self) -> ProcessingSummary:
        """Process all screenshots on the desktop."""
        if not self.logger:
            raise RuntimeError("Application not initialized. Call initialize() first.")
        
        try:
            # Scan for screenshots
            print(f"\nScanning desktop: {self.config.desktop_path}")
            screenshots = self.file_manager.scan_screenshots()
            
            if not screenshots:
                print("No screenshot files found.")
                self.logger.log_scan_results(0)
                return self.logger.generate_summary()
            
            self.logger.log_scan_results(len(screenshots))
            
            # Show cost estimate
            screenshot_paths = [s.path for s in screenshots]
            cost_estimate = self.cost_calculator.estimate_costs(screenshot_paths)
            self.logger.log_cost_estimate(cost_estimate)
            
            print(f"Found {len(screenshots)} screenshot files to process\n")
            
            # Process screenshots in batches
            self._process_screenshots_batch(screenshots)
            
            # Log actual costs and generate final summary
            actual_costs = self.cost_calculator.get_actual_costs()
            self.logger.log_actual_costs(actual_costs)
            summary = self.logger.generate_summary()
            self.logger.save_log()
            
            return summary
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            self.logger.log_error("Operation cancelled by user")
            # Log costs even if cancelled
            if self.cost_calculator:
                actual_costs = self.cost_calculator.get_actual_costs()
                self.logger.log_actual_costs(actual_costs)
            summary = self.logger.generate_summary()
            self.logger.save_log()
            return summary
            
        except Exception as e:
            self.logger.log_error(f"Unexpected error in main processing: {e}")
            # Log costs even if error occurred
            if self.cost_calculator:
                actual_costs = self.cost_calculator.get_actual_costs()
                self.logger.log_actual_costs(actual_costs)
            summary = self.logger.generate_summary()
            self.logger.save_log()
            return summary
    
    def _process_screenshots_batch(self, screenshots: List[ScreenshotFile]):
        """Process screenshots in batches for better performance and API management."""
        total_files = len(screenshots)
        batch_size = self.config.batch_size
        
        for i in range(0, total_files, batch_size):
            batch = screenshots[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_files + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches}")
            
            for j, screenshot in enumerate(batch):
                current_file = i + j + 1
                
                # Log progress
                if current_file % 5 == 0 or current_file == total_files:
                    self.logger.log_progress(current_file, total_files)
                
                # Process individual screenshot
                self._process_single_screenshot(screenshot)
            
            # Small delay between batches to be respectful of API rate limits
            if i + batch_size < total_files:
                time.sleep(1)
    
    def _process_single_screenshot(self, screenshot: ScreenshotFile):
        """Process a single screenshot file."""
        try:
            # Validate file access
            if not self.file_manager.validate_file_access(screenshot.path):
                self.logger.log_error(f"Cannot access file: {screenshot.original_name}")
                return
            
            # Analyze the screenshot
            self.logger.log_analysis_start(screenshot.original_name)
            analysis_result = self.vision_analyzer.analyze_screenshot(screenshot.path)
            self.logger.log_analysis_result(screenshot.original_name, analysis_result)
            
            # If analysis failed, skip renaming
            if not analysis_result.success:
                return
            
            # Rename the file
            rename_result = self.file_manager.rename_file(screenshot, analysis_result.description)
            self.logger.log_rename_result(rename_result)
            
        except Exception as e:
            self.logger.log_error(f"Error processing {screenshot.original_name}: {e}")
    
    def run_interactive_mode(self):
        """Run the application in interactive mode with user confirmations."""
        if not self.initialize():
            return
        
        screenshots = self.file_manager.scan_screenshots()
        if not screenshots:
            print("No screenshot files found.")
            return
        
        print(f"\nFound {len(screenshots)} screenshot files:")
        for i, screenshot in enumerate(screenshots[:5], 1):
            print(f"  {i}. {screenshot.original_name}")
        
        if len(screenshots) > 5:
            print(f"  ... and {len(screenshots) - 5} more files")
        
        # Show cost estimate
        screenshot_paths = [s.path for s in screenshots]
        cost_estimate = self.cost_calculator.estimate_costs(screenshot_paths)
        print(f"\n💰 Estimated cost: ${cost_estimate.total_estimated_cost:.4f}")
        print(f"   • ~{cost_estimate.total_images} API calls × ${cost_estimate.total_estimated_cost/cost_estimate.total_images:.4f} each")
        
        # Ask for confirmation
        response = input(f"\nProceed with renaming {len(screenshots)} files? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            return
        
        # Process all screenshots
        summary = self.process_all_screenshots()
        
        # Display final results
        print(f"\n{'='*50}")
        print("OPERATION COMPLETE")
        print(f"{'='*50}")
        print(f"Successfully renamed: {summary.successful_renames}/{summary.total_files} files")
        print(f"Processing time: {summary.duration}")
        
        if summary.errors:
            print(f"\nErrors encountered: {len(summary.errors)}")
            print("Check the log file for details.")

def main():
    """Main entry point for the application."""
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        # Automatic mode - no user interaction
        renamer = ScreenshotRenamer()
        if renamer.initialize():
            renamer.process_all_screenshots()
    else:
        # Interactive mode
        renamer = ScreenshotRenamer()
        renamer.run_interactive_mode()

if __name__ == "__main__":
    main() 