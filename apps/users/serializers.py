import logging
import zoneinfo
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
from apps.users.models import LANGUAGE_CHOICES, TIMEZONE_MAX_LENGTH
from apps.users.models import User
from apps.users.tasks import send_welcome_email_task

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 8
FIRST_NAME_MAX_LENGTH = 50
LAST_NAME_MAX_LENGTH = 50


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "avatar",
            "language",
            "timezone",
        )
        read_only_fields = ("id", "email", "date_joined")


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=FIRST_NAME_MAX_LENGTH)
    last_name = serializers.CharField(max_length=LAST_NAME_MAX_LENGTH)
    password = serializers.CharField(write_only=True, min_length=MIN_PASSWORD_LENGTH)
    password_confirm = serializers.CharField(write_only=True)
    language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES, default="en", required=False
    )

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value.lower()

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")},
            )
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password_confirm")
        language = validated_data.pop("language", "en")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            language=language,
        )
        logger.info("User registered via serializer: %s", user.email)
        send_welcome_email_task.delay(user.id)
        return user

    def get_tokens(self, user: User) -> dict:
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def to_representation(self, instance: User) -> dict:
        user_data = UserSerializer(instance).data
        tokens = self.get_tokens(instance)
        return {
            "user": user_data,
            "tokens": tokens,
        }


class LanguageSerializer(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        error_messages={
            "invalid_choice": _("Invalid language. Supported: en, ru, kk."),
        },
    )


class TimezoneSerializer(serializers.Serializer):
    timezone = serializers.CharField(max_length=TIMEZONE_MAX_LENGTH)

    def validate_timezone(self, value: str) -> str:
        try:
            zoneinfo.ZoneInfo(value)
        except (KeyError, zoneinfo.ZoneInfoNotFoundError):
            raise serializers.ValidationError(
                _("Invalid timezone. Use IANA format."),
            )
        return value
