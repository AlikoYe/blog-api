from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.users.views import RegisterViewSet , CustomTokenRefreshView , CustomTokenObtainPairView

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register')

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]
urlpatterns += router.urls
