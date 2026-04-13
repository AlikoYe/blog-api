import os
from pathlib import Path
from django.core.asgi import get_asgi_application
from decouple import Config, RepositoryEnv
from channels.routing import ProtocolTypeRouter, URLRouter

SETTINGS_DIR = Path(__file__).resolve().parent
env_path = SETTINGS_DIR / ".env"
env_config = Config(RepositoryEnv(str(env_path)))

env_id = env_config("BLOG_ENV_ID", default="local")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{env_id}")

django_asgi_app = get_asgi_application()

from apps.notifications.routing import websocket_urlpatterns
from apps.notifications.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
