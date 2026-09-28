from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.contrib.auth.models import User
import json
import tempfile
import os

from .models import (
    PredictionRequest, CommunityPost, PostLike, PostComment, 
    UserFollow, VeterinaryService, ServiceReview
)
from emotion_detection.models import CatProfile
from emotion_detection.ml_service import get_audio_predictor, get_image_predictor

@login_required
def prediction_dashboard(request):
    """Enhanced prediction dashboard"""
    # Get predictions from both models
    enhanced_predictions = PredictionRequest.objects.filter(user=request.user)
    from emotion_detection.models import EmotionPrediction
    regular_predictions = EmotionPrediction.objects.filter(cat__owner=request.user)
    
    user_cats = CatProfile.objects.filter(owner=request.user)
    
    # Statistics - combine both prediction types
    total_enhanced = enhanced_predictions.count()
    total_regular = regular_predictions.count()
    total_predictions = total_enhanced + total_regular
    
    completed_predictions = enhanced_predictions.filter(status='completed').count()
    success_rate = (completed_predictions / total_enhanced * 100) if total_enhanced > 0 else 0
    
    # Get recent predictions for display (from enhanced service)
    recent_predictions = enhanced_predictions.order_by('-created_at')[:10]
    
    context = {
        'user_predictions': recent_predictions,
        'user_cats': user_cats,
        'total_predictions': total_predictions,
        'total_enhanced': total_enhanced,
        'total_regular': total_regular,
        'success_rate': success_rate,
    }
    return render(request, 'prediction_service/dashboard.html', context)

