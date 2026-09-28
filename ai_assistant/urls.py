from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.ai_chat, name='chat'),
    path('ask/', views.ask_question, name='ask'),
    path('history/', views.conversation_history, name='history'),
    path('clear-history/', views.clear_history, name='clear_history'),
    path('delete-conversation/', views.delete_conversation, name='delete_conversation'),
]