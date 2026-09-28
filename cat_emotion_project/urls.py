"""
URL configuration for cat_emotion_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # Changed to use custom view
    
    # Custom authentication URLs
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/register/', views.register, name='register'),
    path('auth/logout-confirm/', views.logout_confirmation, name='logout_confirm'),
    path('auth/logout-success/', views.logout_success, name='logout_success'),
    
    # Django Allauth URLs (includes Google OAuth)
    path('accounts/', include('allauth.urls')),
    
    # App URLs
    path('dashboard/', include('dashboard.urls')),
    path('emotion/', include('emotion_detection.urls')),
    path('cats/', include('cat_profiles.urls')),
    path('ai/', include('ai_assistant.urls')),
    path('predictions/', include('prediction_service.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])