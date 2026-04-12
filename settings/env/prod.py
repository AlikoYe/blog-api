from settings.base import *  # noqa: F401,F403
from settings.conf import BLOG_ALLOWED_HOSTS
from decouple import config

DEBUG = False
ALLOWED_HOSTS = BLOG_ALLOWED_HOSTS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DATABASE_DB_NAME", default="blog_db"),
        "USER": config("DATABASE_DB_USER", default="postgres"),
        "PASSWORD": config("DATABASE_DB_PASSWORD", default=""),
        "HOST": config("DATABASE_DB_HOST", default="localhost"),
        "PORT": config("DATABASE_DB_PORT", default="5432"),
    }
}
