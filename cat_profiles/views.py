from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator

from emotion_detection.models import CatProfile, DietPlan, EmotionPrediction, PhotoGallery

@login_required
def cat_list(request):
    """List all user's cats"""
    from prediction_service.models import CommunityPost
    
    cats = CatProfile.objects.filter(owner=request.user).order_by('-created_at')
    
    # Add prediction counts and photo counts for each cat
    for cat in cats:
        cat.prediction_count = EmotionPrediction.objects.filter(cat=cat).count()
        
        # Count photos from all sources
        gallery_photos = PhotoGallery.objects.filter(cat=cat).count()
        prediction_photos = EmotionPrediction.objects.filter(
            cat=cat, 
            prediction_type='image',
            file_path__isnull=False
        ).exclude(file_path='').count()
        community_photos = CommunityPost.objects.filter(
            cat=cat,
            image__isnull=False
        ).exclude(image='').count()
        
        cat.photo_count = gallery_photos + prediction_photos + community_photos
    
    context = {
        'cats': cats,
    }
    return render(request, 'cat_profiles/list.html', context)

@login_required
def add_cat(request):
    """Add a new cat profile"""
    if request.method == 'POST':
        try:
            cat = CatProfile.objects.create(
                owner=request.user,
                name=request.POST.get('name'),
                breed=request.POST.get('breed', ''),
                age=int(request.POST.get('age')),
                gender=request.POST.get('gender'),
                weight=float(request.POST.get('weight')) if request.POST.get('weight') else None,
                description=request.POST.get('description', ''),
                photo=request.FILES.get('photo')
            )
            messages.success(request, f'{cat.name} has been added successfully!')
            return redirect('cat_profiles:detail', cat_id=cat.id)
        except Exception as e:
            messages.error(request, f'Error adding cat: {str(e)}')
    
    return render(request, 'cat_profiles/add.html')

@login_required
def cat_detail(request, cat_id):
    """Cat profile detail view"""
    from prediction_service.models import CommunityPost
    
    cat = get_object_or_404(CatProfile, id=cat_id, owner=request.user)
    
    # Recent predictions
    recent_predictions = EmotionPrediction.objects.filter(cat=cat).order_by('-created_at')[:10]
    
    # Recent photos
    recent_photos = PhotoGallery.objects.filter(cat=cat).order_by('-created_at')[:6]
    
    # Diet plans
    diet_plans = DietPlan.objects.filter(cat=cat, is_active=True)
    
    # Statistics - count photos from all sources
    total_predictions = EmotionPrediction.objects.filter(cat=cat).count()
    gallery_photos = PhotoGallery.objects.filter(cat=cat).count()
    prediction_photos = EmotionPrediction.objects.filter(
        cat=cat,
        prediction_type='image',
        file_path__isnull=False
    ).exclude(file_path='').count()
    community_photos = CommunityPost.objects.filter(
        cat=cat,
        image__isnull=False
    ).exclude(image='').count()
    total_photos = gallery_photos + prediction_photos + community_photos
    
    context = {
        'cat': cat,
        'recent_predictions': recent_predictions,
        'recent_photos': recent_photos,
        'diet_plans': diet_plans,
        'total_predictions': total_predictions,
        'total_photos': total_photos,
    }
    return render(request, 'cat_profiles/detail.html', context)

@login_required
def edit_cat(request, cat_id):
    """Edit cat profile"""
    cat = get_object_or_404(CatProfile, id=cat_id, owner=request.user)
    
    if request.method == 'POST':
        try:
            cat.name = request.POST.get('name')
            cat.breed = request.POST.get('breed', '')
            cat.age = int(request.POST.get('age'))
            cat.gender = request.POST.get('gender')
            cat.weight = float(request.POST.get('weight')) if request.POST.get('weight') else None
            cat.description = request.POST.get('description', '')
            
            if request.FILES.get('photo'):
                cat.photo = request.FILES.get('photo')
            
            cat.save()
            messages.success(request, f'{cat.name}\'s profile has been updated!')
            return redirect('cat_profiles:detail', cat_id=cat.id)
        except Exception as e:
            messages.error(request, f'Error updating cat: {str(e)}')
    
    context = {
        'cat': cat,
    }
    return render(request, 'cat_profiles/edit.html', context)

@login_required
def delete_cat(request, cat_id):
    """Delete cat profile"""
    cat = get_object_or_404(CatProfile, id=cat_id, owner=request.user)
    
    if request.method == 'POST':
        cat_name = cat.name
        cat.delete()
        messages.success(request, f'{cat_name}\'s profile has been deleted.')
        return redirect('cat_profiles:list')
    
    context = {
        'cat': cat,
    }
    return render(request, 'cat_profiles/delete.html', context)

@login_required
def diet_plans(request, cat_id):
    """View cat's diet plans"""
    cat = get_object_or_404(CatProfile, id=cat_id, owner=request.user)
    plans = DietPlan.objects.filter(cat=cat).order_by('-created_at')
    
    context = {
        'cat': cat,
        'diet_plans': plans,
    }
    return render(request, 'cat_profiles/diet_plans.html', context)

@login_required
def add_diet_plan(request, cat_id):
    """Add a new diet plan"""
    cat = get_object_or_404(CatProfile, id=cat_id, owner=request.user)
    
    if request.method == 'POST':
        try:
            # Parse food items and schedule from form
            food_items = []
            schedule = []
            
            # Simple parsing - in production you'd want more robust handling
            food_names = request.POST.getlist('food_name[]')
            food_quantities = request.POST.getlist('food_quantity[]')
            
            for name, quantity in zip(food_names, food_quantities):
                if name and quantity:
                    food_items.append({'name': name, 'quantity': quantity})
            
            schedule_times = request.POST.getlist('schedule_time[]')
            schedule_foods = request.POST.getlist('schedule_food[]')
            
            for time, food in zip(schedule_times, schedule_foods):
                if time and food:
                    schedule.append({'time': time, 'food': food})
            
            diet_plan = DietPlan.objects.create(
                cat=cat,
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                food_items=food_items,
                feeding_schedule=schedule,
                notes=request.POST.get('notes', ''),
                is_active=request.POST.get('is_active') == 'on'
            )
            
            messages.success(request, f'Diet plan "{diet_plan.title}" has been created!')
            return redirect('cat_profiles:diet_plans', cat_id=cat.id)
        except Exception as e:
            messages.error(request, f'Error creating diet plan: {str(e)}')
    
    context = {
        'cat': cat,
    }
    return render(request, 'cat_profiles/add_diet_plan.html', context)
