"""
Gemini AI-powered cat emotion prediction
Uses Google Gemini to analyze cat images and predict emotions
"""

import os
import base64
import requests
from typing import Dict, Optional
from PIL import Image
from django.conf import settings


class GeminiEmotionPredictor:
    """Use Gemini AI to predict cat emotions from images"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
        # Using gemini-2.0-flash: 60 RPM, 1500 RPD (vs 2.5-flash: 10 RPM, 250 RPD)
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        # Primary emotions that match your TensorFlow model
        self.emotions = ['Angry', 'Disgusted', 'Happy', 'Normal', 'Sad', 'Scared', 'Surprised']
        # Extended emotions for comprehensive analysis
        self.extended_emotions = {
            'angry': 'Angry', 'anger': 'Angry', 'mad': 'Angry', 'aggressive': 'Angry',
            'happy': 'Happy', 'joy': 'Happy', 'playful': 'Happy', 'content': 'Happy',
            'sad': 'Sad', 'depressed': 'Sad', 'unhappy': 'Sad',
            'scared': 'Scared', 'fear': 'Scared', 'afraid': 'Scared', 'frightened': 'Scared',
            'normal': 'Normal', 'neutral': 'Normal', 'calm': 'Normal', 'relaxed': 'Normal',
            'surprised': 'Surprised', 'shock': 'Surprised', 'startled': 'Surprised',
            'disgusted': 'Disgusted', 'disgust': 'Disgusted',
            # Behavioral states (map to closest primary emotion)
            'defence': 'Angry', 'defense': 'Angry', 'fighting': 'Angry', 'fight': 'Angry',
            'hunting': 'Normal', 'hunt': 'Normal', 'huntingmind': 'Normal',
            'mating': 'Normal', 'mate': 'Normal',
            'mother': 'Normal', 'mothercall': 'Normal',
            'pain': 'Sad', 'paining': 'Sad', 'hurt': 'Sad',
            'resting': 'Normal', 'rest': 'Normal', 'sleep': 'Normal',
            'warning': 'Scared', 'warn': 'Scared', 'alert': 'Scared'
        }
    
    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        return self.api_key is not None
    
    def predict_emotion(self, image_path: str) -> Optional[Dict]:
        """
        Predict cat emotion using Gemini AI
        
        Args:
            image_path: Path to the cat image
            
        Returns:
            Dict with prediction results or None if API unavailable
        """
        if not self.is_available():
            print("[GEMINI] API key not available")
            return None
        
        print(f"[GEMINI] Starting prediction for: {image_path}")
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()
            
            print(f"[GEMINI] Image loaded: {len(image_data)} bytes")
            
            # Optimize image size
            image_data = self._optimize_image(image_data)
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            print(f"[GEMINI] Image optimized and encoded: {len(image_b64)} chars")
            
            # Create detailed prompt for emotion analysis
            prompt = """
You are an expert feline behavior analyst AI system trained in recognizing cat emotional and instinctual states from images.

Your task is to carefully analyze the provided cat image and classify it into ONE of the following categories:

Allowed Emotion Classes (Choose ONLY one):
- Angry
- Defence
- Fighting
- Happy
- HuntingMind
- Mating
- MotherCall
- Paining
- Resting
- Warning

--------------------------------------------------
ANALYSIS INSTRUCTIONS
--------------------------------------------------

Step 1: Analyze Physical Indicators
- Ear position (forward, sideways, flattened, backward)
- Eye shape (wide, relaxed, squinting)
- Pupil size (normal, dilated)
- Mouth (closed, open, hissing, teeth visible)
- Whisker direction
- Tail posture (raised, puffed, low, curved)
- Body posture (relaxed, crouched, arched back, tense)
- Muscle tension
- Presence of another cat (interaction signs)

Step 2: Behavioral Interpretation

Emotion Guidelines:

Angry → Flattened ears, intense stare, tense body, possible growling.

Defence → Low body posture, ears partially back, cautious alert stance.

Fighting → Direct aggression toward another cat, claws visible, biting or attacking.

Happy → Relaxed eyes, upright tail, playful or content body language.

HuntingMind → Focused stare, crouched stalking posture, forward ears.

Mating → Mating posture, tail positioned to side, submissive stance.

MotherCall → Vocalizing posture, protective stance, searching behavior.

Paining → Squinting eyes, withdrawn body, abnormal posture, discomfort signs.

Resting → Calm lying posture, relaxed muscles, half-closed eyes.

Warning → Hissing, raised paw, puffed tail, arched back.

Step 3:
If the image quality is unclear, blurred, or emotion cannot be confidently determined, return "Resting" only if relaxed, otherwise choose the most visually supported category.

--------------------------------------------------
STRICT OUTPUT FORMAT (JSON ONLY)
--------------------------------------------------

{
    "predicted_emotion": "",
    "confidence_score": 0-100,
    "visual_evidence": {
        "ear_position": "",
        "eye_expression": "",
        "body_posture": "",
        "tail_posture": "",
        "aggression_signs": ""
    }
}

