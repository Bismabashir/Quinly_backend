from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]

        if token:
            try:
                access_token = AccessToken(token)
                user = await self.get_user(access_token["user_id"])
                scope["user"] = user  # Attach user to WebSocket scope
            except Exception:
                scope["user"] = AnonymousUser()  # Fallback to anonymous user

        return await super().__call__(scope, receive, send)

    @staticmethod
    async def get_user(user_id):
        """Fetch user asynchronously"""
        return await User.objects.aget(id=user_id)
