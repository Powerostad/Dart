import os
import django
from channels.sessions import SessionMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeproject.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from apps.dashboard.middlewares import JWTAuthMiddleware
from apps.dashboard.routing import websocket_urlpatterns as dashboard_websocket_urlpatterns
from apps.chatbot.routing import websocket_urlpatterns as chatbot_websocket_urlpatterns

websocket_urlpatterns = dashboard_websocket_urlpatterns + chatbot_websocket_urlpatterns

def JWTAuthMiddlewareStack(inner):
    """
    Convenience wrapper to add JWT authentication to an application.
    Can be used in routing.py
    """
    return SessionMiddleware(JWTAuthMiddleware(inner))

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
