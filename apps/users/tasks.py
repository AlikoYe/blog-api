import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_welcome_email_task(user_id: int) -> None:
    from apps.users.models import User
    from apps.users.services import send_welcome_email

    try:
        user = User.objects.get(id=user_id)
        send_welcome_email(user)
        logger.info("Welcome email task completed for user %s", user.email)
    except User.DoesNotExist:
        logger.info("Welcome email task failed for user %s", user.id)
