from django.urls import path
from . import views

app_name = 'emotion_detection'

urlpatterns = [
    path('', views.emotion_detection_view, name='detection'),
    path('predict/audio/', views.predict_audio_emotion, name='predict_audio'),
    path('predict/image/', views.predict_image_emotion, name='predict_image'),
    path('predict-tab/', views.prediction_tab_view, name='prediction_tab'),
    path('history/', views.prediction_history, name='history'),
    path('feedback/submit/', views.submit_feedback, name='submit_feedback'),
    path('feedback/patterns/', views.get_learned_patterns, name='get_learned_patterns'),
    path('feedback/next/', views.get_next_feedback_prediction, name='get_next_feedback'),
]