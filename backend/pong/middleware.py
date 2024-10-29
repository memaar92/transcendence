import jwt
from django.conf import settings
from channels.auth import AuthMiddlewareStack
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
import logging

User = get_user_model()

logger = logging.getLogger("JWT WS Middleware")

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Get the token from the headers
        headers = dict(scope['headers'])
        cookies = headers.get(b'cookie', b'').decode()
        token = None

        # Extract token from cookies
        for cookie in cookies.split(';'):
            if 'access_token' in cookie:
                token = cookie.split('=')[-1]
                break

        if token:
            try:
                # Decode the token to get user data
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                scope['user'] = await self.get_user(payload['user_id'])
                print(f"User: {scope['user']}")
            except jwt.ExpiredSignatureError:
                logger.error("Token expired")
                scope['user'] = AnonymousUser()
            except jwt.InvalidTokenError:
                logger.error("Invalid token")
                scope['user'] = AnonymousUser()
            except Exception as e:
                logger.error(e)
                scope['user'] = AnonymousUser()
        else:
            logger.error("No token found")
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()

def jwt_auth_middleware_stack(inner):
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))