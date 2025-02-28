import os
import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack  # Use this instead
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeproject.settings')
django.setup()

from apps.dashboard.middlewares import JWTAuthMiddleware
from apps.forex.routing import websocket_urlpatterns as dashboard_websocket_urlpatterns
from apps.chatbot.routing import websocket_urlpatterns as chatbot_websocket_urlpatterns

# Combine WebSocket URL patterns
websocket_urlpatterns = dashboard_websocket_urlpatterns + chatbot_websocket_urlpatterns

# Define JWT middleware stack correctly
def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": SessionMiddlewareStack(
        JWTAuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
