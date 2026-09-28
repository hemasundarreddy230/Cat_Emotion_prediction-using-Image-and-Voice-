from django.urls import path
from . import views

app_name = 'prediction_service'

urlpatterns = [
    # Dashboard
    path('', views.prediction_dashboard, name='dashboard'),
    
    # Enhanced Prediction
    path('predict/', views.enhanced_predict, name='enhanced_predict'),
    
    # Community Features
    path('community/', views.community_feed, name='community_feed'),
    path('community/create/', views.create_community_post, name='create_post'),
    path('api/like/', views.toggle_like, name='toggle_like'),
    path('api/comment/', views.add_comment, name='add_comment'),
    
    # Group Features
    path('groups/', views.groups_list, name='groups_list'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/join/', views.join_group, name='join_group'),
    path('groups/<int:group_id>/leave/', views.leave_group, name='leave_group'),
    path('groups/<int:group_id>/chat/', views.group_chat, name='group_chat'),
    path('groups/<int:group_id>/members/', views.group_members, name='group_members'),
    path('api/group-message/', views.send_group_message, name='send_group_message'),
    
    # User Profiles
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('api/follow/', views.toggle_follow, name='toggle_follow'),
    
    # Veterinary Services
    path('map/', views.veterinary_map, name='veterinary_map'),
    path('api/review/', views.add_service_review, name='add_service_review'),
]