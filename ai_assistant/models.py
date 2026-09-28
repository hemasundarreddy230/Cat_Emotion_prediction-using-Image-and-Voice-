from django.db import models
from django.contrib.auth.models import User

class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cat = models.ForeignKey('emotion_detection.CatProfile', on_delete=models.CASCADE, null=True, blank=True)
    question = models.TextField(default='')
    answer = models.TextField(default='')
    context_used = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Legacy fields for compatibility
    message = models.TextField(blank=True)
    response = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Conversation with {self.user.username} at {self.created_at}"
    
    def save(self, *args, **kwargs):
        # Sync legacy fields
        if not self.message and self.question:
            self.message = self.question
        if not self.response and self.answer:
            self.response = self.answer
        if not self.question and self.message:
            self.question = self.message
        if not self.answer and self.response:
            self.answer = self.response
        super().save(*args, **kwargs)
