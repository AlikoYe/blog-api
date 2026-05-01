# Blog API

Blog API is a Django REST Framework project built through HW1, HW2, HW3, and HW4.

The project includes:

- Custom email-based user authentication with JWT
- Blog posts, categories, tags, and comments
- Redis caching
- Multilanguage support: English, Russian, Kazakh
- API documentation with Swagger UI and ReDoc
- Async external API calls
- Real-time communication with WebSockets and Server-Sent Events
- Notification polling
- Celery background tasks and scheduled tasks
- Docker Compose setup
- Nginx reverse proxy in front of Django

---

## Technology Stack

- Python 3.12
- Django
- Django REST Framework
- Simple JWT
- Redis
- Django Channels
- Celery
- Celery Beat
- Flower
- Daphne
- Nginx
- Docker / Docker Compose
- SQLite for local Docker development
- drf-spectacular for OpenAPI documentation

---

## Project Structure

```text
blog-api/
├── apps/
│   ├── users/
│   ├── blog/
│   ├── core/
│   └── notifications/
├── settings/
│   ├── conf.py
│   ├── base.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── celery.py
│   ├── .env.example
│   └── env/
│       ├── local.py
│       └── prod.py
├── nginx/
│   └── default.conf
├── scripts/
│   ├── start.sh
│   └── entrypoint.sh
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── locale/
├── templates/
├── logs/
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── README.md