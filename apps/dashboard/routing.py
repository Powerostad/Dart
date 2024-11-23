from django.urls import re_path
from apps.dashboard.consumers import SignalConsumer

websocket_urlpatterns = [
    re_path(r'ws/predict/(?P<symbol>\w+)/$', SignalConsumer.as_asgi()),
]