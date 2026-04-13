import logging
import random
from datetime import timedelta

from django.utils import timezone
from django.core.management.base import BaseCommand

from apps.blog.models import Category, Comment, Post, Tag
from apps.users.models import User

logger = logging.getLogger(__name__)


SUPERUSER_EMAIL = "admin@blogapi.com"
SUPERUSER_PASSWORD = "admin123456"
SUPERUSER_FIRST_NAME = "Admin"
SUPERUSER_LAST_NAME = "User"

TEST_USERS = [
    ("john@example.com", "John", "Smith", "en", "UTC"),
    ("ivan@example.com", "Ivan", "Petrov", "ru", "Europe/Moscow"),
    ("alikhan@example.com", "Alikhan", "Serik", "kk", "Asia/Almaty"),
    ("maria@example.com", "Maria", "Garcia", "en", "America/New_York"),
    ("dmitry@example.com", "Dmitry", "Ivanov", "ru", "Europe/Moscow"),
]

TEST_PASSWORD = "testpass123"

CATEGORIES = [
    ("Technology", "technology", "Технологии", "Технология"),
    ("Science", "science", "Наука", "Ғылым"),
    ("Travel", "travel", "Путешествия", "Саяхат"),
    ("Food", "food", "Еда", "Тамақ"),
    ("Sports", "sports", "Спорт", "Спорт"),
]

TAGS = [
    ("Python", "python"),
    ("Django", "django"),
    ("JavaScript", "javascript"),
    ("AI", "ai"),
    ("Machine Learning", "machine-learning"),
    ("Web Development", "web-development"),
    ("DevOps", "devops"),
    ("Database", "database"),
]

COMMENT_BODIES = [
    "Great article! Very informative.",
    "Thanks for sharing this.",
    "I learned a lot from this post.",
    "Could you write more about this topic?",
    "Excellent explanation!",
    "This helped me with my project.",
    "Very well written.",
    "I disagree with some points, but overall good.",
    "Looking forward to more posts like this.",
    "Bookmarked for future reference.",
]


