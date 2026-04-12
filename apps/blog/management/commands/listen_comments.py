import asyncio
import json
import logging

from django.core.management.base import BaseCommand
from redis import asyncio as aioredis
from apps.blog.services import COMMENTS_CHANNEL
from settings.conf import BLOG_REDIS_URL

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Subscribe to Redis comments channel using async and print events"

    def handle(self, *args, **options) -> None:
        self.stdout.write(
            self.style.SUCCESS(
                f'Subscribing to Redis channel: "{COMMENTS_CHANNEL}" (async)'
            )
        )
        self.stdout.write("Waiting for new comments... (Ctrl+C to stop)\n")

        try:
            asyncio.run(self._listen())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nUnsubscribed. Goodbye!"))

    async def _listen(self) -> None:
        client = aioredis.from_url(BLOG_REDIS_URL)
        pubsub = client.pubsub()
        await pubsub.subscribe(COMMENTS_CHANNEL)

        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    data = json.loads(message["data"])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\n--- New Comment ---\n"
                            f"Post:   {data['post_slug']}\n"
                            f"Author: {data['author']}\n"
                            f"Body:   {data['body']}\n"
                        )
                    )
                    logger.info(
                        'Received comment event: post="%s" by %s',
                        data["post_slug"],
                        data["author"],
                    )
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(
                        "Invalid message received: %s — %s", message["data"], e
                    )
        finally:
            await pubsub.unsubscribe(COMMENTS_CHANNEL)
            await pubsub.aclose()
            await client.aclose()
