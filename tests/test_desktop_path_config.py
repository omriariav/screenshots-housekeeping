#!/usr/bin/env python3
"""Test script to verify DESKTOP_PATH configuration functionality."""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ConfigManager, AppConfig

def test_default_desktop_path():
    """Test that default desktop path is used when DESKTOP_PATH is not set."""
    print("Testing default desktop path...")
    
    # Ensure DESKTOP_PATH is not set
    with patch.dict(os.environ, {}, clear=False):
        if 'DESKTOP_PATH' in os.environ:
            del os.environ['DESKTOP_PATH']
        
        config_manager = ConfigManager()
        expected_path = Path.home() / "Desktop"
        
        if config_manager.desktop_path == expected_path:
            print(f"✅ Default desktop path correct: {config_manager.desktop_path}")
            return True
        else:
            print(f"❌ Expected: {expected_path}, Got: {config_manager.desktop_path}")
            return False

def test_custom_desktop_path():
    """Test that custom desktop path is used when DESKTOP_PATH is set."""
    print("Testing custom desktop path...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_path = temp_dir
        
        # Set DESKTOP_PATH environment variable
        with patch.dict(os.environ, {'DESKTOP_PATH': custom_path}):
            config_manager = ConfigManager()
            expected_path = Path(custom_path)
            
            if config_manager.desktop_path == expected_path:
                print(f"✅ Custom desktop path correct: {config_manager.desktop_path}")
                return True
            else:
                print(f"❌ Expected: {expected_path}, Got: {config_manager.desktop_path}")
                return False

def test_desktop_path_in_app_config():
    """Test that desktop path is properly included in AppConfig."""
    print("Testing desktop path in AppConfig...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_path = temp_dir
        
        # Mock API key to avoid validation error
        with patch.dict(os.environ, {
            'DESKTOP_PATH': custom_path,
            'OPENAI_API_KEY': 'test-key-123'
        }):
            config_manager = ConfigManager()
            
            try:
                app_config = config_manager.get_config()
                expected_path = Path(custom_path)
                
                if app_config.desktop_path == expected_path:
                    print(f"✅ Desktop path in AppConfig correct: {app_config.desktop_path}")
                    return True
                else:
                    print(f"❌ Expected: {expected_path}, Got: {app_config.desktop_path}")
                    return False
            except Exception as e:
                print(f"❌ Error getting config: {e}")
                return False

def test_log_file_path_updates():
    """Test that log file path updates with custom desktop path."""
    print("Testing log file path updates with custom desktop path...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_path = temp_dir
        
        with patch.dict(os.environ, {'DESKTOP_PATH': custom_path}):
            config_manager = ConfigManager()
            expected_log_path = Path(custom_path) / "screenshot_rename_log.txt"
            
            if config_manager.log_file_path == expected_log_path:
                print(f"✅ Log file path updates correctly: {config_manager.log_file_path}")
                return True
            else:
                print(f"❌ Expected: {expected_log_path}, Got: {config_manager.log_file_path}")
                return False

def test_path_validation():
    """Test path validation with custom desktop path."""
    print("Testing path validation with custom desktop path...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_path = temp_dir
        
        # Make the directory writable
        os.chmod(temp_dir, 0o755)
        
        with patch.dict(os.environ, {
            'DESKTOP_PATH': custom_path,
            'OPENAI_API_KEY': 'test-key-123'
        }):
            config_manager = ConfigManager()
            
            # Should pass validation since temp_dir exists and is writable
            if config_manager.validate_environment():
                print(f"✅ Path validation passes for custom path: {custom_path}")
                return True
            else:
                print(f"❌ Path validation failed for custom path: {custom_path}")
                return False

def test_nonexistent_path():
    """Test behavior with non-existent custom path."""
    print("Testing non-existent custom path...")
    
    nonexistent_path = "/this/path/should/not/exist/ever"
    
    with patch.dict(os.environ, {
        'DESKTOP_PATH': nonexistent_path,
        'OPENAI_API_KEY': 'test-key-123'
    }):
        config_manager = ConfigManager()
        
        # Should set the path even if it doesn't exist
        expected_path = Path(nonexistent_path)
        if config_manager.desktop_path == expected_path:
            print(f"✅ Non-existent path is set correctly: {config_manager.desktop_path}")
            
            # But validation should fail
            if not config_manager.validate_environment():
                print("✅ Validation correctly fails for non-existent path")
                return True
            else:
                print("❌ Validation should fail for non-existent path")
                return False
        else:
            print(f"❌ Expected: {expected_path}, Got: {config_manager.desktop_path}")
            return False

def main():
    """Run all DESKTOP_PATH configuration tests."""
    print("DESKTOP_PATH Configuration Tests")
    print("=" * 50)
    
    tests = [
        ("Default Desktop Path", test_default_desktop_path),
        ("Custom Desktop Path", test_custom_desktop_path),
        ("Desktop Path in AppConfig", test_desktop_path_in_app_config),
        ("Log File Path Updates", test_log_file_path_updates),
        ("Path Validation", test_path_validation),
        ("Non-existent Path Handling", test_nonexistent_path)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All DESKTOP_PATH configuration tests passed!")
        print("\nThe DESKTOP_PATH environment variable is working correctly:")
        print("• Uses default ~/Desktop when not set")
        print("• Uses custom path when DESKTOP_PATH is set")
        print("• Updates log file path accordingly")
        print("• Validates paths properly")
    else:
        print("❌ Some tests failed. Please check the configuration implementation.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 