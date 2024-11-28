from urllib.parse import parse_qs

from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

User = get_user_model()


@database_sync_to_async
def get_user(validated_token):
    """
    Retrieve the user from the validated token payload.

    :param validated_token: Decoded token payload
    :return: User instance or AnonymousUser
    """
    try:
        user_id = validated_token['user_id']
        user = User.objects.get(id=user_id)
        return user
    except (KeyError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom WebSocket middleware for JWT authentication.
    Supports token authentication via query parameters or headers.
    """

    async def __call__(self, scope, receive, send):
        # Close any old database connections
        close_old_connections()

        # First, try to authenticate from query parameters
        query_params = parse_qs(scope.get('query_string', b'').decode())
        token = query_params.get('token', [None])[0]

        # If no token in query params, check authorization header
        if not token and 'headers' in scope:
            for name, value in scope['headers']:
                if name.decode('ascii') == 'authorization':
                    try:
                        # Expect header in format: 'Bearer <token>'
                        token = value.decode('ascii').split()[1]
                    except (IndexError, UnicodeDecodeError):
                        token = None

        # If token found, validate it
        if token:
            try:
                # Decode the token without verification (channels can't verify)
                UntypedToken(token)

                # Use Django REST framework's JWT authentication for validation
                jwt_authenticator = JWTAuthentication()
                validated_token = jwt_authenticator.get_validated_token(token)

                # Get the user
                scope['user'] = await get_user(validated_token)
            except (InvalidToken, TokenError):
                # Authentication failed
                scope['user'] = AnonymousUser()
        else:
            # No token provided
            scope['user'] = AnonymousUser()

        # Continue the middleware chain
        return await super().__call__(scope, receive, send)