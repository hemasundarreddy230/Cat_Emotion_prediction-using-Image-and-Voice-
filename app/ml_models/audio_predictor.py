import os
import io

# Global variables to hold the models
classifier_model = None
yamnet_model = None
AUDIO_MODEL_LOADED = False

# Audio Model Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "models", "yamnet_cat_audio_emotion_model.keras")
YAMNET_URL = "https://tfhub.dev/google/yamnet/1"
TARGET_SAMPLE_RATE = 16000
EMOTION_LABELS = ['Angry', 'Defence', 'Fighting', 'Happy', 'HuntingMind', 
                  'Mating', 'MotherCall', 'Paining', 'Resting', 'Warning']

def load_audio_model():
    """Loads the YamNet model from TensorFlow Hub and the trained classifier model.
    This should be called at application startup."""
    global classifier_model, yamnet_model, AUDIO_MODEL_LOADED
    
    import tensorflow_hub as hub
    import tensorflow as tf
    
    # 1. Load YamNet
    try:
        print(f"Loading YamNet from {YAMNET_URL}...")
        yamnet_model = hub.load(YAMNET_URL)
        print("YamNet loaded successfully.")
    except Exception as e:
        print(f"Error loading YamNet: {e}")
        yamnet_model = None
    
    # 2. Load Custom Classifier
    if os.path.exists(MODEL_PATH):
        try:
            print(f"Loading Audio Classifier from {MODEL_PATH}...")
            classifier_model = tf.keras.models.load_model(MODEL_PATH)
            print("Audio Classifier loaded successfully.")
        except Exception as e:
            print(f"Error loading Audio Classifier: {e}")
            classifier_model = None
    else:
        print(f"Warning: Audio model file not found at {MODEL_PATH}")
        classifier_model = None
    
    if yamnet_model is not None and classifier_model is not None:
        AUDIO_MODEL_LOADED = True
    else:
        AUDIO_MODEL_LOADED = False

def predict_audio_emotion(audio_bytes: bytes):
    """Predicts emotion from raw audio bytes.
    1. Preprocesses audio (resample to 16k).
    2. Extracts embeddings using YamNet.
    3. Feeds embeddings to the classifier."""
    
    if yamnet_model is None or classifier_model is None:
        return "Model Not Loaded", 0.0
    
    import librosa
    import numpy as np
    import tensorflow as tf
    
    try:
        # Load audio from bytes
        # librosa.load expects a file path or file-like object
        # sr=TARGET_SAMPLE_RATE ensures it is resampled to 16kHz
        audio_stream = io.BytesIO(audio_bytes)
        waveform, sr = librosa.load(audio_stream, sr=TARGET_SAMPLE_RATE)
        
        # YamNet expects normalized audio in [-1.0, 1.0]
        # librosa.load usually returns normalized float32 audio, but good to ensure
        if waveform.dtype != np.float32:
            waveform = waveform.astype(np.float32)
        
        # Inference with YamNet
        # YamNet returns: scores, embeddings, spectrogram
        _, embeddings, _ = yamnet_model(waveform)
        
        # Taking the mean of embeddings across time (as done in the notebook)
        # Shape changes from (N, 1024) -> (1024,)
        # And then we need to add batch dimension -> (1, 1024)
        input_embedding = tf.reduce_mean(embeddings, axis=0)
        input_tensor = tf.expand_dims(input_embedding, axis=0)
        
        # Inference with Classifier
        predictions = classifier_model.predict(input_tensor, verbose=0)
        
        # Get result
        predicted_idx = np.argmax(predictions[0])
        confidence = np.max(predictions[0])
        predicted_label = EMOTION_LABELS[predicted_idx]
        
        return predicted_label, round(float(confidence), 2)
        
    except Exception as e:
        print(f"Error during audio inference: {e}")
        return "Error", 0.0

# Load model on module import
load_audio_model()
