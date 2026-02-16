
import logging
from apps.users.throttles import PostCreationThrottle
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action
from apps.blog.models import Post
from apps.blog.permissions import IsOwnerOrReadOnly
from apps.blog.serializers import CommentSerializer , PostSerializer
from apps.blog.services import publish_comment_event
logger = logging.getLogger(__name__)

POSTS_CACHE_KEY = 'posts_list'
POSTS_CACHE_TTL = 60

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        if self.action == 'list':
            return Post.objects.filter(status=Post.Status.PUBLISHED,).select_related('author' , 'category').prefetch_related('tags')

        return Post.objects.select_related('author' , 'category').prefetch_related('tags')

    def get_permissions(self) -> list:
        if self.action in ('list' , 'retrieve'):
            return [AllowAny()]
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsAuthenticated() , IsOwnerOrReadOnly()]

    def get_throttles(self) -> list:
        if self.action == 'create':
            return [PostCreationThrottle()]
        return []

    def list(self, request: Request, *args, **kwargs) -> Response:
        cached_data = cache.get(POSTS_CACHE_KEY)
        if cached_data is not None:
            logger.debug('Posts list serves from cache')
            return Response(cached_data)
        logger.debug('Posts list cache miss - querying database')
        response = super().list(request, *args, **kwargs)
        cache.set(POSTS_CACHE_KEY, response.data, POSTS_CACHE_TTL)
        return response


    def perform_create(self, serializer: PostSerializer) -> None:
        try:
            post = serializer.save(author=self.request.user)
            cache.delete(POSTS_CACHE_KEY)
            logger.info('Post created: "%s" by %s - cache invalidated', post.slug, self.request.user.email)
        except Exception:
            logger.exception('Post creation failed by %s', self.request.user.email)
            raise

    def perform_update(self, serializer: PostSerializer) -> None:
        try:
            post = serializer.save()
            cache.delete(POSTS_CACHE_KEY)
            logger.info('Post updated: "%s" by %s - cache invalidated', post.slug, self.request.user.email)
        except Exception:
            logger.exception('Post update failed by %s', self.request.user.email)
            raise


    def perform_destroy(self, instance: Post) -> None:
        logger.info('Post deleted: "%s" by %s', instance.slug, self.request.user.email)
        try:
            instance.delete()
            cache.delete(POSTS_CACHE_KEY)
            logger.info('Post cache invalidated after deletion')
        except Exception:
            logger.exception('Post deletion failed: "%s"', instance.slug)
            raise

    @action(detail=True, methods=['get' , 'post'] , url_path='comments')
    def comments(self, request: Request, slug: str = None) -> Response:
        post = self.get_object()
        if request.method == 'GET':
            return self._list_comments(post)
        return self._create_comment(request, post)

    def _list_comments(self, post: Post) -> Response:
        comments = post.comments.select_related('author').all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def _create_comment(self, request: Request, post: Post) -> Response:
        if not request.user.is_authenticated:
            return Response({'detail':'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED,)
        logger.info('Comment attempt on "%s" by %s', post.slug, self.request.user.email,)
        serializer = CommentSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning('Comment creation failed: %s', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = serializer.save(author=request.user, post=post)
            logger.info('Comment created on "%s" by %s',post.slug,request.user.email,)
            # Publish event to Redis pub/sub
            publish_comment_event(post_slug=post.slug,author_email=request.user.email,body=comment.body,)
        except Exception:
            logger.exception('Comment creation failed on "%s"', post.slug)
            return Response({'detail': 'Comment creation failed.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR,)
        return Response(serializer.data, status=status.HTTP_201_CREATED)