from django.contrib import admin
from .models import (
    PredictionRequest, CommunityPost, PostLike, PostComment,
    UserFollow, VeterinaryService, ServiceReview
)

@admin.register(PredictionRequest)
class PredictionRequestAdmin(admin.ModelAdmin):
    list_display = ['cat', 'user', 'prediction_type', 'status', 'confidence_score', 'created_at']
    list_filter = ['prediction_type', 'status', 'is_public', 'created_at']
    search_fields = ['cat__name', 'user__username']
    readonly_fields = ['created_at', 'completed_at', 'processing_time']

@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'cat', 'caption_preview', 'likes_count', 'comments_count', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['user__username', 'cat__name', 'caption']
    readonly_fields = ['created_at', 'updated_at']
    
    def caption_preview(self, obj):
        return obj.caption[:50] + '...' if len(obj.caption) > 50 else obj.caption
    caption_preview.short_description = 'Caption'

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__caption']

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content_preview', 'parent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']

@admin.register(VeterinaryService)
class VeterinaryServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'phone', 'rating', 'reviews_count', 'is_emergency']
    list_filter = ['is_emergency', 'rating']
    search_fields = ['name', 'address', 'services']
    readonly_fields = ['rating', 'reviews_count', 'created_at']

@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'service__name']
