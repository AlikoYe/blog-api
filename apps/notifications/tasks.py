import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_new_comment_task(comment_id: int) -> None:
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    from apps.blog.models import Comment
    from apps.notifications.models import Notification

    try:
        comment = Comment.objects.select_related("post__author", "author").get(
            id=comment_id
        )
    except Comment.DoesNotExist:
        logger.error(
            "process_new_comment_task failed - comment %d not found", comment_id
        )
        return

    post = comment.post
    author = comment.author

    if post.author != author:
        Notification.objects.create(
            recipient=post.author,
            comment=comment,
        )
        logger.info(
            'Notification created for %s - comment by %s on "%s"',
            post.author.email,
            author.email,
            post.slug,
        )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"post_comments_{post.slug}",
        {
            "type": "comment.created",
            "data": {
                "comment_id": comment.id,
                "author": {
                    "id": author.id,
                    "email": author.email,
                },
                "body": comment.body,
                "created_at": comment.created_at.isoformat(),
            },
        },
    )
    logger.info('WebSocket broadcast sent via Celery for post "%s"', post.slug)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def clear_expired_notifications() -> None:
    from datetime import timedelta

    from django.utils import timezone

    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=30)
    deleted_count, _ = Notification.objects.filter(created_at__lt=cutoff).delete()

    logger.info("Cleared %d expired notifications", deleted_count)
