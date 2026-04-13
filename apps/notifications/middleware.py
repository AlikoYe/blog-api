from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from apps.users.models import User


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = self._extract_token(query_string)
        if token:
            scope["user"] = await self._get_user(token)
        else:
            scope["user"] = AnonymousUser()

    def _extract_token(self, query_string: str) -> str:
        params = dict(
            pair.split("=", 1) for pair in query_string.split("&") if "=" in pair
        )
        return params.get("token", "")

    @database_sync_to_async
    def _get_user(self, token: str):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()