class Command(BaseCommand):
    help = "Seed the database with test data"

    def handle(self, *args, **options) -> None:
        if Post.objects.exists():
            self.stdout.write(self.style.WARNING("Test data already exists, skipping."))
            return

        users = self._create_users()
        categories = self._create_categories()
        tags = self._create_tags()
        self._create_posts(users, categories, tags)
        self._create_comments(users)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded: {User.objects.count()} users, "
                f"{Category.objects.count()} categories, "
                f"{Tag.objects.count()} tags, "
                f"{Post.objects.count()} posts, "
                f"{Comment.objects.count()} comments"
            )
        )

    def _create_users(self) -> list:
        # Superuser
        if not User.objects.filter(email=SUPERUSER_EMAIL).exists():
            User.objects.create_superuser(
                email=SUPERUSER_EMAIL,
                password=SUPERUSER_PASSWORD,
                first_name=SUPERUSER_FIRST_NAME,
                last_name=SUPERUSER_LAST_NAME,
            )
            self.stdout.write(f"  Created superuser: {SUPERUSER_EMAIL}")

        # Test users
        users = []
        for email, first, last, lang, tz in TEST_USERS:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password=TEST_PASSWORD,
                    first_name=first,
                    last_name=last,
                    language=lang,
                    timezone=tz,
                )
                users.append(user)
            else:
                users.append(User.objects.get(email=email))

        self.stdout.write(f"  Users ready: {len(users)} test users")
        return users

    def _create_categories(self) -> list:
        categories = []
        for name_en, slug, name_ru, name_kk in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name_en},
            )
            if created:
                cat.name_ru = name_ru
                cat.name_kk = name_kk
                cat.save()
            categories.append(cat)

        self.stdout.write(f"  Categories ready: {len(categories)}")
        return categories

    def _create_tags(self) -> list:
        tags = []
        for name, slug in TAGS:
            tag, _ = Tag.objects.get_or_create(name=name, slug=slug)
            tags.append(tag)

        self.stdout.write(f"  Tags ready: {len(tags)}")
        return tags

    def _create_posts(self, users: list, categories: list, tags: list) -> None:
        now = timezone.now()

        posts_data = [
            {
                "author": users[0],
                "title": "Getting Started with Django",
                "slug": "getting-started-with-django",
                "body": "Django is a powerful web framework for Python. In this post, we explore the basics of setting up a Django project, creating models, and building views.",
                "category": categories[0],
                "tags": [tags[0], tags[1], tags[5]],
                "status": "published",
            },
            {
                "author": users[0],
                "title": "Python Best Practices",
                "slug": "python-best-practices",
                "body": "Writing clean Python code is essential for maintainable projects. Learn about PEP 8, type hints, virtual environments, and testing.",
                "category": categories[0],
                "tags": [tags[0]],
                "status": "published",
            },
            {
                "author": users[1],
                "title": "Introduction to Machine Learning",
                "slug": "intro-to-ml",
                "body": "Machine learning is transforming industries. This post covers the fundamental concepts of supervised and unsupervised learning.",
                "category": categories[1],
                "tags": [tags[3], tags[4]],
                "status": "published",
            },
            {
                "author": users[2],
                "title": "Exploring Almaty",
                "slug": "exploring-almaty",
                "body": "Almaty is a beautiful city surrounded by mountains. From Big Almaty Lake to Kok Tobe, there is so much to explore.",
                "category": categories[2],
                "tags": [],
                "status": "published",
            },
            {
                "author": users[3],
                "title": "JavaScript Frameworks in 2025",
                "slug": "js-frameworks-2025",
                "body": "The JavaScript ecosystem continues to evolve rapidly. React, Vue, and Svelte all have their strengths.",
                "category": categories[0],
                "tags": [tags[2], tags[5]],
                "status": "published",
            },
            {
                "author": users[4],
                "title": "DevOps Fundamentals",
                "slug": "devops-fundamentals",
                "body": "Understanding CI/CD pipelines, containerization, and infrastructure as code is essential for modern development.",
                "category": categories[0],
                "tags": [tags[6]],
                "status": "published",
            },
            {
                "author": users[0],
                "title": "Database Design Patterns",
                "slug": "database-design-patterns",
                "body": "Good database design is the foundation of any application. Learn about normalization, indexing, and query optimization.",
                "category": categories[0],
                "tags": [tags[7]],
                "status": "published",
            },
            {
                "author": users[1],
                "title": "Cooking Beshbarmak",
                "slug": "cooking-beshbarmak",
                "body": "Beshbarmak is a traditional Central Asian dish. Here is how to make it authentically at home.",
                "category": categories[3],
                "tags": [],
                "status": "published",
            },
            {
                "author": users[2],
                "title": "Football in Kazakhstan",
                "slug": "football-kazakhstan",
                "body": "Football is growing in popularity in Kazakhstan. The national team has made progress in recent years.",
                "category": categories[4],
                "tags": [],
                "status": "published",
            },
            {
                "author": users[4],
                "title": "Advanced Django REST Framework",
                "slug": "advanced-drf",
                "body": "Take your DRF skills to the next level with custom permissions, throttling, and caching.",
                "category": categories[0],
                "tags": [tags[0], tags[1], tags[5]],
                "status": "published",
            },
            {
                "author": users[0],
                "title": "Draft Post About Testing",
                "slug": "draft-testing",
                "body": "This is a draft post about testing in Django. It should not appear in the public list.",
                "category": categories[0],
                "tags": [tags[0], tags[1]],
                "status": "draft",
            },
            {
                "author": users[3],
                "title": "Another Draft",
                "slug": "another-draft",
                "body": "This is another draft post that should be hidden from the public API.",
                "category": categories[1],
                "tags": [],
                "status": "draft",
            },
            {
                "author": users[0],
                "title": "Upcoming Post About AI",
                "slug": "upcoming-ai-post",
                "body": "This post is scheduled for future publication.",
                "category": categories[1],
                "tags": [tags[3], tags[4]],
                "status": "scheduled",
                "publish_at": now + timedelta(hours=1),
            },
        ]

        for data in posts_data:
            post_tags = data.pop("tags")
            post = Post.objects.create(**data)
            if post_tags:
                post.tags.set(post_tags)

        self.stdout.write(f"  Posts created: {len(posts_data)}")

    def _create_comments(self, users: list) -> None:
        published_posts = Post.objects.filter(status="published")
        count = 0

        for post in published_posts:
            num_comments = random.randint(1, 4)
            for _ in range(num_comments):
                Comment.objects.create(
                    post=post,
                    author=random.choice(users),
                    body=random.choice(COMMENT_BODIES),
                )
                count += 1

        self.stdout.write(f"  Comments created: {count}")