@login_required
@csrf_exempt
def enhanced_predict(request):
    """Enhanced prediction endpoint with better tracking"""
    if request.method == 'POST':
        try:
            cat_id = request.POST.get('cat_id')
            prediction_type = request.POST.get('prediction_type')
            file_field = 'image_file' if prediction_type == 'image' else 'audio_file'
            uploaded_file = request.FILES.get(file_field)
            is_public = request.POST.get('is_public') == 'true'
            
            if not all([cat_id, prediction_type, uploaded_file]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            cat = get_object_or_404(CatProfile, id=cat_id, owner=request.user)
            
            # Create prediction request
            prediction_request = PredictionRequest.objects.create(
                user=request.user,
                cat=cat,
                prediction_type=prediction_type,
                file_path=uploaded_file,
                status='processing',
                is_public=is_public
            )
            
            # Process prediction
            try:
                # Save file temporarily with proper extension
                file_extension = uploaded_file.name.split('.')[-1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                import time
                start_time = time.time()
                
                if prediction_type == 'image':
                    result = get_image_predictor().predict_emotion(temp_file_path)
                else:
                    result = get_audio_predictor().predict_emotion(temp_file_path)
                
                processing_time = time.time() - start_time
                
                # Update prediction request
                prediction_request.status = 'completed'
                prediction_request.result_data = result
                prediction_request.confidence_score = result['confidence']
                prediction_request.processing_time = processing_time
                prediction_request.save()
                
                return JsonResponse({
                    'success': True,
                    'prediction_id': prediction_request.id,
                    'predicted_emotion': result['predicted_emotion'],
                    'confidence': f"{result['confidence']:.2f}%",
                    'processing_time': f"{processing_time:.2f}s",
                    'all_predictions': result['all_predictions']
                })
                
            except Exception as e:
                prediction_request.status = 'failed'
                prediction_request.error_message = str(e)
                prediction_request.save()
                return JsonResponse({'error': str(e)}, status=500)
                
            finally:
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def community_feed(request):
    """Instagram-like community feed"""
    posts = CommunityPost.objects.filter(is_public=True).select_related('user', 'cat').prefetch_related('likes', 'comments')
    
    # Filter options - Fixed for SQLite compatibility
    emotion_filter = request.GET.get('emotion')
    if emotion_filter:
        # Use icontains on the JSON field converted to text for SQLite compatibility
        from django.db.models import Q
        import json
        
        # Filter posts where emotion_tags contains the emotion
        filtered_posts = []
        for post in posts:
            if post.emotion_tags and emotion_filter in post.emotion_tags:
                filtered_posts.append(post.id)
        
        posts = posts.filter(id__in=filtered_posts)
    
    # Pagination
    paginator = Paginator(posts, 12)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    
    context = {
        'posts': page_posts,
        'emotion_filter': emotion_filter,
    }
    return render(request, 'prediction_service/community_feed.html', context)

@login_required
@csrf_exempt
def create_community_post(request):
    """Create new community post"""
    if request.method == 'POST':
        try:
            cat_id = request.POST.get('cat_id')
            caption = request.POST.get('caption', '')
            location = request.POST.get('location', '')
            image = request.FILES.get('image')
            
            if not cat_id or not image:
                return JsonResponse({'error': 'Cat and image are required'}, status=400)
            
            cat = get_object_or_404(CatProfile, id=cat_id, owner=request.user)
            
            # Auto-detect emotions if image
            emotion_tags = []
            if image:
                try:
                    # Save file temporarily with proper extension
                    file_extension = image.name.split('.')[-1].lower()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                        for chunk in image.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                    
                    try:
                        result = get_image_predictor().predict_emotion(temp_file_path)
                        emotion_tags = [result['predicted_emotion']]
                    except Exception as pred_error:
                        print(f"Prediction error: {pred_error}")
                        pass
                    finally:
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                except Exception as file_error:
                    print(f"File handling error: {file_error}")
                    pass
            
            post = CommunityPost.objects.create(
                user=request.user,
                cat=cat,
                image=image,
                caption=caption,
                location=location,
                emotion_tags=emotion_tags
            )
            
            return JsonResponse({
                'success': True,
                'post_id': post.id,
                'message': 'Post created successfully!'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    user_cats = CatProfile.objects.filter(owner=request.user)
    context = {'user_cats': user_cats}
    return render(request, 'prediction_service/create_post.html', context)

@login_required
@csrf_exempt
def toggle_like(request):
    """Toggle like on a post"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')
            
            post = get_object_or_404(CommunityPost, id=post_id)
            like, created = PostLike.objects.get_or_create(user=request.user, post=post)
            
            if not created:
                like.delete()
                liked = False
            else:
                liked = True
            
            return JsonResponse({
                'success': True,
                'liked': liked,
                'likes_count': post.likes_count
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def add_comment(request):
    """Add comment to a post"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')
            content = data.get('content')
            parent_id = data.get('parent_id')
            
            if not post_id or not content:
                return JsonResponse({'error': 'Post ID and content are required'}, status=400)
            
            post = get_object_or_404(CommunityPost, id=post_id)
            parent = None
            if parent_id:
                parent = get_object_or_404(PostComment, id=parent_id)
            
            comment = PostComment.objects.create(
                user=request.user,
                post=post,
                content=content,
                parent=parent
            )
            
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'username': request.user.username,
                'content': content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def veterinary_map(request):
    """Enhanced map with veterinary services"""
    services = VeterinaryService.objects.all()
    
    # Filter by service type - Fixed for SQLite compatibility
    service_type = request.GET.get('service_type')
    if service_type:
        # Filter services where services JSON contains the service_type
        filtered_services = []
        for service in services:
            if service.services and service_type in service.services:
                filtered_services.append(service.id)
        
        services = VeterinaryService.objects.filter(id__in=filtered_services)
    
    # Filter by emergency
    emergency_only = request.GET.get('emergency') == 'true'
    if emergency_only:
        services = services.filter(is_emergency=True)
    
    # Prepare services data for JSON (for map markers)
    services_json = json.dumps([{
        'id': service.id,
        'name': service.name,
        'address': service.address,
        'phone': service.phone,
        'latitude': service.latitude,
        'longitude': service.longitude,
        'rating': float(service.rating),
        'reviews_count': service.reviews_count,
        'is_emergency': service.is_emergency
    } for service in services])
    
    context = {
        'services': services,
        'services_json': services_json,
        'service_type': service_type,
        'emergency_only': emergency_only,
    }
    return render(request, 'prediction_service/veterinary_map.html', context)

@login_required
@csrf_exempt
def add_service_review(request):
    """Add review for veterinary service"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service_id = data.get('service_id')
            rating = data.get('rating')
            review_text = data.get('review', '')
            
            if not service_id or not rating:
                return JsonResponse({'error': 'Service ID and rating are required'}, status=400)
            
            service = get_object_or_404(VeterinaryService, id=service_id)
            
            review, created = ServiceReview.objects.update_or_create(
                user=request.user,
                service=service,
                defaults={'rating': rating, 'review': review_text}
            )
            
            # Update service rating
            avg_rating = ServiceReview.objects.filter(service=service).aggregate(
                avg_rating=Avg('rating')
            )['avg_rating']
            service.rating = avg_rating or 0
            service.reviews_count = ServiceReview.objects.filter(service=service).count()
            service.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Review added successfully!',
                'new_rating': service.rating
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def user_profile(request, username):
    """User profile with posts and stats"""
    profile_user = get_object_or_404(User, username=username)
    posts = CommunityPost.objects.filter(user=profile_user, is_public=True)
    
    # Follow status
    is_following = False
    if request.user != profile_user:
        is_following = UserFollow.objects.filter(
            follower=request.user, 
            following=profile_user
        ).exists()
    
    # Stats
    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()
    posts_count = posts.count()
    
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
    }
    return render(request, 'prediction_service/user_profile.html', context)

@login_required
@csrf_exempt
def toggle_follow(request):
    """Toggle follow user"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            
            target_user = get_object_or_404(User, id=user_id)
            if target_user == request.user:
                return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
            
            follow, created = UserFollow.objects.get_or_create(
                follower=request.user,
                following=target_user
            )
            
            if not created:
                follow.delete()
                following = False
            else:
                following = True
            
            return JsonResponse({
                'success': True,
                'following': following,
                'followers_count': target_user.followers.count()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Group Management Views
@login_required
def groups_list(request):
    """List all available groups"""
    from .models import CommunityGroup, GroupMembership
    
    # Get all public groups with consistent member counts
    all_groups = CommunityGroup.objects.filter(is_active=True, is_public=True).order_by('-created_at')
    
    # Get user's groups
    user_groups = CommunityGroup.objects.filter(
        members=request.user,
        is_active=True
    )
    
    # Filter by type if specified
    group_type = request.GET.get('type')
    if group_type:
        all_groups = all_groups.filter(group_type=group_type)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        all_groups = all_groups.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(all_groups, 12)
    page_number = request.GET.get('page')
    groups = paginator.get_page(page_number)
    
    context = {
        'groups': groups,
        'user_groups': user_groups,
        'group_types': CommunityGroup.GROUP_TYPES,
        'current_type': group_type,
        'search_query': search_query,
    }
    return render(request, 'prediction_service/groups_list.html', context)

@login_required
def create_group(request):
    """Create a new community group"""
    from .models import CommunityGroup, GroupMembership
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        group_type = request.POST.get('group_type')
        is_public = request.POST.get('is_public') == 'on'
        cover_image = request.FILES.get('cover_image')
        
        if name and description:
            group = CommunityGroup.objects.create(
                name=name,
                description=description,
                group_type=group_type,
                is_public=is_public,
                creator=request.user,
                cover_image=cover_image
            )
            
            # Add creator as admin
            GroupMembership.objects.create(
                user=request.user,
                group=group,
                role='admin'
            )
            
            messages.success(request, f'Group "{name}" created successfully!')
            return redirect('prediction_service:group_detail', group_id=group.id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'group_types': CommunityGroup.GROUP_TYPES,
    }
    return render(request, 'prediction_service/create_group.html', context)

@login_required
def group_detail(request, group_id):
    """Group detail page with posts and members"""
    from .models import CommunityGroup, GroupMembership, GroupMessage
    
    group = get_object_or_404(CommunityGroup, id=group_id, is_active=True)
    
    # Check if user is a member
    is_member = GroupMembership.objects.filter(user=request.user, group=group).exists()
    membership = None
    if is_member:
        membership = GroupMembership.objects.get(user=request.user, group=group)
    
    # Get group posts
    group_posts = CommunityPost.objects.filter(group=group).select_related(
        'user', 'cat'
    ).prefetch_related('likes', 'comments').order_by('-created_at')
    
    # Pagination for posts
    paginator = Paginator(group_posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    # Get recent members
    recent_members = group.members.order_by('-groupmembership__joined_at')[:12]
    
    # Get recent messages (if member)
    recent_messages = []
    if is_member:
        recent_messages = GroupMessage.objects.filter(group=group).select_related(
            'sender'
        ).order_by('-created_at')[:5]
    
    context = {
        'group': group,
        'is_member': is_member,
        'membership': membership,
        'posts': posts,
        'recent_members': recent_members,
        'recent_messages': recent_messages,
        'members_count': group.members.count(),
        'posts_count': group_posts.count(),
    }
    return render(request, 'prediction_service/group_detail.html', context)

@login_required
@csrf_exempt
def join_group(request, group_id):
    """Join a community group"""
    from .models import CommunityGroup, GroupMembership, GroupMessage
    
    if request.method == 'POST':
        group = get_object_or_404(CommunityGroup, id=group_id, is_active=True)
        
        # Check if already a member
        if GroupMembership.objects.filter(user=request.user, group=group).exists():
            return JsonResponse({'success': False, 'message': 'Already a member'})
        
        # Join the group
        GroupMembership.objects.create(
            user=request.user,
            group=group,
            role='member'
        )
        
        # Send system message
        GroupMessage.objects.create(
            group=group,
            sender=request.user,
            message_type='system',
            content=f'{request.user.username} joined the group'
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully joined {group.name}!',
            'members_count': group.members.count()
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@csrf_exempt
def leave_group(request, group_id):
    """Leave a community group"""
    from .models import CommunityGroup, GroupMembership, GroupMessage
    
    if request.method == 'POST':
        group = get_object_or_404(CommunityGroup, id=group_id, is_active=True)
        
        try:
            membership = GroupMembership.objects.get(user=request.user, group=group)
            
            # Don't allow creator to leave if they're the only admin
            if membership.role == 'admin':
                admin_count = GroupMembership.objects.filter(group=group, role='admin').count()
                if admin_count == 1:
                    return JsonResponse({
                        'success': False, 
                        'message': 'Cannot leave - you are the only admin. Transfer admin rights first.'
                    })
            
            membership.delete()
            
            # Send system message
            GroupMessage.objects.create(
                group=group,
                sender=request.user,
                message_type='system',
                content=f'{request.user.username} left the group'
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Successfully left {group.name}',
                'members_count': group.members.count()
            })
            
        except GroupMembership.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Not a member of this group'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def group_chat(request, group_id):
    """Group chat interface"""
    from .models import CommunityGroup, GroupMembership, GroupMessage
    
    group = get_object_or_404(CommunityGroup, id=group_id, is_active=True)
    
    # Check if user is a member
    if not GroupMembership.objects.filter(user=request.user, group=group).exists():
        messages.error(request, 'You must be a member to access group chat.')
        return redirect('prediction_service:group_detail', group_id=group_id)
    
    # Get chat messages
    chat_messages = GroupMessage.objects.filter(group=group).select_related(
        'sender'
    ).order_by('created_at')
    
    # Pagination for messages (show latest first, then reverse)
    paginator = Paginator(chat_messages, 50)
    page_number = request.GET.get('page', paginator.num_pages)  # Default to last page
    messages_page = paginator.get_page(page_number)
    
    context = {
        'group': group,
        'messages': messages_page,
        'total_messages': chat_messages.count(),
    }
    return render(request, 'prediction_service/group_chat.html', context)

@login_required
def group_members(request, group_id):
    """Group members list"""
    from .models import CommunityGroup, GroupMembership
    
    group = get_object_or_404(CommunityGroup, id=group_id, is_active=True)
    
    # Get all members with their roles
    memberships = GroupMembership.objects.filter(group=group).select_related(
        'user'
    ).order_by('role', '-joined_at')
    
    # Check if current user is member and their role
    user_membership = None
    try:
        user_membership = GroupMembership.objects.get(user=request.user, group=group)
    except GroupMembership.DoesNotExist:
        pass
    
    context = {
        'group': group,
        'memberships': memberships,
        'user_membership': user_membership,
        'can_manage': user_membership and user_membership.role in ['admin', 'moderator'],
    }
    return render(request, 'prediction_service/group_members.html', context)

@login_required
@csrf_exempt
def send_group_message(request):
    """Send a message to group chat"""
    from .models import CommunityGroup, GroupMembership, GroupMessage
    
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                group_id = data.get('group_id')
                content = data.get('content', '').strip()
                message_type = data.get('message_type', 'text')
                image = None
            else:
                # Form data (for file uploads)
                group_id = request.POST.get('group_id')
                content = request.POST.get('content', '').strip()
                message_type = request.POST.get('message_type', 'text')
                image = request.FILES.get('image')
            
            if not group_id:
                return JsonResponse({'success': False, 'message': 'Group ID is required'})
            
            if not content and not image:
                return JsonResponse({'success': False, 'message': 'Message content or image is required'})
            
            group = get_object_or_404(CommunityGroup, id=group_id, is_active=True)
            
            # Check if user is a member
            if not GroupMembership.objects.filter(user=request.user, group=group).exists():
                return JsonResponse({'success': False, 'message': 'Not a member of this group'})
            
            # Create message
            message = GroupMessage.objects.create(
                group=group,
                sender=request.user,
                message_type=message_type,
                content=content,
                image=image
            )
            
            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.username,
                    'created_at': message.created_at.isoformat(),
                    'message_type': message.message_type,
                    'image_url': message.image.url if message.image else None
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})