from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
import os
import tempfile
import mimetypes
from PIL import Image
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("Warning: python-magic not available. Using fallback MIME type detection.")

from .models import CatProfile, EmotionPrediction, HealthAlert
from .ml_service import get_audio_predictor, get_image_predictor
from .ai_content_validator import validate_cat_image, validate_cat_audio

# File validation constants
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/bmp': ['.bmp'],
    'image/webp': ['.webp']
}

ALLOWED_AUDIO_TYPES = {
    'audio/wav': ['.wav'],
    'audio/mpeg': ['.mp3'],
    'audio/mp4': ['.m4a'],
    'audio/ogg': ['.ogg'],
    'audio/flac': ['.flac'],
    'audio/aac': ['.aac']
}

MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB (increased)
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
# Removed dimension restrictions to allow any image size

def validate_image_file(file):
    """Comprehensive image file validation (without size restrictions)"""
    errors = []
    
    # Check file size (increased limit)
    if file.size > MAX_IMAGE_SIZE:
        errors.append(f"Image file too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)}MB")
    
    if file.size < 1024:  # Less than 1KB
        errors.append("Image file too small. Minimum size is 1KB")
    
    # Check file extension
    file_extension = os.path.splitext(file.name)[1].lower()
    valid_extensions = []
    for mime_type, extensions in ALLOWED_IMAGE_TYPES.items():
        valid_extensions.extend(extensions)
    
    if file_extension not in valid_extensions:
        errors.append(f"Invalid image format. Allowed formats: {', '.join(valid_extensions)}")
    
    # Check MIME type using python-magic (more reliable than file extension)
    if MAGIC_AVAILABLE:
        try:
            file_content = file.read(1024)  # Read first 1KB for MIME detection
            file.seek(0)  # Reset file pointer
            
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type not in ALLOWED_IMAGE_TYPES:
                errors.append(f"Invalid image MIME type: {mime_type}")
        except Exception as e:
            errors.append("Could not verify image file type")
    else:
        # Fallback: use Django's content type detection
        if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
            errors.append(f"Invalid image MIME type: {file.content_type}")
    
    # Validate image format using PIL (without dimension restrictions)
    try:
        file.seek(0)
        with Image.open(file) as img:
            # Just verify the image can be opened (no dimension checks)
            img.verify()
            
    except Exception as e:
        errors.append(f"Invalid or corrupted image file: {str(e)}")
    finally:
        file.seek(0)  # Reset file pointer
    
    return errors

def validate_audio_file(file):
    """Comprehensive audio file validation"""
    errors = []
    
    # Check file size
    if file.size > MAX_AUDIO_SIZE:
        errors.append(f"Audio file too large. Maximum size is {MAX_AUDIO_SIZE // (1024*1024)}MB")
    
    if file.size < 1024:  # Less than 1KB
        errors.append("Audio file too small. Minimum size is 1KB")
    
    # Check file extension
    file_extension = os.path.splitext(file.name)[1].lower()
    valid_extensions = []
    for mime_type, extensions in ALLOWED_AUDIO_TYPES.items():
        valid_extensions.extend(extensions)
    
    if file_extension not in valid_extensions:
        errors.append(f"Invalid audio format. Allowed formats: {', '.join(valid_extensions)}")
    
    # Check MIME type using python-magic
    if MAGIC_AVAILABLE:
        try:
            file_content = file.read(1024)  # Read first 1KB for MIME detection
            file.seek(0)  # Reset file pointer
            
            mime_type = magic.from_buffer(file_content, mime=True)
            
            # Some audio files might be detected as application/octet-stream
            if mime_type not in ALLOWED_AUDIO_TYPES and mime_type != 'application/octet-stream':
                errors.append(f"Invalid audio MIME type: {mime_type}")
        except Exception as e:
            errors.append("Could not verify audio file type")
    else:
        # Fallback: use Django's content type detection
        if file.content_type and file.content_type not in ALLOWED_AUDIO_TYPES:
            errors.append(f"Invalid audio MIME type: {file.content_type}")
    
    # Additional audio-specific validations can be added here
    # For example, using librosa or pydub to validate audio content
    
    return errors

