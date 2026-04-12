import logging
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

AVATAR_UPLOAD_PATH = "avatars/"
FIRST_NAME_MAX_LENGTH = 50
LAST_NAME_MAX_LENGTH = 50

LANGUAGE_CHOICES = [
    ("en", _("English")),
    ("ru", _("Russian")),
    ("kk", _("Kazakh")),
]
DEFAULT_LANGUAGE = "en"
DEFAULT_TIMEZONE = "UTC"
LANGUAGE_MAX_LENGTH = 10
TIMEZONE_MAX_LENGTH = 50


class CustomUserManager(BaseUserManager):
    def create_user(self, email: str, password: str = None, **extra_fields) -> "User":
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        logger.info("User created: %s", email)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        logger.info("Superuser created: %s", email)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(
        upload_to=AVATAR_UPLOAD_PATH,
        null=True,
        blank=True,
        verbose_name=_("avatar"),
    )
    language = models.CharField(
        max_length=LANGUAGE_MAX_LENGTH,
        choices=LANGUAGE_CHOICES,
        default=DEFAULT_LANGUAGE,
        verbose_name=_("preferred language"),
    )
    timezone = models.CharField(
        max_length=TIMEZONE_MAX_LENGTH,
        default=DEFAULT_TIMEZONE,
        verbose_name=_("timezone"),
        help_text=_("IANA timezone string, e.g. 'Asia/Almaty'"),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = CustomUserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email