Rules:
- Output ONLY valid JSON.
- Do NOT include explanation outside JSON.
- Do NOT add markdown formatting.
- Do NOT add extra commentary.
- Confidence must be an integer between 0 and 100.
- predicted_emotion must be EXACTLY one of: Angry, Defence, Fighting, Happy, HuntingMind, Mating, MotherCall, Paining, Resting, Warning
"""
            
            # Make API request
            print("[GEMINI] Sending request to API...")
            response = self._make_gemini_request(image_b64, prompt)
            
            if response['success']:
                print("[GEMINI] API response received successfully")
                result = self._parse_emotion_response(response['data'])
                if result:
                    print(f"[GEMINI] Prediction: {result['predicted_emotion']} ({result['confidence']:.1f}%)")
                else:
                    print("[GEMINI] Failed to parse response")
                return result
            else:
                print(f"[GEMINI] API error: {response['error']}")
                return None
                
        except Exception as e:
            print(f"[GEMINI] Prediction error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _optimize_image(self, image_data: bytes) -> bytes:
        """Optimize image for API"""
        try:
            import tempfile
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            # Open and resize if needed
            with Image.open(temp_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                max_size = 1024
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Save optimized
                optimized_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                img.save(optimized_temp.name, 'JPEG', quality=85, optimize=True)
                
                with open(optimized_temp.name, 'rb') as f:
                    optimized_data = f.read()
                
                # Cleanup
                os.unlink(temp_path)
                os.unlink(optimized_temp.name)
                
                return optimized_data
        except Exception:
            return image_data
    
    def _make_gemini_request(self, image_b64: str, prompt: str) -> Dict:
        """Make request to Gemini API"""
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            url = f"{self.api_url}?key={self.api_key}"
            
            print(f"[GEMINI] API URL: {self.api_url}")
            print(f"[GEMINI] Payload size: {len(image_b64)} chars")
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_b64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "application/json"
                }
            }
            
            print("[GEMINI] Sending POST request...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"[GEMINI] Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    text_response = data['candidates'][0]['content']['parts'][0]['text']
                    print(f"[GEMINI] Response text length: {len(text_response)}")
                    return {'success': True, 'data': text_response}
                else:
                    error_msg = f'No candidates in response. Full response: {str(data)[:500]}'
                    print(f"[GEMINI] {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'API error: {response.status_code} - {response.text[:500]}'
                print(f"[GEMINI] {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f'Exception: {str(e)}'
            print(f"[GEMINI] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _parse_emotion_response(self, response_text: str) -> Optional[Dict]:
        """Parse Gemini's emotion prediction response"""
        try:
            import json
            
            # Clean response
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            primary_emotion = data.get('predicted_emotion', 'Resting')
            confidence_score = int(data.get('confidence_score', 0))
            visual_evidence = data.get('visual_evidence', {})
            
            # Normalize emotion name to match TensorFlow model
            emotion_mapping = {
                'Angry': 'Angry',
                'Defence': 'Scared',  # Map to closest TF emotion
                'Fighting': 'Angry',
                'Happy': 'Happy',
                'HuntingMind': 'Normal',
                'Mating': 'Normal',
                'MotherCall': 'Normal',
                'Paining': 'Sad',
                'Resting': 'Normal',
                'Warning': 'Scared'
            }
            
            # Map to TensorFlow emotion
            tf_emotion = emotion_mapping.get(primary_emotion, 'Normal')
            
            # Convert confidence to percentage (0-100 to 0.0-100.0)
            confidence_pct = float(confidence_score)
            
            # Create all_predictions based on the single prediction
            all_predictions = {
                'Angry': 0.0,
                'Disgusted': 0.0,
                'Happy': 0.0,
                'Normal': 0.0,
                'Sad': 0.0,
                'Scared': 0.0,
                'Surprised': 0.0
            }
            all_predictions[tf_emotion] = confidence_pct
            
            # Distribute remaining confidence
            remaining = 100.0 - confidence_pct
            other_emotions = [e for e in all_predictions.keys() if e != tf_emotion]
            if other_emotions:
                per_emotion = remaining / len(other_emotions)
                for emo in other_emotions:
                    all_predictions[emo] = per_emotion
            
            return {
                'predicted_emotion': tf_emotion,
                'confidence': round(confidence_pct, 1),
                'all_predictions': all_predictions,
                'reasoning': f"Gemini detected: {primary_emotion}. Visual evidence: {visual_evidence}",
                'key_features': [
                    f"Ear position: {visual_evidence.get('ear_position', 'N/A')}",
                    f"Eye expression: {visual_evidence.get('eye_expression', 'N/A')}",
                    f"Body posture: {visual_evidence.get('body_posture', 'N/A')}",
                    f"Tail posture: {visual_evidence.get('tail_posture', 'N/A')}"
                ],
                'detection_method': 'gemini_ai',
                'gemini_original_emotion': primary_emotion,
                'gemini_analysis': data
            }
            
        except json.JSONDecodeError as e:
            print(f"[GEMINI] JSON parse error: {e}")
            print(f"[GEMINI] Response: {response_text[:200]}")
            return None
        except Exception as e:
            print(f"[GEMINI] Parse error: {e}")
            return None


# Global instance
_gemini_predictor = None

def get_gemini_predictor() -> GeminiEmotionPredictor:
    """Get or create Gemini predictor instance"""
    global _gemini_predictor
    if _gemini_predictor is None:
        _gemini_predictor = GeminiEmotionPredictor()
    return _gemini_predictor
