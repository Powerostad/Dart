from django.urls import path
from apps.chatbot.consumers import AIChatbotConsumer


websocket_urlpatterns = [
    path("ws/chatbot/", AIChatbotConsumer.as_asgi()),
]