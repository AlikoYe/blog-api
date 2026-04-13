import logging
import zoneinfo
from datetime import datetime
from django.utils import timezone as dj_timezone
from rest_framework import serializers
from apps.blog.models import Category, Comment, Post, Tag
from apps.users.serializers import UserSerializer

logger = logging.getLogger(__name__)

DATE_FORMAT_BY_LOCALE = {
    "en": "%B %d, %Y %H:%M",
    "ru": "%d %B %Y г. %H:%M",
    "kk": "%Y ж. %d %B %H:%M",
}
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "post", "author", "body", "created_at")
        read_only_fields = ("id", "post", "author", "created_at")


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    formatted_created_at = serializers.SerializerMethodField()
    formatted_updated_at = serializers.SerializerMethodField()

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source="tags",
        write_only=True,
        many=True,
        required=False,
    )

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "title",
            "slug",
            "body",
            "category",
            "category_id",
            "tags",
            "tag_ids",
            "status",
            "publish_at",
            "comments_count",
            "created_at",
            "updated_at",
            "formatted_created_at",
            "formatted_updated_at",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")

    def get_comments_count(self, obj: Post) -> int:
        return obj.comments.count()

    def get_formatted_created_at(self, obj: Post) -> str:
        return self._format_datetime(obj.created_at)

    def get_formatted_updated_at(self, obj: Post) -> str:
        return self._format_datetime(obj.updated_at)

    def _format_datetime(self, dt: datetime) -> str:
        request = self.context.get("request")

        user_tz = dj_timezone.utc
        if request and hasattr(request, "user") and request.user.is_authenticated:
            tz_name = getattr(request.user, "timezone", None)
            if tz_name:
                try:
                    user_tz = zoneinfo.ZoneInfo(tz_name)
                except (KeyError, zoneinfo.ZoneInfoNotFoundError):
                    pass

        local_dt = dt.astimezone(user_tz)

        lang = getattr(request, "LANGUAGE_CODE", "en") if request else "en"
        date_format = DATE_FORMAT_BY_LOCALE.get(lang, DEFAULT_DATE_FORMAT)

        return self._localized_format(local_dt, date_format, lang)

    def _localized_format(self, dt: datetime, fmt: str, lang: str) -> str:
        if lang == "ru":
            months = {
                1: "января",
                2: "февраля",
                3: "марта",
                4: "апреля",
                5: "мая",
                6: "июня",
                7: "июля",
                8: "августа",
                9: "сентября",
                10: "октября",
                11: "ноября",
                12: "декабря",
            }
            formatted = dt.strftime(fmt)
            eng_month = dt.strftime("%B")
            return formatted.replace(eng_month, months[dt.month])

        if lang == "kk":
            months = {
                1: "қаңтар",
                2: "ақпан",
                3: "наурыз",
                4: "сәуір",
                5: "мамыр",
                6: "маусым",
                7: "шілде",
                8: "тамыз",
                9: "қыркүйек",
                10: "қазан",
                11: "қараша",
                12: "желтоқсан",
            }
            formatted = dt.strftime(fmt)
            eng_month = dt.strftime("%B")
            return formatted.replace(eng_month, months[dt.month])

        return dt.strftime(fmt)
