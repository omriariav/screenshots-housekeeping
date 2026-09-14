"""LLM vision analysis for generating screenshot descriptions."""

import base64
import time
from pathlib import Path
from typing import Optional, List, Tuple
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
    error_details: Optional[str] = None  # Additional technical details
    retry_count: int = 0

class VisionAnalyzer:
    """Handles LLM-based image analysis for screenshot descriptions."""
    
    def __init__(self, api_config: APIConfig, cost_calculator: CostCalculator):
        self.api_config = api_config
        self.cost_calculator = cost_calculator
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        if api_config.provider == "openai":
            self.session.headers.update({"Authorization": f"Bearer {api_config.api_key}"})
        self.last_errors: List[str] = []  # Track errors across retries
    
    def analyze_screenshot(self, image_path: Path) -> AnalysisResult:
        """Analyze a screenshot and generate a concise description."""
        retry_count = 0
        self.last_errors = []  # Reset error tracking for this analysis
        
        while retry_count <= self.api_config.max_retries:
            try:
                # Prepare image for analysis
                image_data = self._prepare_image(image_path)
                if not image_data:
                    return AnalysisResult(
                        success=False,
                        error_message="Failed to process image file",
                        error_details="Could not read, convert, or encode the image file. Check if the file is corrupted or in an unsupported format."
                    )
                
                # Make API request
                response = self._make_api_request(image_data)
                
                if response:
                    description = self._parse_description(response)
                    
                    # Check if description is None (safety refusal)
                    if description is None:
                        # Track failed API call for cost calculation (AI refused)
                        self.cost_calculator.track_request(False)
                        return AnalysisResult(
                            success=False,
                            error_message="AI safety filter refused to analyze image",
                            error_details="The AI model's safety filters prevented analysis of this image. This typically happens with screenshots containing sensitive, personal, or inappropriate content.",
                            retry_count=retry_count
                        )
                    
                    # Track successful API call for cost calculation
                    self.cost_calculator.track_request(True, description)
                    return AnalysisResult(
                        success=True,
                        description=description,
                        retry_count=retry_count
                    )
                
            except requests.exceptions.Timeout:
                error_msg = f"API timeout after {self.api_config.timeout}s (attempt {retry_count + 1})"
                self.last_errors.append(error_msg)
                print(f"API timeout for {image_path.name}, attempt {retry_count + 1}")
            except requests.exceptions.RequestException as e:
                error_msg = f"API request failed: {str(e)} (attempt {retry_count + 1})"
                self.last_errors.append(error_msg)
                print(f"API request failed for {image_path.name}: {e}")
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)} (attempt {retry_count + 1})"
                self.last_errors.append(error_msg)
                print(f"Unexpected error analyzing {image_path.name}: {e}")
            
            retry_count += 1
            if retry_count <= self.api_config.max_retries:
                # Exponential backoff
                time.sleep(2 ** retry_count)
        
        # Track failed API call
        self.cost_calculator.track_request(False)
        
        # Create comprehensive error message with all retry details
        primary_error = f"Failed after {retry_count} attempts"
        detailed_errors = "; ".join(self.last_errors) if self.last_errors else "No specific error details captured"
        
        return AnalysisResult(
            success=False,
            error_message=primary_error,
            error_details=f"All attempts failed. Details: {detailed_errors}",
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
        """Make a provider-specific request to analyze the image."""
        prompt = (
            "Analyze this screenshot and provide a concise 4-5 word description "
            "that captures the main content or purpose. Focus on what the user "
            "was doing or viewing. Examples: 'Web browser article reading', "
            "'Code editor Python file', 'Settings screen preferences', "
            "'Email inbox messages'. Be specific but brief."
        )
        if self.api_config.provider == "ollama":
            payload = {
                "model": self.api_config.model,
                "messages": [{"role": "user", "content": prompt, "images": [image_data]}],
                "stream": False,
                "options": {"num_predict": self.api_config.max_tokens, "temperature": 0.3}
            }
            endpoint = "/api/chat"
        else:
            payload = {
                "model": self.api_config.model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }],
                "max_tokens": self.api_config.max_tokens,
                "temperature": 0.3
            }
            endpoint = "/chat/completions"
        
        try:
            response = self.session.post(
                f"{self.api_config.base_url}{endpoint}",
                json=payload,
                timeout=self.api_config.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Enhanced error handling with specific status code analysis
            error_details = self._analyze_api_error(e)
            print(f"API request failed: {error_details}")
            
            # Re-raise with the enhanced error information
            enhanced_error = requests.exceptions.RequestException(error_details)
            enhanced_error.response = e.response if hasattr(e, 'response') else None
            raise enhanced_error
    
    def _analyze_api_error(self, error: requests.exceptions.RequestException) -> str:
        """Analyze provider-specific API errors and provide actionable guidance."""
        if self.api_config.provider == "ollama":
            return self._analyze_ollama_error(error)

        if hasattr(error, 'response') and error.response is not None:
            status_code = error.response.status_code
            try:
                error_body = error.response.json()
                api_error_message = error_body.get('error', {}).get('message', '')
            except Exception:
                api_error_message = getattr(error.response, 'text', '')[:200]

            if status_code == 401:
                return f"Authentication failed (401): Invalid or expired API key. Please check your OPENAI_API_KEY in the .env file. API response: {api_error_message}"
            if status_code == 403:
                return f"Access forbidden (403): API key doesn't have required permissions. Ensure your API key has access to GPT-4 Vision. API response: {api_error_message}"
            if status_code == 429:
                if 'quota' in api_error_message.lower():
                    return f"Quota exceeded (429): You've reached your API usage limit. Check your OpenAI billing and usage limits. API response: {api_error_message}"
                return f"Rate limit exceeded (429): Too many requests. The script will automatically retry with backoff. API response: {api_error_message}"
            if status_code == 400:
                if 'model' in api_error_message.lower():
                    return f"Invalid model (400): The model '{self.api_config.model}' may not exist or be accessible. Check your OPENAI_MODEL setting in .env. API response: {api_error_message}"
                return f"Bad request (400): Invalid request format or parameters. API response: {api_error_message}"
            if status_code == 404:
                return f"Not found (404): The API endpoint or resource was not found. This may indicate an issue with the API URL or the model name. API response: {api_error_message}"
            if status_code == 422:
                return f"Unprocessable entity (422): The request was well-formed but contains invalid data. This often happens with unsupported image formats or sizes. API response: {api_error_message}"
            if status_code == 500:
                return f"OpenAI server error (500): Temporary issue with OpenAI's servers. This is usually temporary - the script will retry automatically. API response: {api_error_message}"
            if status_code == 502:
                return f"Bad gateway (502): Issue with OpenAI's server infrastructure. This is usually temporary - the script will retry automatically. API response: {api_error_message}"
            if status_code == 503:
                return f"Service unavailable (503): OpenAI servers are temporarily overloaded. This is usually temporary - the script will retry automatically. API response: {api_error_message}"
            if status_code == 504:
                return f"Gateway timeout (504): Request took too long to process. This may indicate server overload - the script will retry automatically. API response: {api_error_message}"
            return f"HTTP {status_code} error: {api_error_message or 'Unknown error'}. This is an unexpected status code. If the problem persists, check OpenAI's status page or contact support. Full error: {str(error)}"

        # SSLError subclasses ConnectionError, so it must be checked first.
        if isinstance(error, requests.exceptions.SSLError):
            return f"SSL/TLS error: Problem with secure connection to OpenAI. This may indicate network configuration issues. Detailed error: {str(error)}"
        if isinstance(error, requests.exceptions.ConnectionError):
            return f"Network connection error: Cannot reach OpenAI servers. Check your internet connection and firewall settings. Detailed error: {str(error)}"
        if isinstance(error, requests.exceptions.Timeout):
            return f"Request timeout: API call took longer than {self.api_config.timeout} seconds. This may indicate network issues or server overload. Detailed error: {str(error)}"
        if isinstance(error, requests.exceptions.TooManyRedirects):
            return f"Too many redirects: The request was redirected too many times. This may indicate an issue with the API URL configuration. Detailed error: {str(error)}"
        if isinstance(error, requests.exceptions.ChunkedEncodingError):
            return f"Chunked encoding error: Problem receiving response data. This may indicate network issues or server problems. Detailed error: {str(error)}"
        if isinstance(error, requests.exceptions.ContentDecodingError):
            return f"Content decoding error: Problem decoding the response. This may indicate server issues or corrupted data. Detailed error: {str(error)}"
        if isinstance(error, requests.exceptions.RequestException):
            return f"Request exception: An unexpected network or HTTP error occurred. Detailed error: {str(error)}"
        return f"Unexpected error: {type(error).__name__}: {str(error)}. This is an unexpected error type. If the problem persists, please report this as a bug."

    def _analyze_ollama_error(self, error: requests.exceptions.RequestException) -> str:
        """Analyze errors returned by the local Ollama service."""
        if hasattr(error, 'response') and error.response is not None:
            status_code = error.response.status_code
            
            # Try to get error details from response
            try:
                error_body = error.response.json()
                api_error_message = error_body.get('error', {}).get('message', '')
                api_error_type = error_body.get('error', {}).get('type', '')
            except Exception:
                # If we can't parse JSON, try to get text content
                try:
                    api_error_message = error.response.text[:200] if error.response.text else ''
                    api_error_type = ''
                except Exception:
                    api_error_message = 'Unable to retrieve error details'
                    api_error_type = ''
            
            if status_code == 400:
                if 'model' in api_error_message.lower():
                    return (
                        f"Invalid Ollama model (400): '{self.api_config.model}' is unavailable or does not support this request. "
                        f"Run `ollama pull {self.api_config.model}` and verify OLLAMA_MODEL in .env. "
                        f"API response: {api_error_message}"
                    )
                else:
                    return (
                        f"Bad Ollama request (400): Invalid request format or parameters. "
                        f"API response: {api_error_message}"
                    )
            elif status_code == 404:
                return (
                    f"Ollama endpoint or model not found (404). Check OLLAMA_BASE_URL "
                    f"({self.api_config.base_url}) and run `ollama pull {self.api_config.model}`. "
                    f"API response: {api_error_message}"
                )
            elif status_code == 422:
                return (
                    f"Ollama could not process this request (422): The request contains invalid data. "
                    f"This often happens with unsupported image formats or sizes. "
                    f"API response: {api_error_message}"
                )
            elif status_code == 500:
                return (
                    f"Ollama server error (500): The local Ollama service could not process the request. "
                    f"The script will retry automatically; check the Ollama service logs if it persists. "
                    f"API response: {api_error_message}"
                )
            elif status_code == 502:
                return (
                    f"Bad gateway from Ollama (502): Check that the Ollama service is running at "
                    f"{self.api_config.base_url}. The script will retry automatically. "
                    f"API response: {api_error_message}"
                )
            elif status_code == 503:
                return (
                    f"Ollama service unavailable (503): Start or restart Ollama, then try again. "
                    f"API response: {api_error_message}"
                )
            elif status_code == 504:
                return (
                    f"Gateway timeout (504): Request took too long to process. "
                    f"This may indicate server overload - the script will retry automatically. "
                    f"API response: {api_error_message}"
                )
            else:
                # Handle any other HTTP status codes
                return (
                    f"HTTP {status_code} error: {api_error_message or 'Unknown error'}. "
                    f"This is an unexpected status code. If the problem persists, "
                    f"check that Ollama is running at {self.api_config.base_url}. "
                    f"Full error: {str(error)}"
                )
        
        # Handle network-level errors
        # SSLError subclasses ConnectionError, so it must be checked first.
        elif isinstance(error, requests.exceptions.SSLError):
            return (
                f"SSL/TLS error connecting to Ollama. Check OLLAMA_BASE_URL and any local proxy configuration. "
                f"Detailed error: {str(error)}"
            )
        elif isinstance(error, requests.exceptions.ConnectionError):
            return (
                f"Cannot reach the local Ollama service at {self.api_config.base_url}. "
                f"Start it with `ollama serve` (or open the Ollama app) and verify OLLAMA_BASE_URL. "
                f"Detailed error: {str(error)}"
            )
        elif isinstance(error, requests.exceptions.Timeout):
            return (
                f"Request timeout: API call took longer than {self.api_config.timeout} seconds. "
                f"The local model may still be loading or generating; try a smaller model or increase API_TIMEOUT. "
                f"Detailed error: {str(error)}"
            )
        elif isinstance(error, requests.exceptions.TooManyRedirects):
            return (
                f"Too many redirects: The request was redirected too many times. "
                f"This may indicate an issue with the API URL configuration. "
                f"Detailed error: {str(error)}"
            )
        elif isinstance(error, requests.exceptions.ChunkedEncodingError):
            return (
                f"Chunked encoding error: Problem receiving response data. "
                f"This may indicate network issues or server problems. "
                f"Detailed error: {str(error)}"
            )
        elif isinstance(error, requests.exceptions.ContentDecodingError):
            return (
                f"Content decoding error: Problem decoding the response. "
                f"This may indicate server issues or corrupted data. "
                f"Detailed error: {str(error)}"
            )
        elif isinstance(error, requests.exceptions.RequestException):
            # Catch-all for any other requests-related errors
            return (
                f"Request exception: An unexpected network or HTTP error occurred. "
                f"Detailed error: {str(error)}"
            )
        else:
            # Ultimate catch-all for any other type of exception
            return (
                f"Unexpected error: {type(error).__name__}: {str(error)}. "
                f"This is an unexpected error type. If the problem persists, "
                f"please report this as a bug."
            )
    
    def _parse_description(self, response: dict) -> Optional[str]:
        """Parse the description from API response."""
        try:
            # Validate response structure
            if not isinstance(response, dict):
                print(f"Error: API response is not a dictionary. Got {type(response)}: {str(response)[:100]}")
                return "Screenshot content"  # Fallback description
            
            if self.api_config.provider == "ollama":
                if 'message' not in response:
                    print(f"Error: Ollama response missing 'message' field. Response: {str(response)[:200]}")
                    return "Screenshot content"
                message = response['message']
            else:
                if 'choices' not in response or not response['choices']:
                    print(f"Error: API response missing usable 'choices'. Response: {str(response)[:200]}")
                    return "Screenshot content"
                message = response['choices'][0].get('message', {})
            if 'content' not in message:
                print(f"Error: API message missing 'content' field. Message: {str(message)[:200]}")
                return "Screenshot content"  # Fallback description
            
            content = message['content']
            
            # Validate content type
            if content is None:
                print("Warning: API returned null content")
                return "Screenshot content"  # Fallback description
            
            if not isinstance(content, str):
                print(f"Warning: API content is not a string. Got {type(content)}: {str(content)[:100]}")
                # Try to convert to string
                try:
                    content = str(content)
                except Exception as e:
                    print(f"Error converting content to string: {e}")
                    return "Screenshot content"  # Fallback description
            
            # Clean up the description
            description = content.strip().strip('"').strip("'")
            
            # Check for empty or whitespace-only content
            if not description or description.isspace():
                print("Warning: API returned empty or whitespace-only content")
                return "Screenshot content"  # Fallback description
            
            # Check for safety refusal responses that indicate the model won't analyze the image
            refusal_patterns = [
                "i'm sorry, i can't help",
                "i can't help with that",
                "i'm not able to help",
                "i cannot help",
                "i'm sorry, but i can't",
                "i can't assist with",
                "i'm unable to help",
                "i cannot assist",
                "i'm sorry, i cannot",
                "i can't provide",
                "i'm not able to provide",
                "i cannot provide",
                "i can't analyze",
                "i cannot analyze",
                "i'm not able to analyze",
                "i'm sorry, i can't analyze"
            ]
            
            # Check if response matches refusal patterns
            description_lower = description.lower()
            for pattern in refusal_patterns:
                if pattern in description_lower:
                    print(f"   🚫 AI refused to analyze image (safety filter): {description[:50]}...")
                    return None  # Return None to indicate refusal/failure
            
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
            
            # Final validation - ensure we have a meaningful description
            if len(description.strip()) < 2:
                print(f"Warning: Description too short after processing: '{description}'")
                return "Screenshot content"  # Fallback description
            
            return description
            
        except (KeyError, IndexError) as e:
            print(f"Error parsing API response structure: {e}")
            print(f"Response structure: {str(response)[:300] if response else 'None'}")
            return "Screenshot content"  # Fallback description
        except TypeError as e:
            print(f"Error with response data types: {e}")
            print(f"Response type: {type(response)}, content: {str(response)[:200] if response else 'None'}")
            return "Screenshot content"  # Fallback description
        except AttributeError as e:
            print(f"Error accessing response attributes: {e}")
            print(f"Response: {str(response)[:200] if response else 'None'}")
            return "Screenshot content"  # Fallback description
        except Exception as e:
            print(f"Unexpected error parsing API response: {type(e).__name__}: {e}")
            print(f"Response: {str(response)[:200] if response else 'None'}")
            return "Screenshot content"  # Fallback description
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the configured provider and verify its model is available."""
        if self.api_config.provider == "openai":
            return self._test_openai_connection()

        try:
            response = self.session.get(
                f"{self.api_config.base_url}/api/tags",
                timeout=10
            )
            
            if response.status_code == 200:
                # Try to verify the model is available
                try:
                    models_data = response.json()
                    available_models = [model.get('name', '') for model in models_data.get('models', [])]
                    model_names = set(available_models)
                    requested_model = self.api_config.model
                    model_is_available = (
                        requested_model in model_names
                        or f"{requested_model}:latest" in model_names
                        or (requested_model.endswith(":latest") and requested_model[:-7] in model_names)
                    )
                    if model_is_available:
                        return True, f"✅ Ollama connection successful. Model '{self.api_config.model}' is available."
                    else:
                        available = ', '.join(available_models[:5]) or 'none'
                        return False, (
                            f"⚠️ Ollama is running, but model '{self.api_config.model}' is not installed. "
                            f"Run `ollama pull {self.api_config.model}`. Available models: {available}"
                        )
                except:
                    return True, "✅ Ollama connection successful (couldn't verify installed models)."
            else:
                connection_error = requests.exceptions.RequestException(
                    f"HTTP {response.status_code}"
                )
                connection_error.response = response
                error_details = self._analyze_api_error(
                    connection_error
                )
                error_details = error_details.replace("Request failed: ", "")
                return False, f"❌ Ollama connection failed: {error_details}"
                
        except requests.exceptions.RequestException as e:
            error_details = self._analyze_api_error(e)
            return False, f"❌ Ollama connection failed: {error_details}"
        except Exception as e:
            return False, f"❌ Unexpected error testing Ollama connection: {str(e)}"

    def _test_openai_connection(self) -> Tuple[bool, str]:
        """Preserve the OpenAI model-list preflight behavior."""
        try:
            response = self.session.get(
                f"{self.api_config.base_url}/models",
                timeout=10
            )
            if response.status_code == 200:
                try:
                    models_data = response.json()
                    available_models = [model.get('id', '') for model in models_data.get('data', [])]
                    if self.api_config.model in available_models:
                        return True, f"✅ API connection successful. Model '{self.api_config.model}' is available."
                    return False, f"⚠️ API connection successful, but model '{self.api_config.model}' is not available. Available models include: {', '.join(available_models[:5])}..."
                except Exception:
                    return True, "✅ API connection successful (couldn't verify model availability)."

            connection_error = requests.exceptions.RequestException(
                f"HTTP {response.status_code}"
            )
            connection_error.response = response
            error_details = self._analyze_api_error(connection_error).replace(
                "Request failed: ", ""
            )
            return False, f"❌ API connection failed: {error_details}"
        except requests.exceptions.RequestException as e:
            error_details = self._analyze_api_error(e)
            return False, f"❌ API connection failed: {error_details}"
        except Exception as e:
            return False, f"❌ Unexpected error testing API connection: {str(e)}"
