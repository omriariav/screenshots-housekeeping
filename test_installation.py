#!/usr/bin/env python3
"""Test script to validate installation and dependencies."""

import sys
import os
from pathlib import Path

def test_python_version():
    """Test Python version compatibility."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is too old. Need Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def test_dependencies():
    """Test required dependencies."""
    dependencies = {
        'requests': 'HTTP requests library',
        'PIL': 'Image processing (Pillow)',
        'dotenv': 'Environment variable loading'
    }
    
    missing = []
    for dep, description in dependencies.items():
        try:
            if dep == 'PIL':
                from PIL import Image
            elif dep == 'dotenv':
                from dotenv import load_dotenv
            else:
                __import__(dep)
            print(f"✅ {dep} ({description}) - OK")
        except ImportError:
            print(f"❌ {dep} ({description}) - MISSING")
            missing.append(dep)
    
    return len(missing) == 0

def test_modules():
    """Test our custom modules."""
    modules = ['config', 'file_manager', 'vision_analyzer', 'logger', 'screenshot_renamer']
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}.py - OK")
        except ImportError as e:
            print(f"❌ {module}.py - ERROR: {e}")
            return False
    
    return True

def test_environment():
    """Test environment setup."""
    desktop_path = Path.home() / "Desktop"
    
    if not desktop_path.exists():
        print(f"❌ Desktop directory not found: {desktop_path}")
        return False
    
    if not os.access(desktop_path, os.W_OK):
        print(f"❌ No write permission to desktop: {desktop_path}")
        return False
    
    print(f"✅ Desktop access - OK ({desktop_path})")
    
    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found (copy env.example to .env)")
    
    return True

def main():
    """Run all tests."""
    print("Screenshot Renaming Tool - Installation Test")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("Custom Modules", test_modules),
        ("Environment", test_environment)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Installation looks good.")
        print("\nNext steps:")
        print("1. Copy env.example to .env")
        print("2. Add your OpenAI API key to .env")
        print("3. Run: python3 screenshot_renamer.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nTo install missing dependencies:")
        print("pip3 install -r requirements.txt")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 