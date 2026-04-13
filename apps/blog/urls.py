from rest_framework.routers import DefaultRouter
from apps.blog.views import PostViewSet
from django.urls import path
from apps.blog.stats import StatsView
from apps.blog.sse import post_stream_view

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
urlpatterns = [
    path("stats/", StatsView.as_view(), name="stats"),
    path("posts/stream/", post_stream_view, name="post_stream"),
] + router.urls
