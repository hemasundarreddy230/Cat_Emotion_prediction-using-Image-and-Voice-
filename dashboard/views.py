from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json

from emotion_detection.models import CatProfile, EmotionPrediction, HealthAlert, PhotoGallery
from ai_assistant.models import AIConversation

@login_required
def dashboard_home(request):
    """Main dashboard view"""
    user_cats = CatProfile.objects.filter(owner=request.user)
    total_cats = user_cats.count()
    
    # Recent predictions
    recent_predictions = EmotionPrediction.objects.filter(
        cat__owner=request.user
    ).order_by('-created_at')[:5]
    
    # Health alerts
    active_alerts = HealthAlert.objects.filter(
        cat__owner=request.user,
        is_resolved=False
    ).order_by('-created_at')[:5]
    
    # Statistics
    total_predictions = EmotionPrediction.objects.filter(cat__owner=request.user).count()
    total_photos = PhotoGallery.objects.filter(cat__owner=request.user).count()
    
    # Emotion trends (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    emotion_trends = EmotionPrediction.objects.filter(
        cat__owner=request.user,
        created_at__gte=week_ago
    ).values('predicted_emotion').annotate(count=Count('id')).order_by('-count')[:5]
    
    context = {
        'user_cats': user_cats,
        'total_cats': total_cats,
        'recent_predictions': recent_predictions,
        'active_alerts': active_alerts,
        'total_predictions': total_predictions,
        'total_photos': total_photos,
        'emotion_trends': emotion_trends,
    }
    return render(request, 'dashboard/home.html', context)

@login_required
def user_profile(request):
    """User profile management"""
    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('dashboard:profile')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            # Update user info
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('dashboard:profile')
    
    password_form = PasswordChangeForm(request.user)
    context = {
        'password_form': password_form,
    }
    return render(request, 'dashboard/profile.html', context)

@login_required
def health_alerts(request):
    """Health alerts management"""
    alerts = HealthAlert.objects.filter(cat__owner=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        alert_id = request.POST.get('alert_id')
        action = request.POST.get('action')
        
        if alert_id and action == 'resolve':
            try:
                alert = HealthAlert.objects.get(id=alert_id, cat__owner=request.user)
                alert.is_resolved = True
                alert.resolved_at = timezone.now()
                alert.save()
                messages.success(request, 'Alert marked as resolved.')
            except HealthAlert.DoesNotExist:
                messages.error(request, 'Alert not found.')
        
        return redirect('dashboard:alerts')
    
    context = {
        'alerts': alerts,
    }
    return render(request, 'dashboard/alerts.html', context)

@login_required
def photo_gallery(request):
    """Photo gallery view - displays all user's cat photos from various sources"""
    from prediction_service.models import CommunityPost
    
    user_cats = CatProfile.objects.filter(owner=request.user)
    cat_filter = request.GET.get('cat')
    
    # Collect all photos from different sources
    all_photos = []
    
    # 1. Photos from PhotoGallery model
    gallery_photos = PhotoGallery.objects.filter(cat__owner=request.user)
    if cat_filter:
        gallery_photos = gallery_photos.filter(cat_id=cat_filter)
    
    for photo in gallery_photos:
        all_photos.append({
            'id': photo.id,
            'image': photo.image,
            'cat': photo.cat,
            'title': photo.title or '',
            'description': photo.description or '',
            'emotion_tags': photo.emotion_tags or [],
            'is_favorite': photo.is_favorite,
            'created_at': photo.created_at,
            'source': 'gallery'
        })
    
    # 2. Photos from EmotionPrediction (emotion detection uploads)
    predictions = EmotionPrediction.objects.filter(
        cat__owner=request.user,
        prediction_type='image',
        file_path__isnull=False
    ).exclude(file_path='')
    
    if cat_filter:
        predictions = predictions.filter(cat_id=cat_filter)
    
    for pred in predictions:
        if pred.file_path:
            all_photos.append({
                'id': f'pred_{pred.id}',
                'image': pred.file_path,
                'cat': pred.cat,
                'title': '',
                'description': '',
                'emotion_tags': [],
                'is_favorite': False,
                'created_at': pred.created_at,
                'source': 'emotion_detection'
            })
    
    # 3. Photos from Community Posts
    posts = CommunityPost.objects.filter(user=request.user, image__isnull=False).exclude(image='')
    if cat_filter:
        posts = posts.filter(cat_id=cat_filter)
    
    for post in posts:
        if post.image:
            all_photos.append({
                'id': f'post_{post.id}',
                'image': post.image,
                'cat': post.cat,
                'title': '',
                'description': post.caption or '',
                'emotion_tags': post.emotion_tags or [],
                'is_favorite': False,
                'created_at': post.created_at,
                'source': 'community_post'
            })
    
    # Sort all photos by creation date (newest first)
    all_photos.sort(key=lambda x: x['created_at'], reverse=True)
    
    context = {
        'photos': all_photos,
        'user_cats': user_cats,
        'selected_cat': int(cat_filter) if cat_filter else None,
        'total_photos': len(all_photos),
    }
    return render(request, 'dashboard/gallery.html', context)

@login_required
def map_view(request):
    """Map view with nearby veterinary services"""
    context = {
        'mapbox_token': 'your_mapbox_token_here',  # You can add this to settings
    }
    return render(request, 'dashboard/map.html', context)

@login_required
def analytics_data(request):
    """API endpoint for dashboard analytics"""
    # Emotion distribution
    emotion_data = EmotionPrediction.objects.filter(
        cat__owner=request.user
    ).values('predicted_emotion').annotate(count=Count('id'))
    
    # Daily predictions (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_predictions = []
    
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        count = EmotionPrediction.objects.filter(
            cat__owner=request.user,
            created_at__date=date.date()
        ).count()
        daily_predictions.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Cat-wise predictions
    cat_predictions = []
    for cat in CatProfile.objects.filter(owner=request.user):
        count = EmotionPrediction.objects.filter(cat=cat).count()
        cat_predictions.append({
            'cat_name': cat.name,
            'count': count
        })
    
    return JsonResponse({
        'emotion_distribution': list(emotion_data),
        'daily_predictions': daily_predictions,
        'cat_predictions': cat_predictions,
    })