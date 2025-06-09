"""LLM vision analysis for generating screenshot descriptions."""

import base64
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import requests
from PIL import Image
import io

from config import APIConfig
from cost_calculator import CostCalculator

@dataclass
class AnalysisResult:
    """Result of image analysis."""
    success: bool
    description: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

class VisionAnalyzer:
    """Handles LLM-based image analysis for screenshot descriptions."""
    
    def __init__(self, api_config: APIConfig, cost_calculator: CostCalculator):
        self.api_config = api_config
        self.cost_calculator = cost_calculator
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_config.api_key}",
            "Content-Type": "application/json"
        })
    
    def analyze_screenshot(self, image_path: Path) -> AnalysisResult:
        """Analyze a screenshot and generate a concise description."""
        retry_count = 0
        
        while retry_count <= self.api_config.max_retries:
            try:
                # Prepare image for analysis
                image_data = self._prepare_image(image_path)
                if not image_data:
                    return AnalysisResult(
                        success=False,
                        error_message="Failed to process image file"
                    )
                
                # Make API request
                response = self._make_api_request(image_data)
                
                if response:
                    description = self._parse_description(response)
                    # Track successful API call for cost calculation
                    self.cost_calculator.track_request(True, description)
                    return AnalysisResult(
                        success=True,
                        description=description,
                        retry_count=retry_count
                    )
                
            except requests.exceptions.Timeout:
                print(f"API timeout for {image_path.name}, attempt {retry_count + 1}")
            except requests.exceptions.RequestException as e:
                print(f"API request failed for {image_path.name}: {e}")
            except Exception as e:
                print(f"Unexpected error analyzing {image_path.name}: {e}")
            
            retry_count += 1
            if retry_count <= self.api_config.max_retries:
                # Exponential backoff
                time.sleep(2 ** retry_count)
        
        # Track failed API call
        self.cost_calculator.track_request(False)
        return AnalysisResult(
            success=False,
            error_message=f"Failed after {retry_count} attempts",
            retry_count=retry_count
        )
    
    def _prepare_image(self, image_path: Path) -> Optional[str]:
        """Prepare image for API submission by compressing and encoding."""
        try:
            # Open and potentially compress the image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (to reduce API costs and improve speed)
                max_size = (1024, 1024)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85)
                img_byte_arr = img_byte_arr.getvalue()
                
                # Encode to base64
                return base64.b64encode(img_byte_arr).decode('utf-8')
                
        except Exception as e:
            print(f"Error preparing image {image_path}: {e}")
            return None
    
    def _make_api_request(self, image_data: str) -> Optional[dict]:
        """Make API request to analyze the image."""
        payload = {
            "model": self.api_config.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this screenshot and provide a concise 4-5 word description "
                                "that captures the main content or purpose. Focus on what the user "
                                "was doing or viewing. Examples: 'Web browser article reading', "
                                "'Code editor Python file', 'Settings screen preferences', "
                                "'Email inbox messages'. Be specific but brief."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": self.api_config.max_tokens,
            "temperature": 0.3  # Lower temperature for more consistent descriptions
        }
        
        try:
            response = self.session.post(
                f"{self.api_config.base_url}/chat/completions",
                json=payload,
                timeout=self.api_config.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return None
    
    def _parse_description(self, response: dict) -> str:
        """Parse the description from API response."""
        try:
            content = response['choices'][0]['message']['content']
            
            # Clean up the description
            description = content.strip().strip('"').strip("'")
            
            # Remove common prefixes that might appear
            prefixes_to_remove = [
                "This screenshot shows",
                "The screenshot shows",
                "This image shows",
                "The image shows",
                "Screenshot of",
                "Image of"
            ]
            
            for prefix in prefixes_to_remove:
                if description.lower().startswith(prefix.lower()):
                    description = description[len(prefix):].strip()
            
            # Ensure it's not too long
            words = description.split()
            if len(words) > 6:
                description = ' '.join(words[:5])
            
            return description
            
        except (KeyError, IndexError) as e:
            print(f"Error parsing API response: {e}")
            return "Screenshot content"  # Fallback description
    
    def test_connection(self) -> bool:
        """Test if the API connection is working."""
        try:
            response = self.session.get(
                f"{self.api_config.base_url}/models",
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False 