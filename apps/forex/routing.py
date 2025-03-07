from django.urls import re_path
from apps.forex import consumers

websocket_urlpatterns = [
    re_path(r'ws/market/(?P<symbol>\w+)/(?P<timeframe>\w+)/$', consumers.MT5DataConsumer.as_asgi()),
]