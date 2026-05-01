import os
from settings.base import *  # noqa: F401,F403
from settings.base import BASE_DIR
from settings.conf import BLOG_DEBUG, BLOG_ALLOWED_HOSTS

DEBUG = BLOG_DEBUG
ALLOWED_HOSTS = BLOG_ALLOWED_HOSTS
DATA_DIR = os.environ.get("BLOG_DATA_DIR", str(BASE_DIR))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(DATA_DIR, "db.sqlite3"),
    }
}
