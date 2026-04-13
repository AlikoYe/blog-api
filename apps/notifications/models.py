import logging
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.blog.models import Comment

logger = logging.getLogger(__name__)


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("recipient"),
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("comment"),
    )
    is_read = models.BooleanField(default=False, verbose_name=_("read"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))

    class Meta:
        ordering = [
            "-created_at",
        ]
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")

    def __str__(self) -> str:
        return f"Notification for {self.recipient} - comment {self.comment_id}"
