from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('profile/', views.user_profile, name='profile'),
    path('alerts/', views.health_alerts, name='alerts'),
    path('gallery/', views.photo_gallery, name='gallery'),
    path('map/', views.map_view, name='map'),
    path('analytics/', views.analytics_data, name='analytics_data'),
]