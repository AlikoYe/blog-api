#!/usr/bin/env bash

# ============================================================================
# Blog API — Project Setup & Start Script
# Takes the project from zero to a fully running server with one command.
# ============================================================================

set -e  # Stop immediately if any command fails

# ── Colors for output ──────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Constants ──────────────────────────────────────────────────────────────

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/settings/.env"
VENV_DIR="$PROJECT_DIR/.venv"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements/dev.txt"
SUPERUSER_EMAIL="${BLOG_SUPERUSER_EMAIL:-admin@blogapi.com}"
SUPERUSER_PASSWORD="${BLOG_SUPERUSER_PASSWORD:-$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')}"
SUPERUSER_FIRST_NAME="Admin"
SUPERUSER_LAST_NAME="User"

# Required environment variables
REQUIRED_VARS=(
    "BLOG_ENV_ID"
    "BLOG_SECRET_KEY"
    "BLOG_DEBUG"
    "BLOG_REDIS_URL"
)

# ── Helper functions ───────────────────────────────────────────────────────

print_step() {
    echo -e "\n${BLUE}[$1/$TOTAL_STEPS]${NC} $2"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗ FAILED:${NC} $1"
    exit 1
}

TOTAL_STEPS=8

# ============================================================================
# Step 1: Validate environment variables
# ============================================================================

print_step 1 "Checking environment variables..."

if [ ! -f "$ENV_FILE" ]; then
    print_error "settings/.env file not found. Copy settings/.env.example to settings/.env and fill in values."
fi

# Read .env file and check required variables
while IFS= read -r line || [ -n "$line" ]; do
    # Skip comments and empty lines
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    # Export the variable
    export "$line"
done < "$ENV_FILE"

for var in "${REQUIRED_VARS[@]}"; do
    value="${!var}"
    if [ -z "$value" ]; then
        print_error "Required environment variable $var is missing or empty in settings/.env"
    fi
done

print_success "All required environment variables are set."

# ============================================================================
# Step 2: Create virtual environment and install dependencies
# ============================================================================

print_step 2 "Setting up virtual environment and installing dependencies..."

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created at $VENV_DIR"
else
    print_warning "Virtual environment already exists, skipping creation."
fi

source "$VENV_DIR/bin/activate"

pip install --quiet --upgrade pip
pip install --quiet -r "$REQUIREMENTS_FILE"

print_success "Dependencies installed."

# ============================================================================
# Step 3: Run migrations
# ============================================================================

print_step 3 "Running database migrations..."

python "$PROJECT_DIR/manage.py" migrate --no-input

print_success "Migrations complete."

# ============================================================================
# Step 4: Collect static files
# ============================================================================

print_step 4 "Collecting static files..."

python "$PROJECT_DIR/manage.py" collectstatic --no-input --clear 2>/dev/null || true

print_success "Static files collected."

# ============================================================================
# Step 5: Compile translation files
# ============================================================================

print_step 5 "Compiling translation files..."

python "$PROJECT_DIR/manage.py" compilemessages 2>/dev/null || print_warning "compilemessages skipped (gettext may not be installed)."

print_success "Translations compiled."

# ============================================================================
# Step 6: Create superuser
# ============================================================================

print_step 6 "Creating superuser..."

python "$PROJECT_DIR/manage.py" shell -c "
from apps.users.models import User
if not User.objects.filter(email='$SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$SUPERUSER_EMAIL',
        password='$SUPERUSER_PASSWORD',
        first_name='$SUPERUSER_FIRST_NAME',
        last_name='$SUPERUSER_LAST_NAME',
    )
    print('Superuser created.')
else:
    print('Superuser already exists, skipping.')
"

print_success "Superuser ready."

# ============================================================================
# Step 7: Seed test data
# ============================================================================

print_step 7 "Seeding test data..."

python "$PROJECT_DIR/manage.py" shell -c "
from apps.users.models import User
from apps.blog.models import Category, Tag, Post, Comment

# Check if data already exists
if Post.objects.exists():
    print('Test data already exists, skipping.')
