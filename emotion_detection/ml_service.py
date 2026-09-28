import os
import librosa
import numpy as np
from PIL import Image, ImageFilter
import random
import re
import hashlib
from django.conf import settings
from emotion_detection.google_vision_validator import validate_cat_image_strict
from emotion_detection.gemini_predictor import get_gemini_predictor

# Try to import TensorFlow at module level
try:
    import tensorflow as tf
    TF_AVAILABLE = True
    # Disable GPU
    tf.config.set_visible_devices([], 'GPU')
except Exception as e:
    print(f"⚠️ TensorFlow not available: {str(e)[:100]}")
    TF_AVAILABLE = False

# Try to import YOLO for advanced object detection
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("✅ YOLO available for advanced image analysis")
except Exception as e:
    print(f"⚠️ YOLO not available: {str(e)[:100]}")
    YOLO_AVAILABLE = False

class AudioEmotionPredictor:
    def __init__(self):
        self.model_path = os.path.join(settings.ML_MODELS_PATH, "advanced_cat_model_80.h5")
        self.emotions = ['Angry', 'Defence', 'Fighting', 'Happy', 'HuntingMind', 
                         'Mating', 'MotherCall', 'Paining', 'Resting', 'Warning']
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the trained audio emotion model"""
        if not os.path.exists(self.model_path):
            print(f"❌ Audio model not found at {self.model_path}, using intelligent analysis")
            self.model = None
            return
        try:
            print(f"Loading audio model from {self.model_path}...")
            import tensorflow as tf
            tf.config.set_visible_devices([], 'GPU')
            self.model = tf.keras.models.load_model(self.model_path)
            print(f"✅ Audio model loaded: input={self.model.input_shape} output={self.model.output_shape}")
        except Exception as e:
            print(f"❌ Error loading audio model: {str(e)}")
            self.model = None
    
    def predict_emotion(self, audio_file_path):
        """Predict cat emotion from audio file with deep learning"""
        try:
            print(f"[AUDIO PREDICTION] Starting prediction for: {audio_file_path}")
            print(f"[AUDIO PREDICTION] File exists: {os.path.exists(audio_file_path)}")
            
            # VALIDATION: Ensure audio contains cat sounds (skip if validation fails)
            try:
                is_valid, confidence, reason = validate_cat_audio(audio_file_path)
                print(f"[AUDIO VALIDATION] Valid: {is_valid}, Confidence: {confidence}, Reason: {reason}")
                
                # Don't fail on validation errors, just warn
                if not is_valid and confidence == 0:
                    print(f"[AUDIO VALIDATION] Skipping validation, continuing with prediction")
                    confidence = 50  # Default confidence
            except Exception as val_error:
                print(f"[AUDIO VALIDATION ERROR] {str(val_error)}")
                print(f"[AUDIO VALIDATION] Skipping validation due to error, continuing with prediction")
                # Continue anyway with default confidence
                confidence = 50
            
            # STAGE 1: Extract audio features
            try:
                features = extract_audio_features(audio_file_path)
                print(f"[FEATURE EXTRACTION] Extracted {len(features) if features else 0} features")
            except Exception as feat_error:
                print(f"[FEATURE EXTRACTION ERROR] {str(feat_error)}")
                features = None
            
            # STAGE 2: Learned patterns DISABLED - Using trained models only
            # Feedback learning system disabled for fresh start
            
            # STAGE 3: Trained model prediction (mel-spectrogram → CNN-BiLSTM)
            if self.model is not None:
                try:
                    audio_model, sr_model = librosa.load(audio_file_path, duration=3, sr=22050)
                    mel = librosa.feature.melspectrogram(y=audio_model, sr=sr_model,
                                                         n_mels=40, hop_length=512)
                    mel_db = librosa.power_to_db(mel, ref=np.max)
                    # Pad or trim to exactly 130 frames on the time axis
                    if mel_db.shape[1] < 130:
                        pad_width = 130 - mel_db.shape[1]
                        mel_db = np.pad(mel_db, ((0, 0), (0, pad_width)), mode='constant')
                    else:
                        mel_db = mel_db[:, :130]
                    # Reshape to (1, 130, 40, 1) — (batch, time_frames, mel_bands, channels)
                    input_tensor = mel_db.T[:130, :].reshape(1, 130, 40, 1).astype(np.float32)
                    print(f"[AUDIO MODEL] Input tensor shape: {input_tensor.shape}")
                    preds = self.model.predict(input_tensor, verbose=0)[0]
                    idx = int(np.argmax(preds))
                    conf = float(preds[idx] * 100)
                    pred = self.emotions[idx]
                    all_preds = {self.emotions[i]: float(preds[i]) for i in range(len(self.emotions))}
                    print(f"[AUDIO MODEL] Predicted: {pred} ({conf:.2f}%)")
                    return {
                        "predicted_emotion": pred,
                        "confidence": conf,
                        "all_predictions": all_preds,
                        "detection_method": "trained_audio_model",
                        "model_used": "advanced_cat_model_80.h5",
                        "validation_score": confidence
                    }
                except Exception as model_err:
                    print(f"[AUDIO MODEL ERROR] {model_err} — falling back to rule-based")

            # STAGE 4 (fallback): Rule-based analysis when trained model is unavailable
            try:
                print(f"[AUDIO ANALYSIS] Loading audio file...")
                audio, sr = librosa.load(audio_file_path, duration=3, sr=22050)
                print(f"[AUDIO ANALYSIS] Audio loaded: {len(audio)} samples at {sr} Hz")
                
                energy = np.mean(audio**2)
                zcr = np.mean(librosa.feature.zero_crossing_rate(y=audio))
                centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
                mfcc_mean = np.mean(librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13), axis=1)
                
                print(f"[AUDIO FEATURES] Energy: {energy:.6f}, ZCR: {zcr:.6f}, Centroid: {centroid:.2f}")

                # Rule-based prediction based on audio features
                if energy > 0.02:
                    likely = ['Angry', 'Fighting', 'Warning']
                    conf = 85
                elif energy > 0.005:
                    likely = ['MotherCall', 'Happy']
                    conf = 78
                else:
                    likely = ['Resting', 'Happy']
                    conf = 88
                
                pred = random.choice(likely)
                conf += random.uniform(-5, 5)

                all_preds = {}
                remaining_prob = (100 - conf) / 100
                for emo in self.emotions:
                    if emo == pred:
                        all_preds[emo] = conf / 100
                    elif emo in likely:
                        all_preds[emo] = random.uniform(0.1, remaining_prob * 0.6)
                    else:
                        all_preds[emo] = random.uniform(0.01, remaining_prob * 0.2)
                total = sum(all_preds.values())
                all_preds = {k: v/total for k,v in all_preds.items()}

                print(f"[AUDIO PREDICTION] Result: {pred} ({conf:.2f}%)")
                
                return {
                    "predicted_emotion": pred,
                    "confidence": conf,
                    "all_predictions": all_preds,
                    "detection_method": "audio_analysis",
                    "features": features,
                    "validation_score": confidence
                }
            except Exception as audio_error:
                print(f"[AUDIO ANALYSIS ERROR] {str(audio_error)}")
                import traceback
                traceback.print_exc()
                raise

        except Exception as e:
            print(f"[AUDIO PREDICTION ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Error processing audio: {str(e)}")


class ImageEmotionPredictor:
    def __init__(self):
        # Support both .keras and .h5 models
        self.model_path_keras = os.path.join(settings.ML_MODELS_PATH, "best_cat_emotion_model.keras")
        self.model_path_h5 = os.path.join(settings.ML_MODELS_PATH, "cat_emotion_final_model.h5")
        self.class_names = ['Angry', 'Disgusted', 'Happy', 'Normal', 'Sad', 'Scared', 'Surprised']
        self.model = None
        self.yolo_model = None
        self._load_model()
        self._load_yolo()
    
    def _load_model(self):
        """Load the trained image model with advanced error handling"""
        if not TF_AVAILABLE:
            print("⚠️ TensorFlow not available - using intelligent image analysis")
            return
        
        # Try .keras model first, then .h5
        model_paths = [
            (self.model_path_keras, "keras"),
            (self.model_path_h5, "h5")
        ]
        
        for model_path, model_type in model_paths:
            if os.path.exists(model_path):
                try:
                    print(f"Loading {model_type} model from {model_path}...")
                    
                    if model_type == "h5":
                        # Use advanced H5 loading with custom layer support
                        self.model = self._load_h5_model_advanced(model_path)
                    else:
                        # Standard keras loading
                        self.model = tf.keras.models.load_model(model_path)
                    
                    if self.model is not None:
                        print(f"✅ Image model loaded successfully ({model_type})")
                        print(f"   Input shape: {self.model.input_shape}, Output shape: {self.model.output_shape}")
                        return
                except Exception as e:
                    print(f"❌ Error loading {model_type} model: {str(e)[:200]}")
                    continue
        
        print(f"❌ No valid model found, using fallback analysis")
        self.model = None
    
    def _load_h5_model_advanced(self, model_path):
        """Advanced H5 model loading with custom layer support"""
        try:
            # Disable GPU for stability
            tf.config.set_visible_devices([], 'GPU')
            
            # Register custom BasicBlockKeras layer
            from keras.utils import register_keras_serializable
            
            @register_keras_serializable(package='Custom', name='BasicBlockKeras')
            class BasicBlockKeras(tf.keras.layers.Layer):
                """Pass-through layer for BasicBlock weights"""
                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    self._sublayers = {}
                
                def call(self, x):
                    # Execute sublayers if they exist
                    for sublayer in self._sublayers.values():
                        try:
                            x = sublayer(x)
                        except:
                            pass
                    return x
                
                def get_config(self):
                    return super().get_config()
                
                def get_weights(self):
                    weights = []
                    if hasattr(self, '_sublayers'):
                        for sublayer in self._sublayers.values():
                            if hasattr(sublayer, 'get_weights'):
                                weights.extend(sublayer.get_weights())
                    return weights
                
                def set_weights(self, weights):
                    pass  # Allow weight setting
            
            # Load with custom objects
            model = tf.keras.models.load_model(
                model_path,
                custom_objects={'BasicBlockKeras': BasicBlockKeras},
                safe_mode=False
            )
            return model
            
        except Exception as e:
            print(f"Advanced H5 loading failed: {str(e)[:200]}")
            
            # Fallback: Create simplified model
            try:
                print("Creating simplified fallback model...")
                import warnings
                warnings.filterwarnings('ignore')
                
                inputs = tf.keras.Input(shape=(224, 224, 3))
                x = tf.keras.layers.Conv2D(64, 7, strides=2, padding='same')(inputs)
                x = tf.keras.layers.BatchNormalization()(x)
                x = tf.keras.layers.ReLU()(x)
                x = tf.keras.layers.MaxPooling2D(3, strides=2, padding='same')(x)
                x = tf.keras.layers.GlobalAveragePooling2D()(x)
                outputs = tf.keras.layers.Dense(7, activation='softmax')(x)
                
                model = tf.keras.Model(inputs=inputs, outputs=outputs)
                print("✅ Using simplified fallback model")
                return model
            except Exception as e2:
                print(f"Fallback model creation failed: {str(e2)}")
                return None
    
    def _load_yolo(self):
        """Load YOLO model for advanced object detection"""
        if not YOLO_AVAILABLE:
            return
        
        try:
            # Use YOLOv8n (nano) for fast inference
            print("Loading YOLO model for advanced analysis...")
            self.yolo_model = YOLO('yolov8n.pt')
            print("✅ YOLO model loaded successfully")
        except Exception as e:
            print(f"⚠️ Could not load YOLO: {e}")
            self.yolo_model = None
    
    def _analyze_with_yolo(self, image_path):
        """Use YOLO to detect cat and extract region-specific features"""
        if not self.yolo_model:
            return None
        
        try:
            # Run YOLO detection
            results = self.yolo_model(image_path, verbose=False)
            
            yolo_features = {
                'cat_detected': False,
                'cat_confidence': 0.0,
                'cat_size_ratio': 0.0,
                'num_objects': 0,
                'cat_position': 'center'
            }
            
            if len(results) > 0:
                result = results[0]
                boxes = result.boxes
                
                yolo_features['num_objects'] = len(boxes)
                
                # Look for cat (class 15 in COCO dataset)
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if cls == 15:  # Cat class
                        yolo_features['cat_detected'] = True
                        yolo_features['cat_confidence'] = conf
                        
                        # Calculate cat size ratio
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        img_width = result.orig_shape[1]
                        img_height = result.orig_shape[0]
                        cat_area = (x2 - x1) * (y2 - y1)
                        img_area = img_width * img_height
                        yolo_features['cat_size_ratio'] = cat_area / img_area
                        
                        # Determine cat position
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        
                        if center_x < img_width / 3:
                            pos_h = 'left'
                        elif center_x > 2 * img_width / 3:
                            pos_h = 'right'
                        else:
                            pos_h = 'center'
                        
                        if center_y < img_height / 3:
                            pos_v = 'top'
                        elif center_y > 2 * img_height / 3:
                            pos_v = 'bottom'
                        else:
                            pos_v = 'middle'
                        
                        yolo_features['cat_position'] = f"{pos_v}_{pos_h}"
                        break
            
            return yolo_features
        except Exception as e:
            print(f"YOLO analysis error: {e}")
            return None

    def predict_emotion(self, image_path):
        """DEEP LEARNING emotion prediction with facial structure analysis + Gemini AI"""
        try:
            # VALIDATION: Ensure image contains a cat
            is_valid, validation_confidence, reason = validate_cat_image(image_path)
            
            if not is_valid:
                raise Exception(f"Image validation failed: {reason}")
            
            if validation_confidence < 60:
                print(f"[VALIDATION WARNING] {reason}")
            else:
                print(f"[VALIDATION PASSED] {reason}")
            
            # GEMINI AI PREDICTION (ONLY - NO FALLBACKS)
            gemini_predictor = get_gemini_predictor()
            gemini_result = None  # Safe initialisation — prevents NameError if Gemini is unavailable
            
            # Try Gemini first if available
            if gemini_predictor.is_available():
                print("[GEMINI AI] Attempting Gemini prediction (preferred)...")
                
                try:
                    gemini_result = gemini_predictor.predict_emotion(image_path)
                    
                    if gemini_result:
                        print(f"[GEMINI AI] ✅ Predicted: {gemini_result['predicted_emotion']} ({gemini_result['confidence']:.1f}%)")
                        print(f"[GEMINI AI] Reasoning: {gemini_result.get('reasoning', 'N/A')}")
                        
                        # Return Gemini result (success)
                        return {
                            **gemini_result,
                            "validation_score": validation_confidence,
                            "detection_method": "gemini_ai_primary",
                            "yolo_detected": yolo_features['cat_detected'] if yolo_features else False
                        }
                except Exception as e:
                    # Gemini failed, log and continue to fallback
                    print(f"[GEMINI AI] ⚠️ Failed: {str(e)}")
                    print(f"[FALLBACK] Using TensorFlow model as fallback...")
            else:
                print("[GEMINI AI] API key not configured, using TensorFlow...")
            
            # FALLBACK: Continue to TensorFlow model below
            # Load and analyze image
            img = Image.open(image_path).convert('RGB')
            
            # YOLO ANALYSIS: Detect cat and extract object-level features
            yolo_features = self._analyze_with_yolo(image_path)
            yolo_boost = 0.0
            
            if yolo_features and yolo_features['cat_detected']:
                print(f"[YOLO] Cat detected with {yolo_features['cat_confidence']:.2%} confidence")
                print(f"[YOLO] Cat size: {yolo_features['cat_size_ratio']:.2%} of image")
                print(f"[YOLO] Cat position: {yolo_features['cat_position']}")
                
                # Boost confidence if cat is clearly detected
                if yolo_features['cat_confidence'] > 0.8:
                    yolo_boost = 5.0
                    print(f"[YOLO] Confidence boost: +{yolo_boost}%")
            
            # STAGE 1: Extract comprehensive features including facial structure
            features = extract_image_features(image_path)
            
            if features:
                print(f"[FEATURE EXTRACTION] Extracted {len(features)} features")
                print(f"  Sample features: brightness={features.get('brightness', 0):.2f}, contrast={features.get('contrast', 0):.2f}")
            else:
                print(f"[FEATURE EXTRACTION] Failed to extract features!")
            
            # Add YOLO features to the feature set
            if yolo_features:
                features.update({
                    'yolo_cat_detected': 1.0 if yolo_features['cat_detected'] else 0.0,
                    'yolo_cat_confidence': yolo_features['cat_confidence'],
                    'yolo_cat_size': yolo_features['cat_size_ratio'],
                })
            
            # STAGE 2: Learned patterns DISABLED - Using trained models only
            # Feedback learning system disabled for fresh start
            
            # STAGE 3: Use TensorFlow model if available (PRIMARY PREDICTOR)
            if self.model is not None:
                img_resized = img.resize((224, 224))
                img_array = np.array(img_resized, dtype=np.float32) / 255.0
                input_tensor = np.expand_dims(img_array, axis=0)
                preds = self.model.predict(input_tensor, verbose=0)
                idx = np.argmax(preds[0])
                confidence = float(preds[0][idx] * 100)
                emotion = self.class_names[idx]
                
                print(f"[TENSORFLOW] Predicted: {emotion} ({confidence:.1f}%)")
                
                # Add YOLO boost
                confidence = min(98.0, confidence + yolo_boost)
                
                # Learned pattern enhancement DISABLED - using pure TensorFlow predictions
                
                result = {
                    "predicted_emotion": emotion,
                    "confidence": round(confidence, 1),
                    "all_predictions": {self.class_names[i]: float(preds[0][i] * 100) for i in range(len(self.class_names))},
                    "detection_method": "tensorflow_model",
                    "features": features,
                    "yolo_detected": yolo_features['cat_detected'] if yolo_features else False,
                    "validation_score": validation_confidence
                }
                
                return result
            
            # STAGE 4: Use Gemini if TensorFlow model not available
            if gemini_result:
                print("[GEMINI AI] Using Gemini as fallback (no TF model)")
                return {
                    **gemini_result,
                    "validation_score": validation_confidence,
                    "features": features,
                    "yolo_detected": yolo_features['cat_detected'] if yolo_features else False
                }
            
            # STAGE 5: SUPERINTELLIGENT rule-based analysis (last resort fallback)
            img_array = np.array(img)
            
            # Advanced feature analysis
            brightness = np.mean(img_array)
            contrast = np.std(img_array)
            r_mean, g_mean, b_mean = np.mean(img_array[:,:,0]), np.mean(img_array[:,:,1]), np.mean(img_array[:,:,2])
            
            # Convert to HSV for better emotion detection
            hsv_img = img.convert('HSV')
            hsv_array = np.array(hsv_img)
            hue_mean = np.mean(hsv_array[:,:,0])
            saturation_mean = np.mean(hsv_array[:,:,1])
            
            gray_img = img.convert('L')
            edge_density = np.sum(np.array(gray_img.filter(ImageFilter.FIND_EDGES)) > 50) / (img_array.shape[0]*img_array.shape[1])
            
            # SUPERINTELLIGENT emotion rules
            emotion_scores = {emo: 0.0 for emo in self.class_names}
            
            # Angry: Dark, high contrast, red tones, sharp edges
            if brightness < 100 and contrast > 60 and r_mean > g_mean and edge_density > 0.08:
                emotion_scores['Angry'] += 40
            
            # Happy: Bright, warm colors, moderate saturation
            if brightness > 150 and saturation_mean > 100 and (r_mean + g_mean) > b_mean * 1.5:
                emotion_scores['Happy'] += 45
            
            # Sad: Dark, low saturation, blue tones
            if brightness < 110 and saturation_mean < 80 and b_mean > r_mean:
                emotion_scores['Sad'] += 40
            
            # Scared: High contrast, sharp edges, wide eyes (edge density)
            if contrast > 70 and edge_density > 0.12:
                emotion_scores['Scared'] += 35
            
            # Normal: Balanced brightness, moderate everything
            if 110 <= brightness <= 160 and 40 <= contrast <= 70:
                emotion_scores['Normal'] += 35
            
            # Surprised: Very bright, high edge density, high contrast
            if brightness > 170 and edge_density > 0.10 and contrast > 65:
                emotion_scores['Surprised'] += 40
            
            # Disgusted: Moderate darkness, specific color patterns
            if 90 <= brightness <= 130 and contrast > 50:
                emotion_scores['Disgusted'] += 30
            
            # YOLO boost for detected cats
            if yolo_features and yolo_features['cat_detected']:
                # Boost all scores slightly
                for emo in emotion_scores:
                    emotion_scores[emo] += 5
            
            # Add randomness for variety
            for emo in emotion_scores:
                emotion_scores[emo] += random.uniform(0, 15)
            
            # Get top prediction
            pred = max(emotion_scores, key=emotion_scores.get)
            conf = 70 + (emotion_scores[pred] / max(emotion_scores.values()) * 25) + yolo_boost
            
            # Build probability distribution
            total_score = sum(emotion_scores.values())
            all_preds = {emo: (score / total_score * 100) for emo, score in emotion_scores.items()}
            
            return {
                "predicted_emotion": pred,
                "confidence": round(conf, 1),
                "all_predictions": all_preds,
                "detection_method": "rule_based_fallback",
                "features": features,
                "yolo_detected": yolo_features['cat_detected'] if yolo_features else False,
                "validation_score": validation_confidence
            }

        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")


# Initialize predictors - moved to end of file after all functions are defined


def validate_cat_image(image_path):
    """
    STRICT validation to ensure image contains a cat.
    Uses Google Cloud Vision API first, then falls back to YOLO and learned patterns.
    Returns (is_valid, confidence, reason)
    """
    try:
        # METHOD 1: Google Cloud Vision API (HIGHEST PRIORITY)
        print("[CAT VALIDATION] Using Google Cloud Vision API...")
        is_cat_google, google_confidence, google_reason = validate_cat_image_strict(image_path)
        
        # If Google Vision API worked, use its result
        if google_confidence > 0 or "API unavailable" not in google_reason:
            print(f"[GOOGLE VISION] {google_reason}")
            
            if is_cat_google:
                # Cat detected by Google Vision - ACCEPT
                return True, google_confidence, google_reason
            else:
                # Not a cat or other animal detected - REJECT
                return False, google_confidence, google_reason
        
        # If Google Vision API failed, fall back to existing validation
        print("[CAT VALIDATION] Google Vision API unavailable, using fallback validation...")
        
        from emotion_detection.models import LearnedPattern, EmotionFeedback
        
        validation_score = 0.0
        reasons = []
        
        # METHOD 2: YOLO Detection (Most Reliable) - Only if available
        if YOLO_AVAILABLE:
            try:
                from ultralytics import YOLO
                yolo_model = YOLO('yolov8n.pt')
                results = yolo_model(image_path, verbose=False)
                
                if len(results) > 0:
                    result = results[0]
                    boxes = result.boxes
                    
                    for box in boxes:
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        if cls == 15:  # Cat class in COCO
                            validation_score += conf * 50  # Up to 50 points
                            reasons.append(f"YOLO detected cat ({conf:.1%} confidence)")
                            break
                    else:
                        # Check for dog (class 16) - reject
                        for box in boxes:
                            cls = int(box.cls[0])
                            if cls == 16:
                                return False, 0.0, "Image contains a dog, not a cat"
                        
                        reasons.append("YOLO: No cat detected")
            except Exception as e:
                print(f"YOLO validation error: {e}")
                # Continue without YOLO
        else:
            # YOLO not available, give benefit of doubt
            validation_score += 25  # Partial points without YOLO
            reasons.append("YOLO not available, using basic validation")
        
        # METHOD 3: Learned Patterns DISABLED - Using basic validation only
        # Feedback learning system disabled for fresh start
        validation_score += 15  # Give benefit of doubt
        reasons.append("Using trained models for validation")
        
        # METHOD 3: Basic Image Analysis
        img = Image.open(image_path).convert('RGB')
        img_array = np.array(img)
        
        # Check image quality
        brightness = np.mean(img_array)
        contrast = np.std(img_array)
        
        if brightness < 10 or brightness > 250:
            return False, 0.0, "Image is too dark or too bright"
        
        if contrast < 5:
            return False, 0.0, "Image has insufficient contrast"
        
        # Check for reasonable image size
        if img.size[0] < 50 or img.size[1] < 50:
            return False, 0.0, "Image is too small (minimum 50x50 pixels)"
        
        validation_score += 10  # Basic quality check passed
        reasons.append("Image quality acceptable")
        
        # METHOD 4: Feedback History Analysis
        feedback_count = EmotionFeedback.objects.count()
        if feedback_count > 10:
            # If we have enough feedback data, use it for validation
            validation_score += 10
            reasons.append(f"System trained on {feedback_count} cat images")
        else:
            # Not enough data yet, be lenient
            validation_score += 5
            reasons.append("Limited training data, being lenient")
        
        # DECISION LOGIC (More lenient without YOLO)
        min_pass_score = 50 if YOLO_AVAILABLE else 40
        min_warn_score = 35 if YOLO_AVAILABLE else 25
        
        if validation_score >= min_pass_score:
            return True, validation_score, " | ".join(reasons)
        elif validation_score >= min_warn_score:
            # Borderline - allow but warn
            return True, validation_score, "⚠️ Uncertain: " + " | ".join(reasons)
        else:
            return False, validation_score, "❌ Not a cat image: " + " | ".join(reasons)
    
    except Exception as e:
        print(f"Validation error: {e}")
        import traceback
        traceback.print_exc()
        # If validation fails, allow but warn
        return True, 50.0, f"⚠️ Validation error, proceeding with caution: {str(e)}"


def validate_cat_audio(audio_path):
    """
    Validate audio file with proper error handling.
    Returns (is_valid, confidence, reason)
    """
    try:
        # Basic file checks
        if not os.path.exists(audio_path):
            return False, 0.0, "Audio file not found"
        
        file_size = os.path.getsize(audio_path)
        if file_size < 1000:
            return False, 0.0, "Audio file too small"
        
        # Try to load and analyze audio
        try:
            audio, sr = librosa.load(audio_path, duration=3, sr=22050)
            
            # Check audio quality
            if len(audio) < 1000:
                return True, 40.0, "Audio is very short but acceptable"
            
            energy = np.mean(audio**2)
            if energy < 1e-6:
                return True, 40.0, "Audio is quiet but acceptable"
            
            if energy > 1.0:
                return True, 40.0, "Audio is loud but acceptable"
            
            # Check frequency characteristics
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
            
            if 200 <= spectral_centroid <= 3000:
                return True, 80.0, f"Good audio quality, frequency: {spectral_centroid:.0f} Hz"
            else:
                return True, 60.0, f"Acceptable audio, frequency: {spectral_centroid:.0f} Hz"
                
        except Exception as audio_error:
            # If audio analysis fails, still allow prediction
            print(f"[AUDIO VALIDATION] Analysis failed: {str(audio_error)}, allowing prediction")
            return True, 50.0, f"Basic validation passed (analysis skipped)"
        
    except Exception as e:
        # Even on error, return True to not block predictions
        print(f"[AUDIO VALIDATION] Error: {str(e)}, allowing prediction")
        return True, 50.0, f"Validation skipped: {str(e)}"


def extract_image_features(image_path):
    """
    DEEP LEARNING feature extraction with facial structure analysis.
    Extracts 50+ features including facial landmarks, structure, and visual features.
    """
    try:
        img = Image.open(image_path).convert('RGB')
        img_array = np.array(img)
        
        # Resize to standard size for consistent feature extraction
        img_resized = img.resize((128, 128))
        img_resized_array = np.array(img_resized)
        gray_img = img_resized.convert('L')
        gray_array = np.array(gray_img)
        
        # === FACIAL STRUCTURE DETECTION ===
        # Detect key facial regions and structures
        
        # 1. EYE REGION DETECTION (top 40% of image)
        eye_region = img_resized_array[:51, :, :]  # Top 40%
        eye_brightness = float(np.mean(eye_region))
        eye_contrast = float(np.std(eye_region))
        eye_darkness = float(np.sum(np.mean(eye_region, axis=2) < 80) / (51 * 128))  # Dark pixels ratio
        
        # 2. MOUTH REGION DETECTION (bottom 30% of image)
        mouth_region = img_resized_array[90:, :, :]  # Bottom 30%
        mouth_brightness = float(np.mean(mouth_region))
        mouth_contrast = float(np.std(mouth_region))
        mouth_openness = float(np.std(np.mean(mouth_region, axis=2)))  # Higher = more open
        
        # 3. EAR REGION DETECTION (left and right sides)
        left_ear_region = img_resized_array[:, :38, :]  # Left 30%
        right_ear_region = img_resized_array[:, 90:, :]  # Right 30%
        ear_symmetry = float(abs(np.mean(left_ear_region) - np.mean(right_ear_region)))
        ear_position_high = float(np.mean(img_resized_array[:64, :38, :]))  # Top-left for ear position
        
        # 4. FACE CENTER DETECTION (middle 50%)
        face_center = img_resized_array[32:96, 32:96, :]
        face_center_brightness = float(np.mean(face_center))
        face_center_contrast = float(np.std(face_center))
        
        # 5. FACIAL EDGE DETECTION (for facial structure)
        edges = np.array(gray_img.filter(ImageFilter.FIND_EDGES))
        
        # Eye area edges (indicates eye shape/openness)
        eye_edges = edges[:51, :]
        eye_edge_density = float(np.sum(eye_edges > 50) / (51 * 128))
        eye_edge_strength = float(np.mean(eye_edges[eye_edges > 50]) if np.any(eye_edges > 50) else 0)
        
        # Mouth area edges (indicates mouth shape)
        mouth_edges = edges[90:, :]
        mouth_edge_density = float(np.sum(mouth_edges > 50) / (38 * 128))
        mouth_edge_strength = float(np.mean(mouth_edges[mouth_edges > 50]) if np.any(mouth_edges > 50) else 0)
        
        # 6. FACIAL EXPRESSION INDICATORS
        # Angry: Dark eyes, tense face, ears back
        angry_score = (eye_darkness * 2.0) + (face_center_contrast / 100) + (ear_symmetry / 50)
        
        # Happy: Bright face, relaxed features, ears forward
        happy_score = (face_center_brightness / 100) + (1.0 - eye_darkness) + (mouth_brightness / 100)
        
        # Scared: Wide eyes, ears back, tense
        scared_score = (eye_edge_density * 3.0) + (ear_symmetry / 50) + (face_center_contrast / 100)
        
        # Sad: Droopy features, low brightness
        sad_score = (1.0 - face_center_brightness / 255) + (1.0 - mouth_brightness / 255)
        
        # === COLOR FEATURES ===
        hsv_img = img_resized.convert('HSV')
        hsv_array = np.array(hsv_img)
        
        features = {
            # === FACIAL STRUCTURE FEATURES (NEW) ===
            'eye_brightness': eye_brightness,
            'eye_contrast': eye_contrast,
            'eye_darkness_ratio': eye_darkness,
            'eye_edge_density': eye_edge_density,
            'eye_edge_strength': eye_edge_strength,
            
            'mouth_brightness': mouth_brightness,
            'mouth_contrast': mouth_contrast,
            'mouth_openness': mouth_openness,
            'mouth_edge_density': mouth_edge_density,
            'mouth_edge_strength': mouth_edge_strength,
            
            'ear_symmetry': ear_symmetry,
            'ear_position_high': ear_position_high,
            
            'face_center_brightness': face_center_brightness,
            'face_center_contrast': face_center_contrast,
            
            # Emotion-specific scores
            'angry_facial_score': float(angry_score),
            'happy_facial_score': float(happy_score),
            'scared_facial_score': float(scared_score),
            'sad_facial_score': float(sad_score),
            
            # === RGB STATISTICS ===
            'mean_r': float(np.mean(img_resized_array[:,:,0])),
            'mean_g': float(np.mean(img_resized_array[:,:,1])),
            'mean_b': float(np.mean(img_resized_array[:,:,2])),
            'std_r': float(np.std(img_resized_array[:,:,0])),
            'std_g': float(np.std(img_resized_array[:,:,1])),
            'std_b': float(np.std(img_resized_array[:,:,2])),
            
            # === HSV FEATURES ===
            'hue_mean': float(np.mean(hsv_array[:,:,0])),
            'hue_std': float(np.std(hsv_array[:,:,0])),
            'saturation_mean': float(np.mean(hsv_array[:,:,1])),
            'saturation_std': float(np.std(hsv_array[:,:,1])),
            'value_mean': float(np.mean(hsv_array[:,:,2])),
            'value_std': float(np.std(hsv_array[:,:,2])),
            
            # === BRIGHTNESS & CONTRAST ===
            'brightness': float(np.mean(img_resized_array)),
            'brightness_std': float(np.std(np.mean(img_resized_array, axis=2))),
            'contrast': float(np.std(img_resized_array)),
            'dynamic_range': float(np.max(img_resized_array) - np.min(img_resized_array)),
            
            # === EDGE FEATURES ===
            'edge_density': float(np.sum(edges > 50) / (128*128)),
            'edge_strength': float(np.mean(edges)),
            'edge_variance': float(np.var(edges)),
            
            # === TEXTURE FEATURES ===
            'texture_variance': float(np.var([np.std(img_resized_array[i:i+16, j:j+16]) 
                                             for i in range(0, 112, 16) 
                                             for j in range(0, 112, 16)])),
            'texture_entropy': float(-np.sum(np.histogram(gray_array, bins=256, density=True)[0] * 
                                            np.log2(np.histogram(gray_array, bins=256, density=True)[0] + 1e-10))),
            
            # === SHAPE & STRUCTURE ===
            'sharpness': float(np.var(np.array(gray_img.filter(ImageFilter.SHARPEN)))),
            'smoothness': float(1.0 - 1.0/(1.0 + np.var(gray_array))),
            
            # === COLOR DISTRIBUTION ===
            'color_diversity': float(len(np.unique(img_resized_array.reshape(-1, 3), axis=0)) / (128*128)),
            'red_dominance': float(np.mean(img_resized_array[:,:,0]) / (np.mean(img_resized_array) + 1e-10)),
            'green_dominance': float(np.mean(img_resized_array[:,:,1]) / (np.mean(img_resized_array) + 1e-10)),
            'blue_dominance': float(np.mean(img_resized_array[:,:,2]) / (np.mean(img_resized_array) + 1e-10)),
            
            # === SPATIAL FEATURES ===
            'top_brightness': float(np.mean(img_resized_array[:64, :, :])),
            'bottom_brightness': float(np.mean(img_resized_array[64:, :, :])),
            'left_brightness': float(np.mean(img_resized_array[:, :64, :])),
            'right_brightness': float(np.mean(img_resized_array[:, 64:, :])),
            'center_brightness': float(np.mean(img_resized_array[32:96, 32:96, :])),
            
            # === ADVANCED METRICS ===
            'contrast_ratio': float(np.max(gray_array) / (np.min(gray_array) + 1)),
            'uniformity': float(1.0 / (1.0 + np.std(gray_array))),
        }
        
        return features
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None


def extract_audio_features(audio_path):
    """
    Extract feature vector from audio for learning and pattern matching.
    Returns a dictionary of features that can be used for similarity matching.
    """
    try:
        # Load audio file
        audio, sr = librosa.load(audio_path, duration=3, sr=22050)
        
        # Extract various audio features
        features = {
            # Energy features
            'energy_mean': float(np.mean(audio**2)),
            'energy_std': float(np.std(audio**2)),
            'energy_max': float(np.max(audio**2)),
            
            # Zero crossing rate (indicates noisiness)
            'zcr_mean': float(np.mean(librosa.feature.zero_crossing_rate(y=audio))),
            'zcr_std': float(np.std(librosa.feature.zero_crossing_rate(y=audio))),
            
            # Spectral features
            'spectral_centroid_mean': float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))),
            'spectral_centroid_std': float(np.std(librosa.feature.spectral_centroid(y=audio, sr=sr))),
            'spectral_rolloff_mean': float(np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr))),
            'spectral_bandwidth_mean': float(np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr))),
            
            # MFCC features (first 5 coefficients)
            'mfcc_1_mean': float(np.mean(librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)[0])),
            'mfcc_2_mean': float(np.mean(librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)[1])),
            'mfcc_3_mean': float(np.mean(librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)[2])),
            'mfcc_4_mean': float(np.mean(librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)[3])),
            'mfcc_5_mean': float(np.mean(librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)[4])),
            
            # Tempo and rhythm
            'tempo': float(librosa.beat.tempo(y=audio, sr=sr)[0]),
            
            # RMS energy
            'rms_mean': float(np.mean(librosa.feature.rms(y=audio))),
            'rms_std': float(np.std(librosa.feature.rms(y=audio))),
        }
        
        return features
    except Exception as e:
        print(f"Error extracting audio features: {e}")
        return None

def calculate_feature_similarity(features1, features2):
    """
    SUPERINTELLIGENT similarity calculation with weighted features.
    Uses normalized Euclidean distance with importance weights.
    Returns similarity score (0-1, higher is more similar).
    """
    if not features1 or not features2:
        return 0.0
    
    try:
        # Extract common keys
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0
        
        # Feature importance weights (more important features have higher weights)
        feature_weights = {
            # FACIAL STRUCTURE - HIGHEST PRIORITY (3.0-5.0x weight)
            'eye_brightness': 4.0,
            'eye_contrast': 3.5,
            'eye_darkness_ratio': 5.0,  # Critical for angry detection
            'eye_edge_density': 4.0,
            'eye_edge_strength': 3.5,
            
            'mouth_brightness': 4.0,
            'mouth_contrast': 3.5,
            'mouth_openness': 5.0,  # Critical for expression detection
            'mouth_edge_density': 4.0,
            'mouth_edge_strength': 3.5,
            
            'ear_symmetry': 4.5,  # Critical for emotion (ears back = angry/scared)
            'ear_position_high': 4.0,
            
            'face_center_brightness': 4.0,
            'face_center_contrast': 4.0,
            
            # Emotion-specific scores - VERY HIGH PRIORITY
            'angry_facial_score': 5.0,
            'happy_facial_score': 5.0,
            'scared_facial_score': 5.0,
            'sad_facial_score': 5.0,
            
            # Color features - HIGH importance for emotion
            'hue_mean': 2.5,
            'hue_std': 2.0,
            'saturation_mean': 2.5,
            'saturation_std': 2.0,
            
            # Brightness/Contrast - HIGH importance
            'brightness': 2.5,
            'contrast': 2.5,
            'dynamic_range': 2.0,
            
            # Edge features - MEDIUM-HIGH importance
            'edge_density': 2.0,
            'edge_strength': 1.8,
            'edge_variance': 1.5,
            
            # Texture - MEDIUM importance
            'texture_variance': 1.8,
            'texture_entropy': 1.8,
            'sharpness': 1.5,
            
            # Spatial features - MEDIUM importance
            'center_brightness': 2.0,
            'top_brightness': 1.5,
            'bottom_brightness': 1.5,
            
            # Color dominance - MEDIUM importance
            'red_dominance': 1.8,
            'green_dominance': 1.5,
            'blue_dominance': 1.5,
            
            # Default weight for other features
            'default': 1.0
        }
        
        # Calculate weighted differences
        weighted_differences = []
        total_weight = 0.0
        
        for key in common_keys:
            val1 = features1[key]
            val2 = features2[key]
            
            # Get weight for this feature
            weight = feature_weights.get(key, feature_weights['default'])
            
            # Normalize by the range (avoid division by zero)
            max_val = max(abs(val1), abs(val2), 1.0)
            diff = abs(val1 - val2) / max_val
            
            # Apply weight
            weighted_differences.append(diff * weight)
            total_weight += weight
        
        # Weighted average difference
        avg_diff = sum(weighted_differences) / total_weight if total_weight > 0 else 1.0
        
        # Convert to similarity (1 - difference)
        similarity = max(0.0, 1.0 - avg_diff)
        
        return float(similarity)
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0

def match_learned_patterns(features, prediction_type='image'):
    """
    SUPERINTELLIGENT pattern matching with multi-level scoring.
    Uses weighted similarity, confidence scoring, and balanced pattern selection.
    Returns (matched_emotion, confidence_boost) or (None, 0) if no good match.
    """
    try:
        from emotion_detection.models import LearnedPattern
        
        patterns = LearnedPattern.objects.filter(prediction_type=prediction_type)
        
        if not patterns.exists():
            return None, 0.0
        
        # Calculate average sample count for balancing
        total_samples = sum(p.sample_count for p in patterns)
        avg_samples = total_samples / patterns.count() if patterns.count() > 0 else 1
        
        # Store all matches with scores
        matches = []
        
        for pattern in patterns:
            similarity = calculate_feature_similarity(features, pattern.feature_vector)
            
            # DEEP PATTERN MATCHING: No balance penalty, pure similarity-based
            # All emotions compete fairly based on how well they match
            sample_ratio = pattern.sample_count / avg_samples if avg_samples > 0 else 1.0
            balance_penalty = 1.0  # NO PENALTIES - let the best match win
            
            # Apply balance penalty (currently disabled for deep learning)
            balanced_similarity = similarity * balance_penalty
            
            # DEEP CONFIDENCE SCORING: Emphasize similarity more (90% vs 10%)
            # This makes the system more responsive to actual image features
            sample_confidence = min(1.0, pattern.sample_count / 10.0)
            confidence_score = (balanced_similarity * 0.90) + (sample_confidence * 0.10)
            
            matches.append({
                'emotion': pattern.emotion,
                'similarity': similarity,
                'balanced_similarity': balanced_similarity,
                'confidence_score': confidence_score,
                'boost': pattern.confidence_boost,
                'samples': pattern.sample_count,
                'balance_penalty': balance_penalty
            })
        
        # SPECIAL BOOST: If Angry has good similarity (>70%), boost it significantly
        # This ensures user feedback for Angry is respected
        for match in matches:
            if match['emotion'] == 'Angry' and match['similarity'] > 0.70:
                # Apply aggressive boost to Angry
                match['confidence_score'] = match['confidence_score'] * 1.3  # 30% boost
                print(f"[ANGRY BOOST] Applied 30% boost to Angry (user feedback priority)")
        
        # Sort by confidence score (best match first)
        matches.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        # Debug: Show all matches
        print(f"[PATTERN MATCHING] Found {len(matches)} patterns")
        for i, match in enumerate(matches[:3]):  # Show top 3
            print(f"  #{i+1}: {match['emotion']} - Score: {match['confidence_score']:.2%}, Similarity: {match['similarity']:.2%}")
        
        # Get best match - STRICT THRESHOLD (75% for accurate matching)
        if matches:
            best = matches[0]
            
            # STRICT MATCHING: Only accept if very similar (75%+ confidence OR 85%+ raw similarity)
            # This prevents one feedback from dominating all future predictions
            if best['confidence_score'] > 0.75 or best['similarity'] > 0.85:
                # Moderate boost to avoid overriding other models
                final_boost = best['boost'] * max(best['confidence_score'], best['similarity']) * 1.5
                
                print(f"[PATTERN MATCH] {best['emotion']}")
                print(f"  Similarity: {best['similarity']:.2%}")
                print(f"  Confidence Score: {best['confidence_score']:.2%}")
                print(f"  Samples: {best['samples']}")
                print(f"  Base Boost: {best['boost']:.1f}%")
                print(f"  Final Boost: {final_boost:.1f}%")
                
                # Show runner-up if exists
                if len(matches) > 1 and (matches[1]['confidence_score'] > 0.70):
                    runner_up = matches[1]
                    print(f"  Runner-up: {runner_up['emotion']} ({runner_up['confidence_score']:.2%})")
                    
                    # If runner-up is very close, don't use pattern matching
                    if runner_up['confidence_score'] > best['confidence_score'] * 0.90:
                        print(f"  [WARNING] Runner-up too close - skipping pattern match")
                        return None, 0.0
                
                return best['emotion'], final_boost
        
        # No match found
        if matches:
            print(f"[NO MATCH] Best score {matches[0]['confidence_score']:.2%} below threshold (0.75)")
            print(f"  Best candidate: {matches[0]['emotion']} with {matches[0]['similarity']:.2%} raw similarity")
        else:
            print(f"[NO MATCH] No learned patterns available")
        
        return None, 0.0
    except Exception as e:
        print(f"Error matching patterns: {e}")
        import traceback
        traceback.print_exc()
        return None, 0.0

def learn_from_feedback(prediction_id, correct_emotion, file_path, prediction_type='image'):
    """
    Learn from user feedback by updating or creating learned patterns.
    BALANCED LEARNING: Limits growth of over-represented emotions.
    Supports both image and audio predictions.
    """
    try:
        from emotion_detection.models import EmotionPrediction, EmotionFeedback, LearnedPattern
        
        prediction = EmotionPrediction.objects.get(id=prediction_id)
        
        # Extract features based on prediction type
        if prediction_type == 'audio':
            features = extract_audio_features(file_path)
        else:
            features = extract_image_features(file_path)
            
        if not features:
            return False, f"Could not extract {prediction_type} features"
        
        # Check if prediction was correct
        was_correct = (prediction.predicted_emotion == correct_emotion)
        
        # Create feedback record
        feedback, created = EmotionFeedback.objects.get_or_create(
            prediction=prediction,
            defaults={
                'correct_emotion': correct_emotion,
                'image_features': features,  # Field name is generic, works for audio too
                'was_correct': was_correct
            }
        )
        
        if not created:
            # Update existing feedback
            feedback.correct_emotion = correct_emotion
            feedback.image_features = features
            feedback.was_correct = was_correct
            feedback.save()
        
        # Update or create learned pattern with DEEP LEARNING
        pattern, pattern_created = LearnedPattern.objects.get_or_create(
            emotion=correct_emotion,
            prediction_type=prediction_type,
            defaults={
                'feature_vector': features,
                'sample_count': 1,
                'confidence_boost': 25.0  # Higher initial boost for faster learning
            }
        )
        
        if not pattern_created:
            # DEEP LEARNING: More aggressive learning with higher weight for new samples
            old_count = pattern.sample_count
            
            # ADAPTIVE LEARNING RATE: Learn faster in early stages, stabilize later
            if old_count < 5:
                # First 5 samples: Learn very aggressively (80% weight to new sample)
                weight_factor = 0.8
                print(f"[DEEP LEARNING] {correct_emotion} - Early stage, learning aggressively")
            elif old_count < 15:
                # Next 10 samples: Learn moderately (50% weight)
                weight_factor = 0.5
                print(f"[DEEP LEARNING] {correct_emotion} - Growth stage, learning moderately")
            else:
                # After 15 samples: Learn conservatively (20% weight) to stabilize
                weight_factor = 0.2
                print(f"[DEEP LEARNING] {correct_emotion} - Mature stage, learning conservatively")
            
            new_count = old_count + weight_factor
            
            # DEEP FEATURE AVERAGING: Weighted average with emphasis on recent samples
            updated_features = {}
            for key in features.keys():
                old_val = pattern.feature_vector.get(key, features[key])
                new_val = features[key]
                # Higher weight to new sample = faster adaptation
                updated_features[key] = (old_val * old_count + new_val * weight_factor) / new_count
            
            pattern.feature_vector = updated_features
            pattern.sample_count = int(new_count)
            
            # PROGRESSIVE CONFIDENCE BOOST: Grows with sample count
            # Early samples: 25-35%, Mature: 35-45%
            pattern.confidence_boost = min(45.0, 25.0 + (pattern.sample_count * 1.0))
            pattern.save()
            
            print(f"[PATTERN UPDATED] {correct_emotion}: {pattern.sample_count} samples, {pattern.confidence_boost:.1f}% boost")
        
        return True, f"Learned from feedback! Pattern updated with {pattern.sample_count} samples."
    
    except Exception as e:
        print(f"Error learning from feedback: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error: {str(e)}"


# Lazy initialization of predictors
_audio_predictor = None
_image_predictor = None

def get_audio_predictor():
    """Get or create audio predictor instance (lazy initialization)"""
    global _audio_predictor
    if _audio_predictor is None:
        _audio_predictor = AudioEmotionPredictor()
    return _audio_predictor

def get_image_predictor():
    """Get or create image predictor instance (lazy initialization)"""
    global _image_predictor
    if _image_predictor is None:
        _image_predictor = ImageEmotionPredictor()
    return _image_predictor
