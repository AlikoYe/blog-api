import os
from settings.base import *  # noqa: F401,F403
from settings.base import BASE_DIR

DEBUG = True
DATA_DIR = os.environ.get("BLOG_DATA_DIR", str(BASE_DIR))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(DATA_DIR, "db.sqlite3"),
    }
}