else:
    # Create test users
    users = []
    test_users = [
        ('john@example.com', 'John', 'Smith', 'en', 'UTC'),
        ('ivan@example.com', 'Ivan', 'Petrov', 'ru', 'Europe/Moscow'),
        ('alikhan@example.com', 'Alikhan', 'Serik', 'kk', 'Asia/Almaty'),
        ('maria@example.com', 'Maria', 'Garcia', 'en', 'America/New_York'),
        ('dmitry@example.com', 'Dmitry', 'Ivanov', 'ru', 'Europe/Moscow'),
    ]
    for email, first, last, lang, tz in test_users:
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                email=email,
                password='testpass123',
                first_name=first,
                last_name=last,
                language=lang,
                timezone=tz,
            )
            users.append(user)
        else:
            users.append(User.objects.get(email=email))

    # Create categories
    categories_data = [
        ('Technology', 'technology'),
        ('Science', 'science'),
        ('Travel', 'travel'),
        ('Food', 'food'),
        ('Sports', 'sports'),
    ]
    categories = []
    for name, slug in categories_data:
        cat, _ = Category.objects.get_or_create(name=name, slug=slug)
        categories.append(cat)

    # Set Russian and Kazakh names for categories
    translations = {
        'technology': ('Технологии', 'Технология'),
        'science': ('Наука', 'Ғылым'),
        'travel': ('Путешествия', 'Саяхат'),
        'food': ('Еда', 'Тамақ'),
        'sports': ('Спорт', 'Спорт'),
    }
    for cat in categories:
        if cat.slug in translations:
            ru_name, kk_name = translations[cat.slug]
            cat.name_ru = ru_name
            cat.name_kk = kk_name
            cat.save()

    # Create tags
    tags_data = [
        ('Python', 'python'),
        ('Django', 'django'),
        ('JavaScript', 'javascript'),
        ('AI', 'ai'),
        ('Machine Learning', 'machine-learning'),
        ('Web Development', 'web-development'),
        ('DevOps', 'devops'),
        ('Database', 'database'),
    ]
    tags = []
    for name, slug in tags_data:
        tag, _ = Tag.objects.get_or_create(name=name, slug=slug)
        tags.append(tag)

    # Create posts
    posts_data = [
        (users[0], 'Getting Started with Django', 'getting-started-with-django',
         'Django is a powerful web framework for Python. In this post, we explore the basics of setting up a Django project, creating models, and building views.',
         categories[0], [tags[0], tags[1], tags[5]], 'published'),
        (users[0], 'Python Best Practices', 'python-best-practices',
         'Writing clean Python code is essential for maintainable projects. Learn about PEP 8, type hints, virtual environments, and testing.',
         categories[0], [tags[0]], 'published'),
        (users[1], 'Introduction to Machine Learning', 'intro-to-ml',
         'Machine learning is transforming industries. This post covers the fundamental concepts of supervised and unsupervised learning.',
         categories[1], [tags[3], tags[4]], 'published'),
        (users[2], 'Exploring Almaty', 'exploring-almaty',
         'Almaty is a beautiful city surrounded by mountains. From Big Almaty Lake to Kok Tobe, there is so much to explore.',
         categories[2], [], 'published'),
        (users[3], 'JavaScript Frameworks in 2025', 'js-frameworks-2025',
         'The JavaScript ecosystem continues to evolve rapidly. React, Vue, and Svelte all have their strengths.',
         categories[0], [tags[2], tags[5]], 'published'),
        (users[4], 'DevOps Fundamentals', 'devops-fundamentals',
         'Understanding CI/CD pipelines, containerization, and infrastructure as code is essential for modern development.',
         categories[0], [tags[6]], 'published'),
        (users[0], 'Database Design Patterns', 'database-design-patterns',
         'Good database design is the foundation of any application. Learn about normalization, indexing, and query optimization.',
         categories[0], [tags[7]], 'published'),
        (users[1], 'Cooking Beshbarmak', 'cooking-beshbarmak',
         'Beshbarmak is a traditional Central Asian dish. Here is how to make it authentically at home.',
         categories[3], [], 'published'),
        (users[2], 'Football in Kazakhstan', 'football-kazakhstan',
         'Football is growing in popularity in Kazakhstan. The national team has made progress in recent years.',
         categories[4], [], 'published'),
        (users[0], 'Draft Post About Testing', 'draft-testing',
         'This is a draft post about testing in Django. It should not appear in the public list.',
         categories[0], [tags[0], tags[1]], 'draft'),
        (users[3], 'Another Draft', 'another-draft',
         'This is another draft post that should be hidden from the public API.',
         categories[1], [], 'draft'),
        (users[4], 'Advanced Django REST Framework', 'advanced-drf',
         'Take your DRF skills to the next level with custom permissions, throttling, and caching.',
         categories[0], [tags[0], tags[1], tags[5]], 'published'),
    ]

    for author, title, slug, body, category, post_tags, post_status in posts_data:
        post = Post.objects.create(
            author=author,
            title=title,
            slug=slug,
            body=body,
            category=category,
            status=post_status,
        )
        if post_tags:
            post.tags.set(post_tags)

    # Create comments
    all_published = Post.objects.filter(status='published')
    comments_data = [
        'Great article! Very informative.',
        'Thanks for sharing this.',
        'I learned a lot from this post.',
        'Could you write more about this topic?',
        'Excellent explanation!',
        'This helped me with my project.',
        'Very well written.',
        'I disagree with some points, but overall good.',
        'Looking forward to more posts like this.',
        'Bookmarked for future reference.',
    ]

    import random
    for post in all_published:
        num_comments = random.randint(1, 4)
        for i in range(num_comments):
            Comment.objects.create(
                post=post,
                author=random.choice(users),
                body=random.choice(comments_data),
            )

    print(f'Seeded: {User.objects.count()} users, {Category.objects.count()} categories, '
          f'{Tag.objects.count()} tags, {Post.objects.count()} posts, {Comment.objects.count()} comments')
"

print_success "Test data seeded."

# ============================================================================
# Step 8: Start development server
# ============================================================================

print_step 8 "Starting development server..."

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Blog API — Ready!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  API:          ${BLUE}http://127.0.0.1:8000/api/${NC}"
echo -e "  Swagger UI:   ${BLUE}http://127.0.0.1:8000/api/docs/${NC}"
echo -e "  ReDoc:        ${BLUE}http://127.0.0.1:8000/api/redoc/${NC}"
echo -e "  Admin:        ${BLUE}http://127.0.0.1:8000/admin/${NC}"
echo ""
echo -e "  Superuser:    ${YELLOW}$SUPERUSER_EMAIL${NC}"
echo -e "  Password:     ${YELLOW}$SUPERUSER_PASSWORD${NC}"
echo ""
echo -e "  Test users:   ${YELLOW}john@example.com / testpass123${NC}"
echo -e "                ${YELLOW}ivan@example.com / testpass123${NC} (Russian)"
echo -e "                ${YELLOW}alikhan@example.com / testpass123${NC} (Kazakh)"
echo ""

python "$PROJECT_DIR/manage.py" runserver