from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User
from app.ml_models.audio_predictor import AudioEmotionPredictor
from app.ml_models.image_predictor import ImageEmotionPredictor
import tempfile
import os
import time
from typing import Dict, Any

router = APIRouter(prefix="/predict", tags=["Prediction"])

# Initialize predictors
audio_predictor = AudioEmotionPredictor()
image_predictor = ImageEmotionPredictor()

@router.post("/audio", response_model=Dict[str, Any])
async def predict_audio_emotion(
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Predict cat emotion from audio file
    Requires authentication
    """
    # Validate file type
    if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file (mp3, wav, etc.)"
        )
    
    temp_file_path = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file_path = temp_file.name
            # Save uploaded file
            content = await audio_file.read()
            temp_file.write(content)
            temp_file.flush()
        
        # Predict emotion (file is now closed)
        result = audio_predictor.predict_emotion(temp_file_path)
        
        # Add user info to result
        result["user"] = current_user.username
        result["file_name"] = audio_file.filename
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio file: {str(e)}"
        )
    finally:
        # Clean up temporary file with retry logic
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except PermissionError:
                # Retry after a short delay
                time.sleep(0.1)
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # If still can't delete, let OS handle it

@router.post("/image", response_model=Dict[str, Any])
async def predict_image_emotion(
    image_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Predict cat emotion from image file
    Requires authentication
    """
    # Validate file type
    if not image_file.content_type or not image_file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image file (jpg, png, etc.)"
        )
    
    temp_file_path = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file_path = temp_file.name
            # Save uploaded file
            content = await image_file.read()
            temp_file.write(content)
            temp_file.flush()
        
        # Predict emotion (file is now closed)
        result = image_predictor.predict_emotion(temp_file_path)
        
        # Add user info to result
        result["user"] = current_user.username
        result["file_name"] = image_file.filename
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image file: {str(e)}"
        )
    finally:
        # Clean up temporary file with retry logic
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except PermissionError:
                # Retry after a short delay
                time.sleep(0.1)
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # If still can't delete, let OS handle it

@router.get("/models/status")
async def get_models_status(current_user: User = Depends(get_current_active_user)):
    """
    Get the status of loaded ML models
    Requires authentication
    """
    return {
        "audio_model": {
            "loaded": audio_predictor.model is not None,
            "path": audio_predictor.model_path,
            "emotions": audio_predictor.emotions,
            "status": "Real TensorFlow model" if audio_predictor.model is not None else "Model not found"
        },
        "image_model": {
            "loaded": image_predictor.model is not None,
            "path": image_predictor.model_path,
            "emotions": image_predictor.class_names,
            "status": "Real PyTorch model" if image_predictor.model is not None else "Model not found"
        },
        "user": current_user.username,
        "note": "Real ML models loaded - providing actual predictions"
    }