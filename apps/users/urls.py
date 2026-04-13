from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.users.views import (
    CustomTokenRefreshView,
    CustomTokenObtainPairView,
    LanguageViewSet,
    RegisterViewSet,
    TimezoneViewSet,
)

router = DefaultRouter()
router.register(r"register", RegisterViewSet, basename="register")

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path(
        "language/",
        LanguageViewSet.as_view({"patch": "partial_update"}),
        name="user_language",
    ),
    path(
        "timezone/",
        TimezoneViewSet.as_view({"patch": "partial_update"}),
        name="user_timezone",
    ),
]
urlpatterns += router.urls
