import logging
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from apps.users.throttles import PostCreationThrottle
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import get_language, gettext_lazy as _
from rest_framework.request import Request
from rest_framework.decorators import action
from apps.blog.models import Post
from apps.blog.permissions import IsOwnerOrReadOnly
from apps.blog.serializers import CommentSerializer, PostSerializer
from apps.blog.services import publish_comment_event

logger = logging.getLogger(__name__)

POSTS_CACHE_KEY_PREFIX = "posts_list"
POSTS_CACHE_TTL = 60
SUPPORTED_LANGUAGES = ("en", "ru", "kk")


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    lookup_field = "slug"

    def get_queryset(self):
        if self.action == "list":
            return (
                Post.objects.filter(
                    status=Post.Status.PUBLISHED,
                )
                .select_related("author", "category")
                .prefetch_related("tags")
            )

        return Post.objects.select_related("author", "category").prefetch_related(
            "tags"
        )

    def get_permissions(self) -> list:
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_throttles(self) -> list:
        if self.action == "create":
            return [PostCreationThrottle()]
        return []

    @extend_schema(
        tags=["Posts"],
        summary="List published posts",
        description=(
            "Return a paginated list of published posts. No authentication required. "
            "Results are cached per language for 60 seconds. "
            "Use ?lang=ru or ?lang=kk to get responses in Russian or Kazakh. "
            "Category names are returned in the active language."
        ),
        responses={
            200: PostSerializer(many=True),
        },
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        lang = get_language() or "en"
        cache_key = f"{POSTS_CACHE_KEY_PREFIX}_{lang}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug("Posts list served from cache (lang=%s)", lang)
            return Response(cached_data)
        logger.debug("Posts list cache miss (lang=%s) - querying database", lang)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, POSTS_CACHE_TTL)
        return response

    @extend_schema(
        tags=["Posts"],
        summary="Create a new post",
        description=(
            "Create a new blog post. Authentication required. "
            "The authenticated user is set as the author. "
            "Invalidates the posts list cache for all languages. "
            "Rate limited to 20 requests per minute per user."
        ),
        request=PostSerializer,
        responses={
            201: PostSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication required."),
            429: OpenApiResponse(description="Rate limit exceeded."),
        },
        examples=[
            OpenApiExample(
                "Create post request",
                value={
                    "title": "My First Post",
                    "slug": "my-first-post",
                    "body": "This is the content.",
                    "category_id": 1,
                    "tag_ids": [1, 2],
                    "status": "published",
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new post."""
        return super().create(request, *args, **kwargs)

    def _invalidate_posts_cache(self) -> None:
        for lang in SUPPORTED_LANGUAGES:
            cache.delete(f"{POSTS_CACHE_KEY_PREFIX}_{lang}")
        logger.debug("Posts cache invalidated for all languages")

    def perform_create(self, serializer: PostSerializer) -> None:
        try:
            post = serializer.save(author=self.request.user)
            self._invalidate_posts_cache()
            logger.info('Post created: "%s" by %s', post.slug, self.request.user.email)
        except Exception:
            logger.exception("Post creation failed by %s", self.request.user.email)
            raise

    def perform_update(self, serializer: PostSerializer) -> None:
        try:
            post = serializer.save()
            self._invalidate_posts_cache()
            logger.info('Post updated: "%s" by %s', post.slug, self.request.user.email)
        except Exception:
            logger.exception("Post update failed by %s", self.request.user.email)
            raise

    @extend_schema(
        tags=["Posts"],
        summary="Delete own post",
        description=(
            "Delete a post. Authentication required. "
            "Only the post author can delete. "
            "Invalidates the posts list cache for all languages."
        ),
        responses={
            204: OpenApiResponse(description="Post deleted."),
            401: OpenApiResponse(description="Authentication required."),
            403: OpenApiResponse(description="Not the post author."),
            404: OpenApiResponse(description="Post not found."),
        },
    )
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete own post."""
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance: Post) -> None:
        slug = instance.slug
        try:
            instance.delete()
            self._invalidate_posts_cache()
            logger.info('Post deleted: "%s" by %s', slug, self.request.user.email)
        except Exception:
            logger.exception('Post deletion failed: "%s"', slug)
            raise

    @extend_schema(
        tags=["Comments"],
        summary="List or create comments",
        description=(
            "GET: List all comments for a post. No authentication required. "
            "POST: Add a comment to a post. Authentication required. "
            'Publishing a comment triggers a Redis pub/sub event on the "comments" channel.'
        ),
        request=CommentSerializer,
        responses={
            200: CommentSerializer(many=True),
            201: CommentSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication required (POST only)."),
            404: OpenApiResponse(description="Post not found."),
        },
        examples=[
            OpenApiExample(
                "Create comment request",
                value={"body": "Great post!"},
                request_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request: Request, slug: str = None) -> Response:
        post = self.get_object()
        if request.method == "GET":
            return self._list_comments(post)
        return self._create_comment(request, post)

    def _list_comments(self, post: Post) -> Response:
        comments = post.comments.select_related("author").all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def _create_comment(self, request: Request, post: Post) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {"detail": _("Authentication required.")},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        logger.info(
            'Comment attempt on "%s" by %s',
            post.slug,
            self.request.user.email,
        )
        serializer = CommentSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(_("Comment creation failed: %s"), serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = serializer.save(author=request.user, post=post)
            logger.info(
                'Comment created on "%s" by %s',
                post.slug,
                request.user.email,
            )
            # Publish event to Redis pub/sub
            publish_comment_event(
                post_slug=post.slug,
                author_email=request.user.email,
                body=comment.body,
            )
        except Exception:
            logger.exception('Comment creation failed on "%s"', post.slug)
            return Response(
                {"detail": "Comment creation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
