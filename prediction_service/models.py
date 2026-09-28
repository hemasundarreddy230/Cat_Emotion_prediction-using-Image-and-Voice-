from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from emotion_detection.models import CatProfile

class PredictionRequest(models.Model):
    """Enhanced prediction request model"""
    PREDICTION_TYPES = [
        ('image', 'Image Analysis'),
        ('audio', 'Audio Analysis'),
        ('video', 'Video Analysis'),
        ('batch', 'Batch Processing'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prediction_requests')
    cat = models.ForeignKey(CatProfile, on_delete=models.CASCADE, related_name='prediction_requests')
    prediction_type = models.CharField(max_length=10, choices=PREDICTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.FileField(upload_to='predictions/')
    result_data = models.JSONField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    error_message = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)  # For community sharing
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.cat.name} - {self.prediction_type} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']

# Enhanced Community System with Groups
class CommunityGroup(models.Model):
    """Community groups for cat owners"""
    GROUP_TYPES = [
        ('breed', 'Breed Specific'),
        ('location', 'Location Based'),
        ('interest', 'Interest Based'),
        ('health', 'Health Support'),
        ('general', 'General Discussion'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES, default='general')
    cover_image = models.ImageField(upload_to='group_covers/', blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, through='GroupMembership', related_name='joined_groups')
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def members_count(self):
        return self.members.count()
    
    @property
    def posts_count(self):
        return self.group_posts.count()
    
    class Meta:
        ordering = ['-created_at']

class GroupMembership(models.Model):
    """Group membership with roles"""
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'group')

class CommunityPost(models.Model):
    """Enhanced posts for cat photos with group support"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    cat = models.ForeignKey(CatProfile, on_delete=models.CASCADE, related_name='community_posts')
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='group_posts', null=True, blank=True)
    image = models.ImageField(upload_to='community_posts/')
    caption = models.TextField(max_length=2000, blank=True)
    emotion_tags = models.JSONField(blank=True, null=True)  # Auto-detected emotions
    location = models.CharField(max_length=200, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.cat.name} post"
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def comments_count(self):
        return self.comments.count()
    
    class Meta:
        ordering = ['-created_at']

class PostLike(models.Model):
    """Like system for community posts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']

class PostComment(models.Model):
    """Comment system for community posts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} on {self.post}"
    
    class Meta:
        ordering = ['created_at']

# Simple Messaging System
class GroupMessage(models.Model):
    """Simple messaging system for groups"""
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('image', 'Image Message'),
        ('system', 'System Message'),
    ]
    
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(max_length=1000, blank=True)
    image = models.ImageField(upload_to='group_messages/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sender.username} in {self.group.name}"
    
    class Meta:
        ordering = ['created_at']

# Diet Plan System
class DietPlan(models.Model):
    """Ready-made diet plans for cats"""
    PLAN_TYPES = [
        ('kitten', 'Kitten (0-12 months)'),
        ('adult', 'Adult (1-7 years)'),
        ('senior', 'Senior (7+ years)'),
        ('weight_loss', 'Weight Management'),
        ('sensitive', 'Sensitive Stomach'),
        ('indoor', 'Indoor Cat'),
        ('outdoor', 'Outdoor Cat'),
        ('medical', 'Medical Diet'),
    ]
    
    ACTIVITY_LEVELS = [
        ('low', 'Low Activity'),
        ('moderate', 'Moderate Activity'),
        ('high', 'High Activity'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVELS, default='moderate')
    description = models.TextField(max_length=1000)
    age_range = models.CharField(max_length=50)  # e.g., "0-12 months", "1-7 years"
    weight_range = models.CharField(max_length=50)  # e.g., "2-5 kg"
    daily_calories = models.IntegerField()  # calories per day
    meals_per_day = models.IntegerField(default=2)
    feeding_schedule = models.JSONField()  # {"breakfast": "8:00 AM", "dinner": "6:00 PM"}
    food_recommendations = models.JSONField()  # List of recommended foods
    portion_guide = models.JSONField()  # Portion sizes by weight
    special_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_diet_plans', null=True, blank=True)
    is_approved = models.BooleanField(default=True)  # For vet-approved plans
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_plan_type_display()}"
    
    class Meta:
        ordering = ['plan_type', 'name']

class CatDietPlan(models.Model):
    """Assigned diet plans for specific cats"""
    cat = models.ForeignKey(CatProfile, on_delete=models.CASCADE, related_name='diet_plans')
    diet_plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE, related_name='assigned_cats')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_diet_plans')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    custom_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.cat.name} - {self.diet_plan.name}"
    
    class Meta:
        ordering = ['-created_at']

class UserFollow(models.Model):
    """Follow system for users"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']

class VeterinaryService(models.Model):
    """Veterinary services for map functionality"""
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    services = models.JSONField()  # List of services offered
    rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    is_emergency = models.BooleanField(default=False)
    opening_hours = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class ServiceReview(models.Model):
    """Reviews for veterinary services"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_reviews')
    service = models.ForeignKey(VeterinaryService, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    review = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.service.name} ({self.rating}★)"
    
    class Meta:
        unique_together = ('user', 'service')
        ordering = ['-created_at']
