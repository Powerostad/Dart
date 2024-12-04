from django.urls import re_path
from apps.dashboard.consumers import SignalConsumer

websocket_urlpatterns = [
    re_path(r'ws/predict/$', SignalConsumer.as_asgi()),
]