@login_required
def emotion_detection_view(request):
    """Main emotion detection page"""
    user_cats = CatProfile.objects.filter(owner=request.user)
    recent_predictions = EmotionPrediction.objects.filter(cat__owner=request.user)[:10]
    
    context = {
        'user_cats': user_cats,
        'recent_predictions': recent_predictions,
    }
    return render(request, 'emotion_detection/simple_detection.html', context)

@login_required
@csrf_exempt
def predict_audio_emotion(request):
    """Handle audio emotion prediction"""
    if request.method == 'POST':
        try:
            cat_id = request.POST.get('cat_id')
            audio_file = request.FILES.get('audio_file')
            
            if not cat_id or not audio_file:
                return JsonResponse({'error': 'Cat ID and audio file are required'}, status=400)
            
            # Basic file validation
            validation_errors = validate_audio_file(audio_file)
            if validation_errors:
                return JsonResponse({
                    'error': 'Audio file validation failed',
                    'validation_errors': validation_errors
                }, status=400)
            
            cat = get_object_or_404(CatProfile, id=cat_id, owner=request.user)
            
            # Save uploaded file temporarily with proper extension
            file_extension = os.path.splitext(audio_file.name)[1].lower()
            if not file_extension:
                file_extension = '.wav'  # Default extension
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                for chunk in audio_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Predict emotion
                print(f"Predicting emotion for audio file: {temp_file_path}")
                print(f"File exists: {os.path.exists(temp_file_path)}")
                print(f"File size: {os.path.getsize(temp_file_path) if os.path.exists(temp_file_path) else 'N/A'}")
                
                result = get_audio_predictor().predict_emotion(temp_file_path)
                print(f"Prediction result: {result}")
                
                # Save prediction to database
                prediction = EmotionPrediction.objects.create(
                    cat=cat,
                    prediction_type='audio',
                    predicted_emotion=result['predicted_emotion'],
                    confidence=result['confidence'],
                    file_path=audio_file,
                    raw_predictions=result['all_predictions']
                )
                
                # Check for health alerts
                check_emotion_alerts(cat, result['predicted_emotion'], result['confidence'])
                
                response_data = {
                    'success': True,
                    'predicted_emotion': result['predicted_emotion'],
                    'confidence': f"{result['confidence']:.2f}%",
                    'all_predictions': result['all_predictions'],
                    'prediction_id': prediction.id,
                    'file_info': {
                        'name': audio_file.name,
                        'size': f"{audio_file.size / (1024*1024):.2f} MB",
                        'type': audio_file.content_type
                    },
                    'model_used': result.get('model_used', 'Audio Analysis'),
                    'detection_method': result.get('detection_method', 'audio_analysis')
                }
                
                return JsonResponse(response_data)
                
            except Exception as pred_error:
                print(f"Prediction error: {pred_error}")
                import traceback
                traceback.print_exc()
                raise
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Audio prediction error: {error_trace}")
            return JsonResponse({'error': f'Processing error: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def predict_image_emotion(request):
    """Handle image emotion prediction with comprehensive validation including AI content validation"""
    if request.method == 'POST':
        try:
            cat_id = request.POST.get('cat_id')
            image_file = request.FILES.get('image_file')
            
            # Debug logging
            print(f"DEBUG: cat_id = {cat_id}")
            print(f"DEBUG: image_file = {image_file}")
            print(f"DEBUG: AI_VALIDATION_ENABLED = {getattr(settings, 'AI_VALIDATION_ENABLED', True)}")
            
            if not cat_id or not image_file:
                print("DEBUG: Missing cat_id or image_file")
                return JsonResponse({'error': 'Cat ID and image file are required'}, status=400)
            
            # Skip all validation for now - just try to process
            cat = get_object_or_404(CatProfile, id=cat_id, owner=request.user)
            print(f"DEBUG: Found cat: {cat.name}")
            
            # Skip AI validation if disabled
            if not getattr(settings, 'AI_VALIDATION_ENABLED', True):
                print("DEBUG: AI validation disabled, skipping...")
                ai_info = {'ai_validated': False, 'ai_reason': 'AI validation disabled for testing'}
            else:
                print("DEBUG: AI validation enabled, running...")
                # Basic file validation
                validation_errors = validate_image_file(image_file)
                if validation_errors:
                    print(f"DEBUG: Basic validation errors: {validation_errors}")
                    return JsonResponse({
                        'error': 'Image file validation failed',
                        'validation_errors': validation_errors
                    }, status=400)
                
                # AI Content Validation - Check if image actually contains a cat
                ai_validation = validate_cat_image(image_file)
                
                if not ai_validation['is_valid']:
                    print(f"DEBUG: AI validation failed: {ai_validation}")
                    return JsonResponse({
                        'error': 'AI Content Validation Failed',
                        'validation_errors': [
                            'This image does not appear to contain a cat.',
                            f'AI Confidence: {ai_validation["confidence"]:.1%}',
                            f'Detected: {ai_validation["detected_content"]}'
                        ] + ai_validation.get('warnings', []),
                        'ai_details': ai_validation.get('details', {}),
                        'suggestions': [
                            'Please upload a clear image of your cat',
                            'Make sure the cat is visible and recognizable',
                            'Avoid images with multiple animals or unclear subjects',
                            'Good lighting and focus help with detection'
                        ]
                    }, status=400)
                
                # Add AI validation info to response for successful validations
                ai_info = {
                    'ai_validated': True,
                    'ai_confidence': ai_validation['confidence'],
                    'ai_details': ai_validation.get('details', {})
                }
            
            # Save uploaded file temporarily with proper extension
            file_extension = os.path.splitext(image_file.name)[1].lower()
            if not file_extension:
                file_extension = '.jpg'  # Default extension
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                for chunk in image_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            print(f"DEBUG: Saved temp file: {temp_file_path}")
            
            try:
                # Predict emotion
                print("DEBUG: Starting emotion prediction...")
                result = get_image_predictor().predict_emotion(temp_file_path)
                print(f"DEBUG: Prediction result: {result}")
                
                # Get image dimensions for additional info
                with Image.open(temp_file_path) as img:
                    width, height = img.size
                
                # Save prediction to database
                prediction = EmotionPrediction.objects.create(
                    cat=cat,
                    prediction_type='image',
                    predicted_emotion=result['predicted_emotion'],
                    confidence=result['confidence'],
                    file_path=image_file,
                    raw_predictions=result['all_predictions']
                )
                
                # Check for health alerts
                check_emotion_alerts(cat, result['predicted_emotion'], result['confidence'])
                
                # Determine prediction source description
                detection_method = result.get('detection_method', 'image_analysis')
                source_descriptions = {
                    'gemini_ai_only': 'Gemini AI (Only Predictor)',
                    'deep_learning_facial_structure': 'Learned Pattern (Your Feedback)',
                    'tensorflow_model': 'TensorFlow Model (Trained AI)',
                    'tensorflow_model_gemini_hybrid': 'Hybrid (TensorFlow + Gemini AI)',
                    'gemini_ai_primary': 'Gemini AI (Primary)',
                    'gemini_ai': 'Gemini AI',
                    'rule_based': 'Rule-Based Analysis (Fallback)',
                    'image_analysis': 'Image Analysis'
                }
                
                response_data = {
                    'success': True,
                    'predicted_emotion': result['predicted_emotion'],
                    'confidence': f"{result['confidence']:.2f}%",
                    'all_predictions': result['all_predictions'],
                    'prediction_id': prediction.id,
                    'file_info': {
                        'name': image_file.name,
                        'size': f"{image_file.size / (1024*1024):.2f} MB",
                        'type': image_file.content_type,
                        'dimensions': f"{width}x{height}"
                    },
                    'detection_method': detection_method,
                    'prediction_source': source_descriptions.get(detection_method, 'AI Analysis'),
                    'yolo_detected': result.get('yolo_detected', False),
                    'validation_score': result.get('validation_score', 0)
                }
                
                # Add Gemini analysis if available
                if 'gemini_analysis' in result:
                    gemini = result['gemini_analysis']
                    response_data['gemini_analysis'] = {
                        'emotion': gemini.get('emotion'),
                        'confidence': f"{gemini.get('confidence', 0):.2f}%",
                        'reasoning': gemini.get('reasoning', ''),
                        'agrees_with_model': gemini.get('emotion') == result['predicted_emotion']
                    }
                
                # Add AI validation info to response
                response_data.update(ai_info)
                
                print(f"DEBUG: Success response: {response_data}")
                return JsonResponse(response_data)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            error_message = str(e)
            print(f"DEBUG: Exception occurred: {error_message}")
            import traceback
            traceback.print_exc()
            
            # Check if it's a validation error (not a cat image)
            if "validation failed" in error_message.lower() or "not a cat" in error_message.lower():
                return JsonResponse({
                    'error': 'Image Validation Failed',
                    'message': error_message,
                    'suggestions': [
                        'Please upload a clear image of a cat',
                        'Make sure the cat is visible and recognizable',
                        'Avoid images with other animals (dogs, birds, etc.)',
                        'Good lighting and focus help with detection'
                    ]
                }, status=400)
            
            # Other errors
            return JsonResponse({'error': f'Processing error: {error_message}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def prediction_tab_view(request):
    """Dedicated prediction tab with 2 buttons for selected cats"""
    cat_ids_param = request.GET.get('cats', '')
    
    if not cat_ids_param:
        messages.error(request, 'No cats selected for prediction.')
        return redirect('emotion_detection:detection')
    
    try:
        cat_ids = [int(id.strip()) for id in cat_ids_param.split(',') if id.strip()]
        selected_cats = CatProfile.objects.filter(id__in=cat_ids, owner=request.user)
        
        if not selected_cats.exists():
            messages.error(request, 'Selected cats not found or not owned by you.')
            return redirect('emotion_detection:detection')
        
        context = {
            'selected_cats': selected_cats,
            'cat_ids': cat_ids,
        }
        return render(request, 'emotion_detection/prediction_tab.html', context)
        
    except ValueError:
        messages.error(request, 'Invalid cat selection.')
        return redirect('emotion_detection:detection')

@login_required
def prediction_history(request):
    """View prediction history"""
    cat_id = request.GET.get('cat_id')
    predictions = EmotionPrediction.objects.filter(cat__owner=request.user)
    
    if cat_id:
        predictions = predictions.filter(cat_id=cat_id)
    
    predictions = predictions.order_by('-created_at')
    user_cats = CatProfile.objects.filter(owner=request.user)
    
    context = {
        'predictions': predictions,
        'user_cats': user_cats,
        'selected_cat_id': int(cat_id) if cat_id else None,
    }
    return render(request, 'emotion_detection/history.html', context)

def check_emotion_alerts(cat, emotion, confidence):
    """Check if emotion requires health alert"""
    alert_emotions = {
        'Paining': {'severity': 'high', 'message': 'Your cat might be in pain. Consider consulting a veterinarian.'},
        'Angry': {'severity': 'medium', 'message': 'Your cat seems agitated. Check for stressors in the environment.'},
        'Fighting': {'severity': 'medium', 'message': 'Your cat shows aggressive behavior. Monitor interactions with other pets.'},
        'Warning': {'severity': 'medium', 'message': 'Your cat is showing warning signs. Be cautious during interactions.'},
        'Sad': {'severity': 'medium', 'message': 'Your cat appears sad. Consider increasing playtime and attention.'},
        'Scared': {'severity': 'low', 'message': 'Your cat seems frightened. Provide a safe, quiet space.'},
    }
    
    if emotion in alert_emotions and confidence > 70:
        alert_info = alert_emotions[emotion]
        
        # Check if similar alert exists in last 24 hours
        from django.utils import timezone
        from datetime import timedelta
        
        recent_alerts = HealthAlert.objects.filter(
            cat=cat,
            alert_type='emotion',
            title__icontains=emotion,
            created_at__gte=timezone.now() - timedelta(hours=24),
            is_resolved=False
        )
        
        if not recent_alerts.exists():
            HealthAlert.objects.create(
                cat=cat,
                alert_type='emotion',
                severity=alert_info['severity'],
                title=f'{emotion} Emotion Detected',
                message=alert_info['message']
            )


@login_required
@csrf_exempt
def submit_feedback(request):
    """Handle user feedback on emotion predictions for learning"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prediction_id = data.get('prediction_id')
            correct_emotion = data.get('correct_emotion')
            
            if not prediction_id or not correct_emotion:
                return JsonResponse({'error': 'Missing prediction_id or correct_emotion'}, status=400)
            
            # Get the prediction
            prediction = get_object_or_404(EmotionPrediction, id=prediction_id, cat__owner=request.user)
            
            # Get the file path
            file_path = prediction.file_path.path
            
            # Learn from feedback (supports both image and audio)
            from .ml_service import learn_from_feedback
            success, message = learn_from_feedback(
                prediction_id, 
                correct_emotion, 
                file_path,
                prediction.prediction_type
            )
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'correct_emotion': correct_emotion,
                    'prediction_type': prediction.prediction_type
                })
            else:
                return JsonResponse({'error': message}, status=500)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Error processing feedback: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def get_learned_patterns(request):
    """Get statistics about learned patterns"""
    try:
        from .models import LearnedPattern, EmotionFeedback
        
        patterns = LearnedPattern.objects.all().order_by('-sample_count')
        feedback_count = EmotionFeedback.objects.count()
        correct_count = EmotionFeedback.objects.filter(was_correct=True).count()
        
        pattern_data = []
        for pattern in patterns:
            pattern_data.append({
                'emotion': pattern.emotion,
                'type': pattern.prediction_type,
                'samples': pattern.sample_count,
                'confidence_boost': pattern.confidence_boost,
                'updated': pattern.updated_at.isoformat()
            })
        
        accuracy = (correct_count / feedback_count * 100) if feedback_count > 0 else 0
        
        return JsonResponse({
            'success': True,
            'patterns': pattern_data,
            'total_feedback': feedback_count,
            'correct_predictions': correct_count,
            'accuracy': round(accuracy, 2)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_next_feedback_prediction(request):
    """Get the next prediction that needs feedback"""
    try:
        from .models import EmotionPrediction, EmotionFeedback
        
        # Get predictions without feedback, ordered by most recent
        predictions_without_feedback = EmotionPrediction.objects.filter(
            cat__owner=request.user
        ).exclude(
            id__in=EmotionFeedback.objects.values_list('prediction_id', flat=True)
        ).order_by('-created_at')
        
        if not predictions_without_feedback.exists():
            return JsonResponse({
                'success': False,
                'message': 'No predictions need feedback. All predictions have been reviewed!'
            })
        
        # Get the next prediction
        next_prediction = predictions_without_feedback.first()
        
        # Get emotion choices based on prediction type
        if next_prediction.prediction_type == 'audio':
            emotion_choices = [choice[0] for choice in EmotionPrediction.AUDIO_EMOTIONS]
        else:
            emotion_choices = [choice[0] for choice in EmotionPrediction.IMAGE_EMOTIONS]
        
        return JsonResponse({
            'success': True,
            'prediction': {
                'id': next_prediction.id,
                'cat_name': next_prediction.cat.name,
                'cat_id': next_prediction.cat.id,
                'predicted_emotion': next_prediction.predicted_emotion,
                'confidence': next_prediction.confidence,
                'prediction_type': next_prediction.prediction_type,
                'file_url': next_prediction.file_path.url,
                'created_at': next_prediction.created_at.isoformat(),
                'all_predictions': next_prediction.raw_predictions
            },
            'emotion_choices': emotion_choices,
            'remaining_count': predictions_without_feedback.count() - 1
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

