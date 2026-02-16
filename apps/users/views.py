
import logging
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from apps.users.serializers import RegisterSerializer
from rest_framework_simplejwt.exceptions import TokenError , InvalidToken
from rest_framework_simplejwt.views import TokenObtainPairView , TokenRefreshView
from apps.users.throttles import LoginThrottle , RegisterThrottle
logger = logging.getLogger(__name__)


class RegisterViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    throttle_classes = (RegisterThrottle,)
    def create(self, request: Request) -> Response:
        logger.info('Registration attempt for email: %s' , request.data['email'])
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning('Registration failed: %s' , serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
        except Exception:
            logger.exception('Registration failed unexpected error')
            return Response({'detail': 'Registration failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,)
        logger.info('User registered successfully: %s' , user.email)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = (LoginThrottle,)
    def post(self, request: Request, *args, **kwargs) -> Response:
        email = request.data.get('email' , 'unknown')
        logger.info('Login attempt for email: %s' , email)

        try:
            response = super().post(request, *args, **kwargs)
            logger.info('Login is successful for email: %s' , email)
            return response
        except (InvalidToken, TokenError) as e:
            logger.warning('Login failed for email: %s - %s' , email, str(e))
            raise
        except Exception:
            logger.exception('Login failed for email: %s - unexpected error' , email)
            raise

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        logger.info('Token refresh attempt')

        try:
            response = super().post(request, *args, **kwargs)
            logger.info('Token refresh is successful')
            return response
        except (InvalidToken, TokenError) as e:
            logger.warning('Token refresh failed: %s',str(e))
            raise
        except Exception:
            logger.exception('Token refresh failed - unexpected error')
            raise