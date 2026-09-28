from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CatProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cats')
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(help_text="Age in months")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    weight = models.FloatField(help_text="Weight in kg", null=True, blank=True)
    photo = models.ImageField(upload_to='cat_photos/', blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    class Meta:
        ordering = ['-created_at']

class EmotionPrediction(models.Model):
    PREDICTION_TYPE_CHOICES = [
        ('audio', 'Audio'),
        ('image', 'Image'),
    ]
    
    AUDIO_EMOTIONS = [
        ('Angry', 'Angry'),
        ('Defence', 'Defence'),
        ('Fighting', 'Fighting'),
        ('Happy', 'Happy'),
        ('HuntingMind', 'Hunting Mind'),
        ('Mating', 'Mating'),
        ('MotherCall', 'Mother Call'),
        ('Paining', 'Paining'),
        ('Resting', 'Resting'),
        ('Warning', 'Warning'),
    ]
    
    IMAGE_EMOTIONS = [
        ('Angry', 'Angry'),
        ('Disgusted', 'Disgusted'),
        ('Happy', 'Happy'),
        ('Normal', 'Normal'),
        ('Sad', 'Sad'),
        ('Scared', 'Scared'),
        ('Surprised', 'Surprised'),
    ]
    
    cat = models.ForeignKey(CatProfile, on_delete=models.CASCADE, related_name='predictions')
    prediction_type = models.CharField(max_length=10, choices=PREDICTION_TYPE_CHOICES)
    predicted_emotion = models.CharField(max_length=20)
    confidence = models.FloatField()
    file_path = models.FileField(upload_to='predictions/')
    raw_predictions = models.JSONField()  # Store all emotion probabilities
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.cat.name} - {self.predicted_emotion} ({self.confidence:.2f}%)"
    
    class Meta:
        ordering = ['-created_at']

class HealthAlert(models.Model):
    ALERT_TYPES = [
        ('emotion', 'Emotion Alert'),
        ('behavior', 'Behavior Alert'),
        ('health', 'Health Alert'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    cat = models.ForeignKey(CatProfile, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.cat.name} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']

class DietPlan(models.Model):
    cat = models.ForeignKey(CatProfile, on_delete=models.CASCADE, related_name='old_diet_plans')
    title = models.CharField(max_length=200)
    description = models.TextField()
    food_items = models.JSONField()  # Store food items and quantities
    feeding_schedule = models.JSONField()  # Store feeding times
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.cat.name} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']

class PhotoGallery(models.Model):
    cat = models.ForeignKey(CatProfile, on_delete=models.CASCADE, related_name='gallery_photos')
    image = models.ImageField(upload_to='gallery/')
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    emotion_tags = models.JSONField(blank=True, null=True)  # Auto-tagged emotions
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.cat.name} - {self.title or 'Photo'}"
    
    class Meta:
        ordering = ['-created_at']

class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    cat = models.ForeignKey(CatProfile, on_delete=models.CASCADE, related_name='ai_conversations', null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    context_used = models.JSONField(blank=True, null=True)  # Store emotion context
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.question[:50]}..."
    
    class Meta:
        ordering = ['-created_at']

class EmotionFeedback(models.Model):
    """Store user feedback on emotion predictions for learning"""
    prediction = models.OneToOneField(EmotionPrediction, on_delete=models.CASCADE, related_name='feedback')
    correct_emotion = models.CharField(max_length=20)  # User's correction
    image_features = models.JSONField()  # Store extracted image features for learning
    was_correct = models.BooleanField(default=False)  # Was original prediction correct?
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback for {self.prediction.id} - {self.correct_emotion}"
    
    class Meta:
        ordering = ['-created_at']

class LearnedPattern(models.Model):
    """
    Store learned patterns from user feedback - GLOBAL FOR ALL USERS.
    
    This model is intentionally NOT linked to any user or cat.
    All feedback from all users contributes to the same global patterns,
    so the AI learns from the entire community and improves for everyone.
    
    When any user provides feedback, it updates the global pattern for that emotion,
    and all future predictions for all users benefit from this learning.
    """
    emotion = models.CharField(max_length=20, db_index=True)
    prediction_type = models.CharField(max_length=10, choices=EmotionPrediction.PREDICTION_TYPE_CHOICES)
    feature_vector = models.JSONField()  # Averaged features for this emotion
    sample_count = models.IntegerField(default=1)  # Number of samples contributing to this pattern
    confidence_boost = models.FloatField(default=10.0)  # How much to boost confidence when matched
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.emotion} pattern ({self.sample_count} samples)"
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['emotion', 'prediction_type']