from jwt import decode, exceptions
from django.conf import settings
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]

        if token:
            try:
                decoded_data = AccessToken(token)
                user = await self.get_user(decoded_data['user_id'])
                scope['user'] = user
            except exceptions.InvalidTokenError:
                scope['user'] = AnonymousUser()  # Invalid token
        else:
            scope['user'] = AnonymousUser()  # No token provided

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()