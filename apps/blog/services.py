import json
import logging
import redis
from settings.conf import BLOG_REDIS_URL

logger = logging.getLogger(__name__)
COMMENTS_CHANNEL = "comments"


def get_redis_client() -> redis.Redis:
    return redis.from_url(BLOG_REDIS_URL)


def publish_comment_event(post_slug: str, author_email: str, body: str) -> None:
    event = {
        "post_slug": post_slug,
        "author": author_email,
        "body": body,
    }

    try:
        client = get_redis_client()
        client.publish(COMMENTS_CHANNEL, json.dumps(event))
        logger.info(
            'Published comment event to Redis: post="%s" by %s', post_slug, author_email
        )
    except redis.ConnectionError:
        logger.exception("Failed to publish comment event - Redis connection error")
