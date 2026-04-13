import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from apps.blog.models import Post

logger = logging.getLogger(__name__)

CLOSE_CODE_UNAUTHENTICATED = 4001
CLOSE_CODE_NOT_FOUND = 4004
GROUP_PREFIX = "post_comments_"


class CommentConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        self.group_name = f"{GROUP_PREFIX}{self.slug}"

        user = self.scope.get("user")
        if not user or user.is_anonymous:
            logger.warning("WebSocked rejected", self.slug)
            await self.close(code=CLOSE_CODE_UNAUTHENTICATED)
            return

        post_exists = await self._post_exists(self.slug)
        if not post_exists:
            logger.warning("WebSocked rejected", self.slug)
            await self.close(code=CLOSE_CODE_NOT_FOUND)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info(
            "WebSocked connected",
            user.email,
            self.slug,
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        user = self.scope.get("user")
        email = user.email if user and not user.is_anonymous else "anonymous"
        logger.info(
            "WebSocked disconnected: user=%s post=%s code=%s",
            email,
            getattr(self, "slug", "?"),
            close_code,
        )

    async def receive_json(self, content, **kwargs):
        pass

    async def comment_created(self, event):
        await self.send_json(event["data"])

    @database_sync_to_async
    def _post_exists(self, slug: str) -> bool:
        return Post.objects.filter(slug=slug).exists()
