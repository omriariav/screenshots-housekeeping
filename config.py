"""Configuration management for the Screenshot Renaming Script."""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class APIConfig:
    """Configuration for LLM API settings."""
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4-vision-preview"
    max_tokens: int = 50
    timeout: int = 30
    max_retries: int = 3

@dataclass
class AppConfig:
    """Main application configuration."""
    desktop_path: Path
    log_file_path: Path
    api_config: APIConfig
    description_length: int = 5  # target number of words
    batch_size: int = 5

class ConfigManager:
    """Manages application configuration and environment setup."""
    
    def __init__(self):
        # Use environment variable if set, otherwise default to home Desktop
        desktop_path_env = os.getenv("DESKTOP_PATH")
        if desktop_path_env:
            self.desktop_path = Path(desktop_path_env)
        else:
            self.desktop_path = Path.home() / "Desktop"
        self.log_file_path = self.desktop_path / "screenshot_rename_log.txt"
        
    def get_config(self) -> AppConfig:
        """Get complete application configuration."""
        api_key = self._get_api_key()
        
        api_config = APIConfig(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4-vision-preview"),
            max_tokens=int(os.getenv("MAX_TOKENS", "50")),
            timeout=int(os.getenv("API_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3"))
        )
        
        return AppConfig(
            desktop_path=self.desktop_path,
            log_file_path=self.log_file_path,
            description_length=int(os.getenv("DESCRIPTION_LENGTH", "5")),
            batch_size=int(os.getenv("BATCH_SIZE", "5")),
            api_config=api_config
        )
    
    def _get_api_key(self) -> str:
        """Get API key from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable "
                "or add it to a .env file in the project directory."
            )
        return api_key
    
    def validate_environment(self) -> bool:
        """Validate that the environment is properly configured."""
        try:
            # Check if desktop directory exists and is writable
            if not self.desktop_path.exists():
                print(f"Error: Desktop directory not found at {self.desktop_path}")
                return False
            
            if not os.access(self.desktop_path, os.W_OK):
                print(f"Error: No write permission to desktop directory {self.desktop_path}")
                return False
            
            # Validate API key
            self._get_api_key()
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False 