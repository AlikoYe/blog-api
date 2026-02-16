"""
WSGI config for settings project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application
from decouple import Config , RepositoryEnv

SETTINGS_DIR = Path(__file__).resolve().parent
env_path = SETTINGS_DIR / '.env'
env_config = Config(RepositoryEnv(str(env_path)))

env_id = env_config('BLOG_ENV_ID', default='local')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'settings.env.{env_id}')

application = get_wsgi_application()
