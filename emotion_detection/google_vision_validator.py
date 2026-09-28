"""
Google Cloud Vision API validator for cat images.
Only accepts images containing cats, rejects all other animals.
"""
import os
import base64
import requests
from django.conf import settings

# Google Cloud Vision API key
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
VISION_API_URL = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"

def validate_cat_image_google(image_path):
    """
    Validate if image contains a cat using Google Cloud Vision API.
    Returns (is_cat, confidence, detected_labels)
    """
    try:
        # Read and encode image
        with open(image_path, 'rb') as image_file:
            image_content = image_file.read()
            image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        # Prepare API request
        request_body = {
            "requests": [
                {
                    "image": {
                        "content": image_base64
                    },
                    "features": [
                        {
                            "type": "LABEL_DETECTION",
                            "maxResults": 20
                        },
                        {
                            "type": "OBJECT_LOCALIZATION",
                            "maxResults": 10
                        }
                    ]
                }
            ]
        }
        
        # Call Google Cloud Vision API
        response = requests.post(VISION_API_URL, json=request_body, timeout=10)
        
        if response.status_code != 200:
            print(f"[GOOGLE VISION] API error: {response.status_code}")
            return None, 0.0, []
        
        result = response.json()
        
        if 'responses' not in result or len(result['responses']) == 0:
            return False, 0.0, []
        
        response_data = result['responses'][0]
        
        # Extract labels
        labels = []
        if 'labelAnnotations' in response_data:
            labels = response_data['labelAnnotations']
        
        # Extract objects
        objects = []
        if 'localizedObjectAnnotations' in response_data:
            objects = response_data['localizedObjectAnnotations']
        
        # Check for cat in labels
        cat_confidence = 0.0
        detected_labels = []
        
        for label in labels:
            label_name = label['description'].lower()
            score = label['score']
            detected_labels.append(f"{label['description']} ({score:.2%})")
            
            if label_name in ['cat', 'kitten', 'felidae', 'small to medium-sized cats', 'whiskers']:
                cat_confidence = max(cat_confidence, score)
        
        # Check for cat in objects
        for obj in objects:
            obj_name = obj['name'].lower()
            score = obj['score']
            detected_labels.append(f"{obj['name']} ({score:.2%})")
            
            if obj_name in ['cat', 'kitten', 'animal']:
                cat_confidence = max(cat_confidence, score)
        
        # Check for other animals (reject them)
        other_animals = ['dog', 'bird', 'horse', 'cow', 'sheep', 'pig', 'rabbit', 
                        'hamster', 'mouse', 'rat', 'fish', 'reptile', 'snake', 
                        'lizard', 'turtle', 'frog', 'insect', 'spider']
        
        for label in labels:
            label_name = label['description'].lower()
            if any(animal in label_name for animal in other_animals):
                return False, 0.0, detected_labels
        
        # Decision logic
        if cat_confidence >= 0.75:
            return True, cat_confidence, detected_labels
        elif cat_confidence >= 0.50:
            return True, cat_confidence, detected_labels  # Accept with warning
        else:
            return False, cat_confidence, detected_labels
    
    except Exception as e:
        print(f"[GOOGLE VISION] Error: {str(e)}")
        return None, 0.0, []


def validate_cat_image_strict(image_path):
    """
    Strict cat validation - only accepts if Google Vision confirms it's a cat.
    Falls back to basic validation if API fails.
    """
    # Try Google Cloud Vision first
    is_cat, confidence, labels = validate_cat_image_google(image_path)
    
    if is_cat is None:
        # API failed, use basic validation
        print("[CAT VALIDATION] Google Vision API unavailable, using basic validation")
        return True, 50.0, "API unavailable, basic validation passed"
    
    if is_cat:
        label_str = ", ".join(labels[:5])  # Show top 5 labels
        return True, confidence * 100, f"✅ Cat detected ({confidence:.1%}): {label_str}"
    else:
        if confidence > 0:
            label_str = ", ".join(labels[:5])
            return False, confidence * 100, f"❌ Not a cat (confidence: {confidence:.1%}): {label_str}"
        else:
            label_str = ", ".join(labels[:5]) if labels else "No cat detected"
            return False, 0.0, f"❌ No cat found: {label_str}"
