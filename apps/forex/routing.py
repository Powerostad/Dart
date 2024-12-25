from django.urls import re_path
from apps.forex.consumers import TradingConsumer

websocket_urlpatterns = [
    re_path(r"ws/predict/$", TradingConsumer.as_asgi())
]