from pathlib import Path
from decouple import config, RepositoryEnv, Config

BASE_DIR = Path(__file__).resolve().parent.parent

env_path = Path(__file__).resolve().parent / '.env'
env_config = Config(RepositoryEnv(str(env_path)))

BLOG_ENV_ID = config('BLOG_ENV_ID', default='local')
BLOG_SECRET_KEY = config('BLOG_SECRET_KEY')
BLOG_DEBUG = config('BLOG_DEBUG', default=False, cast=bool)

BLOG_REDIS_URL = config('BLGO_REDIS_URL', default='redis://localhost:6379/0')

BLOG_ALLOWED_HOSTS = config('BLOG_ALLOWED_HOSTS', default='localhost,127.0.0.1', cast= lambda v: [s.strip() for s in v.split(',')])