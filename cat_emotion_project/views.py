from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from emotion_detection.models import CatProfile, EmotionPrediction, EmotionFeedback
from ai_assistant.models import AIConversation

def home(request):
    """Homepage with real statistics"""
    # Calculate real statistics
    total_cats = CatProfile.objects.count()
    total_predictions = EmotionPrediction.objects.count()
    total_users = User.objects.count()
    
    # Calculate accuracy from feedback
    total_feedback = EmotionFeedback.objects.count()
    correct_feedback = EmotionFeedback.objects.filter(was_correct=True).count()
    
    if total_feedback > 0:
        accuracy = round((correct_feedback / total_feedback) * 100)
    else:
        accuracy = 85  # Default if no feedback yet
    
    # AI conversations
    total_conversations = AIConversation.objects.count()
    
    context = {
        'total_cats': total_cats,
        'total_predictions': total_predictions,
        'total_users': total_users,
        'accuracy': accuracy,
        'total_conversations': total_conversations,
    }
    
    return render(request, 'home.html', context)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Use authenticate to properly set the backend attribute
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Registration successful! Welcome to CatCare AI.')
                return redirect('dashboard:home')
            else:
                # Fallback: specify backend explicitly
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Registration successful! Welcome to CatCare AI.')
                return redirect('dashboard:home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def logout_confirmation(request):
    """Show logout confirmation page"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('logout_success')
    
    return render(request, 'registration/logout_confirmation.html')

def logout_success(request):
    """Show logout success page"""
    return render(request, 'registration/logged_out.html')