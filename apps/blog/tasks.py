import logging
from celery import shared_task
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def invalidate_post_cache_task() -> None:
    from django.core.cache import cache
    from apps.blog.views import POSTS_CACHE_KEY_PREFIX, SUPPORTED_LANGUAGES

    for lang in SUPPORTED_LANGUAGES:
        cache.delete(f"{POSTS_CACHE_KEY_PREFIX}_{lang}")
    logger.info("Posts cache invalidated via Celery task")


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def publish_scheduled_posts() -> None:
    from apps.blog.models import Post
    from apps.blog.views import _publish_post_sse_event

    now = timezone.now()
    scheduled_posts = Post.objects.filter(
        status=Post.Status.SCHEDULED, published_at__lte=now
    )
    count = 0
    for post in scheduled_posts:
        post.status = Post.Status.PUBLISHED
        post.save(update_fields=["status", "updated_at"])
        _publish_post_sse_event(post)
        count += 1
    if count:
        logger.info("Published %d posts scheduled via Celery task", count)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_daily_stats() -> None:
    from apps.blog.models import Post, Comment
    from apps.users.models import User

    yesterday = timezone.now() - timedelta(days=1)
    new_posts = Post.objects.filter(created_at__gte=yesterday).count()
    new_comments = Comment.objects.filter(created_at__gte=yesterday).count()
    new_users = User.objects.filter(is_active=True).count()
    logger.info(
        "Daily stats - new posts: %d new comments: %d new users: %d",
        new_posts,
        new_comments,
        new_users,
    )
