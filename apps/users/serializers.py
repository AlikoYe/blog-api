import logging

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 8

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'date_joined', 'avatar')
        read_only_fields = ('id', 'email', 'date_joined')

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    password = serializers.CharField(write_only=True, min_length=MIN_PASSWORD_LENGTH)
    password_confirm = serializers.CharField(write_only=True)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate(self, attrs: dict) -> dict:
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        logger.info('User registered via serializer: %s', user.email)
        return user

    def get_tokens(self, user: User) -> dict:
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def to_representation(self, instance: User) -> dict:
        user_data = UserSerializer(instance).data
        tokens = self.get_tokens(instance)
        return {
            'user': user_data,
            'tokens': tokens,
        }