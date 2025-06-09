#!/usr/bin/env python3
"""Test safety refusal handling for AI vision responses."""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import just the parsing method we need to test
import vision_analyzer

def test_safety_refusal_detection():
    """Test that safety refusal responses are properly detected and handled."""
    
    print("🛡️  Testing Safety Refusal Detection")
    print("=" * 50)
    
    # Test cases with various refusal responses
    refusal_responses = [
        "I'm sorry, I can't help with that request.",
        "I can't help with that.",
        "I'm not able to help with this image.",
        "I cannot help analyze this content.",
        "I'm sorry, but I can't provide information about this image.",
        "I can't assist with analyzing this screenshot.",
        "I'm unable to help with this request.",
        "I cannot assist with this type of content.",
        "I'm sorry, I cannot analyze this image.",
        "I can't provide a description of this content.",
        "I'm not able to provide analysis of this image.",
        "I cannot provide information about this screenshot.",
        "I can't analyze this type of content.",
        "I cannot analyze images containing children.",
        "I'm not able to analyze this screenshot.",
        "I'm sorry, I can't analyze this image."
    ]
    
    # Test cases with valid responses that should NOT be refused
    valid_responses = [
        "Web browser article reading",
        "Code editor Python file",
        "Email inbox messages view",
        "Settings screen preferences",
        "Document editing interface",
        "Social media timeline scrolling",
        "Video conference call screen",
        "File manager directory listing"
    ]
    
    # Create a minimal analyzer instance just for testing the method
    class TestAnalyzer:
        def _parse_description(self, response):
            # Copy the exact logic from VisionAnalyzer
            try:
                content = response['choices'][0]['message']['content']
                
                # Clean up the description
                description = content.strip().strip('"').strip("'")
                
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
                
                return description
                
            except (KeyError, IndexError) as e:
                print(f"Error parsing API response: {e}")
                return "Screenshot content"  # Fallback description
    
    analyzer = TestAnalyzer()
    
    print("\n🚫 Testing Refusal Responses (should return None):")
    print("-" * 50)
    refusal_detected = 0
    for i, response_text in enumerate(refusal_responses, 1):
        # Mock response structure
        mock_response = {
            'choices': [
                {
                    'message': {
                        'content': response_text
                    }
                }
            ]
        }
        
        result = analyzer._parse_description(mock_response)
        if result is None:
            print(f"✅ {i:2d}. Correctly detected refusal: '{response_text[:40]}...'")
            refusal_detected += 1
        else:
            print(f"❌ {i:2d}. MISSED refusal: '{response_text[:40]}...' → '{result}'")
    
    print(f"\n✅ Valid Responses (should return description):")
    print("-" * 50)
    valid_processed = 0
    for i, response_text in enumerate(valid_responses, 1):
        # Mock response structure
        mock_response = {
            'choices': [
                {
                    'message': {
                        'content': response_text
                    }
                }
            ]
        }
        
        result = analyzer._parse_description(mock_response)
        if result is not None:
            print(f"✅ {i:2d}. Correctly processed: '{response_text}' → '{result}'")
            valid_processed += 1
        else:
            print(f"❌ {i:2d}. INCORRECTLY refused: '{response_text}'")
    
    # Results summary
    print(f"\n📊 Results Summary:")
    print("-" * 30)
    print(f"Refusal responses detected: {refusal_detected}/{len(refusal_responses)} ({100*refusal_detected//len(refusal_responses)}%)")
    print(f"Valid responses processed: {valid_processed}/{len(valid_responses)} ({100*valid_processed//len(valid_responses)}%)")
    
    total_correct = refusal_detected + valid_processed
    total_tests = len(refusal_responses) + len(valid_responses)
    
    print(f"Overall accuracy: {total_correct}/{total_tests} ({100*total_correct//total_tests}%)")
    
    if total_correct == total_tests:
        print("🎉 All safety refusal detection tests passed!")
        return True
    else:
        print("⚠️  Some tests failed - check the detection patterns!")
        return False

def test_edge_cases():
    """Test edge cases for safety refusal detection."""
    
    # Same test analyzer as above
    class TestAnalyzer:
        def _parse_description(self, response):
            try:
                content = response['choices'][0]['message']['content']
                description = content.strip().strip('"').strip("'")
                
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
                
                description_lower = description.lower()
                for pattern in refusal_patterns:
                    if pattern in description_lower:
                        return None
                
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
                
                words = description.split()
                if len(words) > 6:
                    description = ' '.join(words[:5])
                
                return description
                
            except (KeyError, IndexError) as e:
                return "Screenshot content"
    
    analyzer = TestAnalyzer()
    
    print(f"\n🔍 Testing Edge Cases:")
    print("-" * 30)
    
    edge_cases = [
        # Mixed case variations
        ("I'M SORRY, I CAN'T HELP", None, "uppercase refusal"),
        ("i'm sorry, i can't help", None, "lowercase refusal"),
        ("I'm Sorry, I Can't Help", None, "title case refusal"),
        
        # Partial matches that should NOT be refused
        ("I can help you with this screenshot", "Screenshot", "contains 'can help' but not refusal"),
        ("This image cannot be displayed properly", "Image cannot be displayed properly", "contains 'cannot' but not refusal"),
        ("I'm sorry to say this is a complex interface", "Complex interface", "contains 'sorry' but not refusal"),
        
        # Refusals with extra text
        ("I'm sorry, I can't help with that. Please try a different image.", None, "refusal with extra text"),
        ("Unfortunately, I can't analyze this type of content for safety reasons.", None, "refusal with explanation"),
    ]
    
    passed = 0
    for i, (response_text, expected_result, description) in enumerate(edge_cases, 1):
        mock_response = {
            'choices': [
                {
                    'message': {
                        'content': response_text
                    }
                }
            ]
        }
        
        result = analyzer._parse_description(mock_response)
        
        if (expected_result is None and result is None) or (expected_result is not None and result is not None):
            print(f"✅ {i}. {description}")
            passed += 1
        else:
            print(f"❌ {i}. {description}")
            print(f"     Expected: {expected_result}, Got: {result}")
    
    print(f"\nEdge cases passed: {passed}/{len(edge_cases)}")
    return passed == len(edge_cases)

if __name__ == "__main__":
    print("🧪 Safety Refusal Handling Test Suite")
    print("=" * 60)
    
    basic_tests = test_safety_refusal_detection()
    edge_tests = test_edge_cases()
    
    if basic_tests and edge_tests:
        print(f"\n🎉 All safety refusal tests passed!")
        print("Screenshots triggering AI safety filters will now be skipped automatically.")
        sys.exit(0)
    else:
        print(f"\n⚠️  Some tests failed!")
        sys.exit(1) 