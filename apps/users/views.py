import logging
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils.translation import gettext_lazy as _
from apps.users.serializers import (
    LanguageSerializer,
    RegisterSerializer,
    TimezoneSerializer,
    UserSerializer,
)
from apps.users.throttles import LoginThrottle, RegisterThrottle

logger = logging.getLogger(__name__)


class RegisterViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    throttle_classes = (RegisterThrottle,)

    @extend_schema(
        tags=["Auth"],
        summary="Register a new user",
        description=(
            "Create a new user account and return user data with JWT tokens. "
            "No authentication required. "
            "A welcome email is sent in the user's chosen language. "
            "Rate limited to 5 requests per minute per IP."
        ),
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description="User created successfully with JWT tokens.",
            ),
            400: OpenApiResponse(
                description="Validation error (invalid email, passwords do not match, etc.)"
            ),
            429: OpenApiResponse(description="Rate limit exceeded."),
        },
        examples=[
            OpenApiExample(
                "Register request",
                value={
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "password": "securepass123",
                    "password_confirm": "securepass123",
                    "language": "en",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Register response",
                value={
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "date_joined": "2025-01-15T10:30:00Z",
                        "avatar": None,
                        "language": "en",
                        "timezone": "UTC",
                    },
                    "tokens": {
                        "refresh": "eyJ...",
                        "access": "eyJ...",
                    },
                },
                response_only=True,
            ),
        ],
    )
    def create(self, request: Request) -> Response:
        logger.info("Registration attempt for email: %s", request.data["email"])
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(_("Registration failed: %s"), serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
        except Exception:
            logger.exception("Registration failed unexpected error")
            return Response(
                {"detail": "Registration failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        logger.info("User registered successfully: %s", user.email)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = (LoginThrottle,)

    @extend_schema(
        tags=["Auth"],
        summary="Login — obtain JWT token pair",
        description=(
            "Authenticate with email and password to receive access and refresh tokens. "
            "No authentication required. "
            "Rate limited to 10 requests per minute per IP."
        ),
        responses={
            200: OpenApiResponse(description="JWT token pair returned."),
            401: OpenApiResponse(description="Invalid credentials."),
            429: OpenApiResponse(description="Rate limit exceeded."),
        },
        examples=[
            OpenApiExample(
                "Login request",
                value={"email": "user@example.com", "password": "securepass123"},
                request_only=True,
            ),
            OpenApiExample(
                "Login response",
                value={"refresh": "eyJ...", "access": "eyJ..."},
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        email = request.data.get("email", "unknown")
        logger.info("Login attempt for email: %s", email)

        try:
            response = super().post(request, *args, **kwargs)
            logger.info("Login is successful for email: %s", email)
            return response
        except (InvalidToken, TokenError) as e:
            logger.warning("Login failed for email: %s - %s", email, str(e))
            raise
        except Exception:
            logger.exception("Login failed for email: %s - unexpected error", email)
            raise


class CustomTokenRefreshView(TokenRefreshView):
    @extend_schema(
        tags=["Auth"],
        summary="Refresh access token",
        description=(
            "Exchange a valid refresh token for a new access token. "
            "No authentication required."
        ),
        responses={
            200: OpenApiResponse(description="New access token returned."),
            401: OpenApiResponse(description="Invalid or expired refresh token."),
        },
        examples=[
            OpenApiExample(
                "Refresh request",
                value={"refresh": "eyJ..."},
                request_only=True,
            ),
            OpenApiExample(
                "Refresh response",
                value={"access": "eyJ..."},
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        logger.info("Token refresh attempt")

        try:
            response = super().post(request, *args, **kwargs)
            logger.info("Token refresh is successful")
            return response
        except (InvalidToken, TokenError) as e:
            logger.warning("Token refresh failed: %s", str(e))
            raise
        except Exception:
            logger.exception("Token refresh failed - unexpected error")
            raise


class LanguageViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Auth"],
        summary="Set preferred language",
        description=(
            "Update the authenticated user's preferred language. "
            "Supported languages: en (English), ru (Russian), kk (Kazakh). "
            "This language will be used for all future API responses and emails."
        ),
        request=LanguageSerializer,
        responses={
            200: OpenApiResponse(description="Language updated successfully."),
            400: OpenApiResponse(description="Invalid language code."),
            401: OpenApiResponse(description="Authentication required."),
        },
        examples=[
            OpenApiExample(
                "Set language request",
                value={"language": "ru"},
                request_only=True,
            ),
            OpenApiExample(
                "Set language response",
                value={"language": "ru"},
                response_only=True,
            ),
        ],
    )
    def partial_update(self, request: Request, **kwargs) -> Response:

        serializer = LanguageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        request.user.language = serializer.validated_data["language"]
        request.user.save(update_fields=["language"])

        logger.info(
            "Language updated to %s for user %s",
            request.user.language,
            request.user.email,
        )
        return Response({"language": request.user.language})


class TimezoneViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Auth"],
        summary="Set preferred timezone",
        description=(
            "Update the authenticated user's preferred timezone. "
            "Accepts any valid IANA timezone string (e.g. 'Asia/Almaty', 'Europe/London'). "
            "This timezone will be used for all future API responses."
        ),
        request=TimezoneSerializer,
        responses={
            200: OpenApiResponse(description="Timezone updated successfully."),
            400: OpenApiResponse(description="Invalid timezone."),
            401: OpenApiResponse(description="Authentication required."),
        },
        examples=[
            OpenApiExample(
                "Set timezone request",
                value={"timezone": "Asia/Almaty"},
                request_only=True,
            ),
            OpenApiExample(
                "Set timezone response",
                value={"timezone": "Asia/Almaty"},
                response_only=True,
            ),
        ],
    )
    def partial_update(self, request: Request, **kwargs) -> Response:
        serializer = TimezoneSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        request.user.timezone = serializer.validated_data["timezone"]
        request.user.save(update_fields=["timezone"])

        logger.info(
            "Timezone updated to %s for user %s",
            request.user.timezone,
            request.user.email,
        )
        return Response({"timezone": request.user.timezone})
