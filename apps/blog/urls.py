from rest_framework.routers import DefaultRouter
from apps.blog.views import PostViewSet
from django.urls import path
from apps.blog.stats import StatsView

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
urlpatterns = [
    path("stats/", StatsView.as_view(), name="stats"),
] + router.urls
