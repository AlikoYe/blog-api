import logging
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)
CATEGORY_NAME_MAX_LENGTH = 100
TAG_NAME_MAX_LENGTH = 50
POST_TITLE_MAX_LENGTH = 200
POST_STATUS_MAX_LENGTH = 10


class Category(models.Model):
    name = models.CharField(
        max_length=CATEGORY_NAME_MAX_LENGTH, unique=True, verbose_name=_("name")
    )
    slug = models.SlugField(unique=True, verbose_name=_("slug"))

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH, unique=True, verbose_name=_("name")
    )
    slug = models.SlugField(unique=True, verbose_name=_("slug"))

    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("author"),
    )
    title = models.CharField(max_length=POST_TITLE_MAX_LENGTH, verbose_name=_("title"))
    slug = models.SlugField(unique=True, verbose_name=_("slug"))
    body = models.TextField(verbose_name=_("body"))
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name=_("category"),
    )
    tags = models.ManyToManyField(
        Tag, blank=True, related_name="posts", verbose_name=_("tags")
    )
    status = models.CharField(
        max_length=POST_STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("status"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("updated at"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "post"
        verbose_name_plural = "posts"

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("post"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("author"),
    )
    body = models.TextField(verbose_name=_("body"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "comment"
        verbose_name_plural = "comments"

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.post}"
