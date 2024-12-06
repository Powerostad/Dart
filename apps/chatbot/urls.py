from django.urls import path
from apps.chatbot import views

urlpatterns = [
    path('history/', views.ChatbotHistoryView.as_view(), name='chatbot_history'),
]