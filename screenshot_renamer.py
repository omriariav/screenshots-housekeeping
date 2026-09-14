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
            provider = getattr(self.config.api_config, "provider", "openai")
            self.cost_calculator = CostCalculator(provider)
            self.vision_analyzer = VisionAnalyzer(self.config.api_config, self.cost_calculator)
            self.logger = ActionLogger(self.config.log_file_path, provider)
            
            is_local = self.cost_calculator.is_local
            print("Testing Ollama connection..." if is_local else "Testing API connection...")
            connection_ok, connection_message = self.vision_analyzer.test_connection()
            print(connection_message)
            if not connection_ok:
                if is_local:
                    print("Warning: Ollama connection issues detected. The script may fail during processing.")
                    print("Please check that Ollama is running and the configured model is installed.")
                else:
                    print("Warning: API connection issues detected. The script may fail during processing.")
                    print("Please check your API key and network connection before proceeding.")
            
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
            
            # Group screenshots and show the provider request estimate
            timestamp_groups = self.file_manager.group_screenshots_by_timestamp(screenshots)
            cost_estimate = self.cost_calculator.estimate_costs_grouped(timestamp_groups)
            self.logger.log_cost_estimate(cost_estimate)
            
            print(f"Found {len(screenshots)} screenshot files in {len(timestamp_groups)} timestamp groups")
            request_label = "Ollama model requests" if self.cost_calculator.is_local else "API calls"
            print(f"Will make {len(timestamp_groups)} {request_label} instead of {len(screenshots)}\n")
            
            # Process screenshots in batches
            self._process_screenshots_batch(screenshots)
            
            # Log provider usage and generate final summary
            actual_costs = self.cost_calculator.get_actual_costs()
            self.logger.log_actual_costs(actual_costs)
            summary = self.logger.generate_summary()
            self.logger.save_log()
            
            return summary
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            self.logger.log_error("Operation cancelled by user")
            # Log provider usage even if cancelled
            if self.cost_calculator:
                actual_costs = self.cost_calculator.get_actual_costs()
                self.logger.log_actual_costs(actual_costs)
            summary = self.logger.generate_summary()
            self.logger.save_log()
            return summary
            
        except Exception as e:
            self.logger.log_error(f"Unexpected error in main processing: {e}")
            # Log provider usage even if an error occurred
            if self.cost_calculator:
                actual_costs = self.cost_calculator.get_actual_costs()
                self.logger.log_actual_costs(actual_costs)
            summary = self.logger.generate_summary()
            self.logger.save_log()
            return summary
    
    def _process_screenshots_batch(self, screenshots: List[ScreenshotFile]):
        """Process screenshots in batches, grouping by timestamp to share descriptions."""
        # Group screenshots by timestamp
        timestamp_groups = self.file_manager.group_screenshots_by_timestamp(screenshots)
        
        total_groups = len(timestamp_groups)
        total_files = len(screenshots)
        processed_files = 0
        
        print(f"Found {total_groups} timestamp groups for {total_files} files")
        
        for group_num, (timestamp, group_screenshots) in enumerate(timestamp_groups.items(), 1):
            print(f"\nProcessing group {group_num}/{total_groups}: {timestamp} ({len(group_screenshots)} files)")
            
            # Process the first screenshot in the group to get the description
            representative_screenshot = group_screenshots[0]
            
            try:
                # Validate file access for representative screenshot
                if not self.file_manager.validate_file_access(representative_screenshot.path):
                    self.logger.log_error(f"Cannot access representative file: {representative_screenshot.original_name}")
                    processed_files += len(group_screenshots)
                    continue
                
                # Analyze the representative screenshot
                self.logger.log_analysis_start(representative_screenshot.original_name)
                analysis_result = self.vision_analyzer.analyze_screenshot(representative_screenshot.path)
                self.logger.log_analysis_result(representative_screenshot.original_name, analysis_result)
                
                # If analysis failed, skip this entire group
                if not analysis_result.success:
                    self.logger.log_error(f"Analysis failed for group {timestamp}, skipping all {len(group_screenshots)} files")
                    processed_files += len(group_screenshots)
                    continue
                
                # Apply the same description to all screenshots in the group
                print(f"   Using description: '{analysis_result.description}' for all {len(group_screenshots)} files")
                rename_results = self.file_manager.rename_screenshot_group(group_screenshots, analysis_result.description)
                
                # Log rename results
                for rename_result in rename_results:
                    self.logger.log_rename_result(rename_result)
                    processed_files += 1
                    
                    # Log progress
                    if processed_files % 5 == 0 or processed_files == total_files:
                        self.logger.log_progress(processed_files, total_files)
                
            except Exception as e:
                self.logger.log_error(f"Error processing group {timestamp}: {e}")
                processed_files += len(group_screenshots)

            # Preserve the existing courtesy delay for cloud OpenAI calls.
            if not self.cost_calculator.is_local and group_num < total_groups:
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
        
        # Show provider request estimate with grouping
        timestamp_groups = self.file_manager.group_screenshots_by_timestamp(screenshots)
        cost_estimate = self.cost_calculator.estimate_costs_grouped(timestamp_groups)
        if self.cost_calculator.is_local:
            print(f"\n🖥️  Ollama model requests: {len(timestamp_groups)}")
            print("   • OpenAI API cost: $0.0000 (Ollama inference)")
        else:
            print(f"\n💰 Estimated cost: ${cost_estimate.total_estimated_cost:.4f}")
            print(f"   • {len(timestamp_groups)} API calls (grouped by timestamp) × ${cost_estimate.total_estimated_cost/cost_estimate.total_images:.4f} each")
        print(f"   • Processing {len(screenshots)} files but only analyzing {len(timestamp_groups)} unique timestamps")
        
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
