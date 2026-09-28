"""
AI-powered content validation using Google Gemini API
Ensures users only upload actual cat images and cat audio files
"""

import os
import base64
import tempfile
import json
from typing import Dict, List, Tuple, Optional
from PIL import Image
import requests
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

# Gemini API configuration
GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', None)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

class AIContentValidator:
    """AI-powered content validation for cat images and audio"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
        self.api_url = GEMINI_API_URL
        
    def validate_image_content(self, image_file: UploadedFile) -> Dict:
        """
        Validate that the uploaded image contains a cat using Gemini AI
        
        Args:
            image_file: Django UploadedFile object
            
        Returns:
            Dict with validation results
        """
        if not self.api_key:
            # Check if strict mode is enabled
            strict_mode = getattr(settings, 'AI_VALIDATION_STRICT_MODE', True)
            
            if strict_mode:
                return {
                    'is_valid': False,  # Reject if no API key (strict mode)
                    'confidence': 0.0,
                    'detected_content': 'AI validation required but API key not configured',
                    'warnings': [
                        'AI validation is required but Gemini API key is not configured',
                        'Please configure GEMINI_API_KEY to enable cat detection',
                        'Without AI validation, we cannot verify this image contains a cat'
                    ]
                }
            else:
                return {
                    'is_valid': True,  # Allow if no API key (permissive mode)
                    'confidence': 0.0,
                    'detected_content': 'API key not configured - permissive mode',
                    'warnings': ['AI validation disabled - API key not found']
                }
        
        try:
            # Convert image to base64
            image_file.seek(0)
            image_data = image_file.read()
            image_file.seek(0)  # Reset for further use
            
            # Optimize image size for API (max 4MB recommended)
            optimized_data = self._optimize_image_for_api(image_data)
            image_b64 = base64.b64encode(optimized_data).decode('utf-8')
            
            # Create prompt for cat detection
            prompt = """
            Analyze this image carefully and determine if it contains a cat or cats.
            
            Please respond with a JSON object containing:
            {
                "contains_cat": true/false,
                "confidence": 0.0-1.0,
                "detected_animals": ["list of animals detected"],
                "cat_details": {
                    "breed_guess": "breed if identifiable",
                    "emotion_visible": "yes/no/unclear",
                    "face_visible": "yes/no/partial",
                    "body_visible": "yes/no/partial"
                },
                "image_quality": "excellent/good/fair/poor",
                "reasons": ["reasons for the decision"]
            }
            
            Be very strict - only return contains_cat: true if you are confident this is actually a cat.
            If you see dogs, other animals, humans, objects, or unclear images, return contains_cat: false.
            """
            
            # Make API request
            response = self._make_gemini_request(image_b64, prompt, 'image/jpeg')
            
            if response['success']:
                return self._parse_image_validation_response(response['data'])
            else:
                return {
                    'is_valid': True,  # Allow on API error (fallback)
                    'confidence': 0.0,
                    'detected_content': 'API error',
                    'warnings': [f'AI validation failed: {response["error"]}']
                }
                
        except Exception as e:
            return {
                'is_valid': True,  # Allow on error (fallback)
                'confidence': 0.0,
                'detected_content': 'Validation error',
                'warnings': [f'AI validation error: {str(e)}']
            }
    
    def validate_audio_content(self, audio_file: UploadedFile) -> Dict:
        """
        Validate that the uploaded audio contains cat sounds
        Note: Gemini doesn't directly support audio analysis, so we use metadata analysis
        
        Args:
            audio_file: Django UploadedFile object
            
        Returns:
            Dict with validation results
        """
        try:
            # For now, we'll do basic validation since Gemini doesn't support audio directly
            # In a production system, you'd use specialized audio AI services
            
            file_name = audio_file.name.lower()
            
            # Check for obvious non-cat audio files
            suspicious_keywords = [
                'music', 'song', 'beat', 'track', 'album', 'artist',
                'human', 'voice', 'speech', 'talk', 'conversation',
                'dog', 'bark', 'woof', 'bird', 'chirp', 'tweet'
            ]
            
            warnings = []
            confidence = 0.7  # Default confidence for basic validation
            
            # Check filename for suspicious content
            for keyword in suspicious_keywords:
                if keyword in file_name:
                    warnings.append(f'Filename contains suspicious keyword: {keyword}')
                    confidence = max(0.3, confidence - 0.2)
            
            # Check file size (very small files might not be real audio)
            if audio_file.size < 5000:  # Less than 5KB
                warnings.append('Audio file is very small - might not contain meaningful cat sounds')
                confidence = max(0.4, confidence - 0.2)
            
            # Check if filename suggests cat content
            cat_keywords = ['cat', 'meow', 'purr', 'kitten', 'feline']
            has_cat_keyword = any(keyword in file_name for keyword in cat_keywords)
            
            if has_cat_keyword:
                confidence = min(0.9, confidence + 0.2)
            
            return {
                'is_valid': confidence > 0.5,
                'confidence': confidence,
                'detected_content': 'Audio file (basic validation)',
                'warnings': warnings if warnings else ['Audio validation is basic - please ensure this is cat audio'],
                'suggestions': [
                    'Make sure the audio contains cat sounds like meowing, purring, or other cat vocalizations',
                    'Avoid uploading music, human speech, or other animal sounds',
                    'Clear, high-quality recordings work best for emotion detection'
                ]
            }
            
        except Exception as e:
            return {
                'is_valid': True,  # Allow on error (fallback)
                'confidence': 0.0,
                'detected_content': 'Audio validation error',
                'warnings': [f'Audio validation error: {str(e)}']
            }
    
    def _optimize_image_for_api(self, image_data: bytes) -> bytes:
        """Optimize image size for Gemini API (without strict dimension limits)"""
        try:
            # Open image with PIL
            with Image.open(tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')) as temp_file:
                temp_file.write(image_data)
                temp_file.flush()
                
                with Image.open(temp_file.name) as img:
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Only resize if extremely large (for API efficiency)
                    max_size = 2048  # Increased from 1024
                    if img.width > max_size or img.height > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    # Save optimized image
                    optimized_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    img.save(optimized_temp.name, 'JPEG', quality=90, optimize=True)  # Higher quality
                    
                    with open(optimized_temp.name, 'rb') as f:
                        optimized_data = f.read()
                    
                    # Cleanup
                    os.unlink(temp_file.name)
                    os.unlink(optimized_temp.name)
                    
                    return optimized_data
                    
        except Exception:
            # Return original data if optimization fails
            return image_data
    
    def _make_gemini_request(self, image_b64: str, prompt: str, mime_type: str) -> Dict:
        """Make request to Gemini API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': self.api_key
            }
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_b64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,  # Low temperature for consistent results
                    "topK": 1,
                    "topP": 0.8,
                    "maxOutputTokens": 1024
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    text_response = data['candidates'][0]['content']['parts'][0]['text']
                    return {'success': True, 'data': text_response}
                else:
                    return {'success': False, 'error': 'No response from API'}
            else:
                return {'success': False, 'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_image_validation_response(self, response_text: str) -> Dict:
        """Parse Gemini API response for image validation"""
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()
            
            # Remove markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            contains_cat = data.get('contains_cat', False)
            confidence = float(data.get('confidence', 0.0))
            detected_animals = data.get('detected_animals', [])
            cat_details = data.get('cat_details', {})
            reasons = data.get('reasons', [])
            
            # Determine if valid (strict validation)
            is_valid = contains_cat and confidence >= 0.7
            
            warnings = []
            if not contains_cat:
                if detected_animals:
                    warnings.append(f'Detected non-cat animals: {", ".join(detected_animals)}')
                else:
                    warnings.append('No cat detected in image')
            
            if confidence < 0.7:
                warnings.append(f'Low confidence in cat detection: {confidence:.1%}')
            
            return {
                'is_valid': is_valid,
                'confidence': confidence,
                'detected_content': f'Cat: {contains_cat}, Animals: {detected_animals}',
                'warnings': warnings,
                'details': {
                    'contains_cat': contains_cat,
                    'detected_animals': detected_animals,
                    'cat_details': cat_details,
                    'reasons': reasons
                }
            }
            
        except json.JSONDecodeError:
            # Fallback: simple text analysis
            response_lower = response_text.lower()
            contains_cat = 'cat' in response_lower and 'no cat' not in response_lower
            
            return {
                'is_valid': contains_cat,
                'confidence': 0.6 if contains_cat else 0.3,
                'detected_content': 'Text analysis fallback',
                'warnings': ['Could not parse AI response as JSON'],
                'details': {'raw_response': response_text}
            }
        
        except Exception as e:
            return {
                'is_valid': False,
                'confidence': 0.0,
                'detected_content': 'Parse error',
                'warnings': [f'Error parsing AI response: {str(e)}']
            }

# Global validator instance
ai_validator = AIContentValidator()

def validate_cat_image(image_file: UploadedFile) -> Dict:
    """Convenience function for image validation"""
    return ai_validator.validate_image_content(image_file)

def validate_cat_audio(audio_file: UploadedFile) -> Dict:
    """Convenience function for audio validation"""
    return ai_validator.validate_audio_content(audio_file)