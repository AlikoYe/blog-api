from rest_framework import serializers
from apps.notifications.models import Notification
from apps.users.serializers import UserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    comment_author = UserSerializer(source="comment.author", read_only=True)
    post_title = serializers.CharField(source="comment.post.title", read_only=True)
    post_slug = serializers.CharField(source="comment.post.slug", read_only=True)
    comment_body = serializers.CharField(source="comment.body", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "is_read",
            "created_at",
            "comment_author",
            "post_title",
            "post_slug",
            "comment_body",
        )
        read_only_fields = ("id", "is_read", "created_at")
