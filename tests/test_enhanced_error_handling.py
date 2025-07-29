"""
Test enhanced error handling for VisionAnalyzer.
Tests various API error scenarios and ensures proper error reporting.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from pathlib import Path
import json
import base64

from config import APIConfig
from cost_calculator import CostCalculator
from vision_analyzer import VisionAnalyzer, AnalysisResult


class TestEnhancedErrorHandling(unittest.TestCase):
    """Test enhanced error handling in VisionAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_config = APIConfig(
            api_key="test_key_12345",
            model="gpt-4-vision-preview",
            max_tokens=50,
            timeout=10,
            max_retries=1  # Reduce retries for faster testing
        )
        self.cost_calculator = CostCalculator()
        self.analyzer = VisionAnalyzer(self.api_config, self.cost_calculator)
        
        # Create a mock image file
        self.test_image_path = Path("test_screenshot.png")
    
    def _setup_successful_image_mock(self):
        """Set up a successful image processing mock that returns valid base64 data."""
        # Create a mock PIL Image
        mock_img = Mock()
        mock_img.mode = 'RGB'
        mock_img.size = (800, 600)
        
        # Mock the save method to write some fake JPEG data
        def mock_save(file_obj, format=None, quality=None):
            file_obj.write(b"fake_jpeg_data")
        
        mock_img.save = mock_save
        mock_img.convert.return_value = mock_img
        mock_img.thumbnail = Mock()
        
        # Mock Image.open to return our mock image
        patcher = patch('vision_analyzer.Image.open')
        mock_image_open = patcher.start()
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        return patcher
    
    def test_invalid_api_key_error_401(self):
        """Test handling of 401 authentication error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with 401 error
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                'error': {
                    'message': 'Incorrect API key provided',
                    'type': 'invalid_request_error'
                }
            }
            mock_response.text = 'Unauthorized'
            
            # Create a RequestException with the mock response
            error = requests.exceptions.RequestException("401 Client Error")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Failed after", result.error_message)
                self.assertIn("Authentication failed (401)", result.error_details)
                self.assertIn("Invalid or expired API key", result.error_details)
                self.assertIn("OPENAI_API_KEY", result.error_details)
                self.assertIn("Incorrect API key provided", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_quota_exceeded_error_429(self):
        """Test handling of 429 quota exceeded error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with 429 quota error
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                'error': {
                    'message': 'You exceeded your current quota, please check your plan and billing details.',
                    'type': 'insufficient_quota'
                }
            }
            
            error = requests.exceptions.RequestException("429 Too Many Requests")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Quota exceeded (429)", result.error_details)
                self.assertIn("usage limit", result.error_details)
                self.assertIn("billing", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_rate_limit_error_429(self):
        """Test handling of 429 rate limit error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with 429 rate limit error
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                'error': {
                    'message': 'Rate limit reached for requests',
                    'type': 'rate_limit_reached'
                }
            }
            
            error = requests.exceptions.RequestException("429 Too Many Requests")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Rate limit exceeded (429)", result.error_details)
                self.assertIn("automatically retry", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_invalid_model_error_400(self):
        """Test handling of 400 invalid model error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with 400 model error
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                'error': {
                    'message': 'The model `gpt-4-vision-preview` does not exist',
                    'type': 'invalid_request_error'
                }
            }
            
            error = requests.exceptions.RequestException("400 Bad Request")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Invalid model (400)", result.error_details)
                self.assertIn("gpt-4-vision-preview", result.error_details)
                self.assertIn("OPENAI_MODEL", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_server_error_500(self):
        """Test handling of 500 server error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with 500 error
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.json.return_value = {
                'error': {
                    'message': 'The server had an error while processing your request.',
                    'type': 'server_error'
                }
            }
            
            error = requests.exceptions.RequestException("500 Internal Server Error")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("OpenAI server error (500)", result.error_details)
                self.assertIn("temporary", result.error_details)
                self.assertIn("retry automatically", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_connection_error(self):
        """Test handling of network connection error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock connection error
            error = requests.exceptions.ConnectionError("Failed to establish a new connection")
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Network connection error", result.error_details)
                self.assertIn("internet connection", result.error_details)
                self.assertIn("firewall", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_timeout_error(self):
        """Test handling of timeout error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock timeout error
            error = requests.exceptions.Timeout("Request timed out")
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Request timeout", result.error_details)
                self.assertIn("10 seconds", result.error_details)  # Uses config timeout
        finally:
            image_patcher.stop()
    
    def test_ssl_error(self):
        """Test handling of SSL error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock SSL error
            error = requests.exceptions.SSLError("SSL certificate verification failed")
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("SSL/TLS error", result.error_details)
                self.assertIn("secure connection", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_unknown_http_error(self):
        """Test handling of unknown HTTP error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock unknown HTTP error
            mock_response = Mock()
            mock_response.status_code = 418  # I'm a teapot - unusual status
            mock_response.json.return_value = {
                'error': {
                    'message': 'Unusual error occurred',
                    'type': 'unknown_error'
                }
            }
            
            error = requests.exceptions.RequestException("418 I'm a teapot")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("HTTP 418 error", result.error_details)
                self.assertIn("Unusual error occurred", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_completely_unexpected_error(self):
        """Test handling of completely unexpected error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock completely unexpected error
            error = ValueError("Something completely unexpected happened")
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Unexpected error", result.error_details)
                self.assertIn("Something completely unexpected happened", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_not_found_error_404(self):
        """Test handling of 404 not found error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with 404 error
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {
                'error': {
                    'message': 'Not found',
                    'type': 'invalid_request_error'
                }
            }
            
            error = requests.exceptions.RequestException("404 Not Found")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Not found (404)", result.error_details)
                self.assertIn("API endpoint", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_unprocessable_entity_error_422(self):
        """Test handling of 422 unprocessable entity error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with 422 error
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.json.return_value = {
                'error': {
                    'message': 'Invalid image format',
                    'type': 'invalid_request_error'
                }
            }
            
            error = requests.exceptions.RequestException("422 Unprocessable Entity")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Unprocessable entity (422)", result.error_details)
                self.assertIn("unsupported image formats", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_bad_gateway_error_502(self):
        """Test handling of 502 bad gateway error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with 502 error
            mock_response = Mock()
            mock_response.status_code = 502
            mock_response.json.return_value = {
                'error': {
                    'message': 'Bad gateway',
                    'type': 'server_error'
                }
            }
            
            error = requests.exceptions.RequestException("502 Bad Gateway")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Bad gateway (502)", result.error_details)
                self.assertIn("server infrastructure", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_gateway_timeout_error_504(self):
        """Test handling of 504 gateway timeout error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with 504 error
            mock_response = Mock()
            mock_response.status_code = 504
            mock_response.json.return_value = {
                'error': {
                    'message': 'Gateway timeout',
                    'type': 'server_error'
                }
            }
            
            error = requests.exceptions.RequestException("504 Gateway Timeout")
            error.response = mock_response
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Gateway timeout (504)", result.error_details)
                self.assertIn("took too long", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_too_many_redirects_error(self):
        """Test handling of too many redirects error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock too many redirects error
            error = requests.exceptions.TooManyRedirects("Too many redirects")
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Too many redirects", result.error_details)
                self.assertIn("API URL configuration", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_chunked_encoding_error(self):
        """Test handling of chunked encoding error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock chunked encoding error
            error = requests.exceptions.ChunkedEncodingError("Connection broken")
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Chunked encoding error", result.error_details)
                self.assertIn("receiving response data", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_content_decoding_error(self):
        """Test handling of content decoding error."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock content decoding error
            error = requests.exceptions.ContentDecodingError("Failed to decode response content")
            
            with patch.object(self.analyzer.session, 'post', side_effect=error):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Content decoding error", result.error_details)
                self.assertIn("decoding the response", result.error_details)
        finally:
            image_patcher.stop()
    
    def test_malformed_api_response(self):
        """Test handling of malformed API response."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock malformed API response (missing choices)
            malformed_response = {"data": "invalid structure"}
            
            with patch.object(self.analyzer.session, 'post') as mock_post:
                mock_post.return_value.json.return_value = malformed_response
                mock_post.return_value.raise_for_status.return_value = None
                
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertTrue(result.success)  # Should fallback gracefully
                self.assertEqual(result.description, "Screenshot content")
        finally:
            image_patcher.stop()
    
    def test_api_response_with_null_content(self):
        """Test handling of API response with null content."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with null content
            null_content_response = {
                "choices": [
                    {
                        "message": {
                            "content": None
                        }
                    }
                ]
            }
            
            with patch.object(self.analyzer.session, 'post') as mock_post:
                mock_post.return_value.json.return_value = null_content_response
                mock_post.return_value.raise_for_status.return_value = None
                
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertTrue(result.success)  # Should fallback gracefully
                self.assertEqual(result.description, "Screenshot content")
        finally:
            image_patcher.stop()
    
    def test_api_response_with_empty_content(self):
        """Test handling of API response with empty content."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with empty content
            empty_content_response = {
                "choices": [
                    {
                        "message": {
                            "content": "   "  # Only whitespace
                        }
                    }
                ]
            }
            
            with patch.object(self.analyzer.session, 'post') as mock_post:
                mock_post.return_value.json.return_value = empty_content_response
                mock_post.return_value.raise_for_status.return_value = None
                
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertTrue(result.success)  # Should fallback gracefully
                self.assertEqual(result.description, "Screenshot content")
        finally:
            image_patcher.stop()
    
    def test_non_string_api_content(self):
        """Test handling of non-string content in API response."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Mock API response with non-string content
            non_string_response = {
                "choices": [
                    {
                        "message": {
                            "content": 123  # Number instead of string
                        }
                    }
                ]
            }
            
            with patch.object(self.analyzer.session, 'post') as mock_post:
                mock_post.return_value.json.return_value = non_string_response
                mock_post.return_value.raise_for_status.return_value = None
                
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertTrue(result.success)  # Should convert and handle gracefully
                self.assertEqual(result.description, "123")
        finally:
            image_patcher.stop()
    
    def test_connection_test_with_401(self):
        """Test connection test with authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'error': {
                'message': 'Invalid API key',
                'type': 'invalid_request_error'
            }
        }
        
        error = requests.exceptions.RequestException("401 Unauthorized")
        error.response = mock_response
        
        with patch.object(self.analyzer.session, 'get', side_effect=error):
            success, message = self.analyzer.test_connection()
            
            self.assertFalse(success)
            self.assertIn("❌", message)
            self.assertIn("Authentication failed", message)
            self.assertIn("Invalid API key", message)
    
    def test_connection_test_success_with_model_check(self):
        """Test successful connection with model availability check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'gpt-4-vision-preview'},
                {'id': 'gpt-4'},
                {'id': 'gpt-3.5-turbo'}
            ]
        }
        
        with patch.object(self.analyzer.session, 'get', return_value=mock_response):
            success, message = self.analyzer.test_connection()
            
            self.assertTrue(success)
            self.assertIn("✅", message)
            self.assertIn("API connection successful", message)
            self.assertIn("gpt-4-vision-preview", message)
            self.assertIn("available", message)
    
    def test_connection_test_success_but_model_unavailable(self):
        """Test successful connection but model not available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'gpt-4'},
                {'id': 'gpt-3.5-turbo'}
            ]
        }
        
        with patch.object(self.analyzer.session, 'get', return_value=mock_response):
            success, message = self.analyzer.test_connection()
            
            self.assertFalse(success)
            self.assertIn("⚠️", message)
            self.assertIn("API connection successful", message)
            self.assertIn("not available", message)
            self.assertIn("Available models include", message)
    
    def test_image_preparation_failure(self):
        """Test handling of image preparation failure."""
        with patch('vision_analyzer.Image.open', side_effect=Exception("Cannot open image")):
            result = self.analyzer.analyze_screenshot(self.test_image_path)
            
            self.assertFalse(result.success)
            self.assertEqual(result.error_message, "Failed to process image file")
            self.assertIn("Could not read, convert, or encode", result.error_details)
            self.assertIn("corrupted or in an unsupported format", result.error_details)
    
    def test_error_tracking_across_retries(self):
        """Test that errors are tracked across multiple retry attempts."""
        image_patcher = self._setup_successful_image_mock()
        
        try:
            # Create different errors for each retry
            errors = [
                requests.exceptions.Timeout("First timeout"),
                requests.exceptions.ConnectionError("Connection failed"),
            ]
            
            with patch.object(self.analyzer.session, 'post', side_effect=errors):
                result = self.analyzer.analyze_screenshot(self.test_image_path)
                
                self.assertFalse(result.success)
                self.assertIn("Failed after 2 attempts", result.error_message)
                self.assertIn("First timeout", result.error_details)
                self.assertIn("Connection failed", result.error_details)
        finally:
            image_patcher.stop()


if __name__ == '__main__':
    unittest.main() 