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

python "$PROJECT_DIR/manage.py" seed

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