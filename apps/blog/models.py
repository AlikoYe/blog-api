from django.db import models
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class Category(models.Model):
    name = models.CharField(max_length=100 , unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self) -> str:
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50 , unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'tag'
        verbose_name_plural = 'tags'

    def __str__(self) -> str:
        return self.name

class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'DRAFT'
        PUBLISHED =  'PUBLISHED', 'PUBLISHED'

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE , related_name='posts',)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    category = models.ForeignKey(Category , on_delete=models.SET_NULL, null=True,blank=True, related_name='posts',)
    tags = models.ManyToManyField(Tag , blank=True, related_name='posts',)
    status = models.CharField(max_length=10, choices=Status.choices , default=Status.DRAFT,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'post'
        verbose_name_plural = 'posts'

    def __str__(self) -> str:
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments',)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE , related_name='comments',)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'comment'
        verbose_name_plural = 'comments'

    def __str__(self) -> str:
        return f'Comment by {self.author} on {self.post}'