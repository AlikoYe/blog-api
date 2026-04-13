import os
from pathlib import Path
from celery import Celery
from celery.schedules import crontab
from decouple import Config, RepositoryEnv

SETTINGS_DIR = Path(__file__).resolve().parent
env_path = SETTINGS_DIR / ".env"
env_config = Config(RepositoryEnv(str(env_path)))
env_id = env_config("BLOG_ENV_ID", default="local")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{env_id}")
app = Celery("blog")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "publish-schedule-posts": {
        "task": "apps.blog.tasks.publish_scheduled_posts",
        "schedule": 60.0,
    },
    "clear-expired-notifications": {
        "task": "apps.notiifications.tasks.clear_expired_notifications",
        "schedule": crontab(hour=3, minute=0),
    },
    "generate-daily-stats": {
        "task": "apps.blog.tasks.generate_daily_stats",
        "schedule": crontab(hour=0, minute=0),
    },
}
