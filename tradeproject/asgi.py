import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeproject.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from apps.dashboard.middlewares import JWTAuthMiddleware
from apps.dashboard.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            websocket_urlpatterns  # Define your WebSocket routes
        )
    ),
})
