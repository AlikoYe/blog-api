#!/usr/bin/env bash

# ============================================================================
# Blog API — Docker Entrypoint
# Runs setup steps before starting the main process (CMD).
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Blog API — Container starting...${NC}"

# ============================================================================
# Step 1: Wait for Redis
# ============================================================================

echo -e "${YELLOW}Waiting for Redis...${NC}"

REDIS_HOST="${BLOG_REDIS_URL:-redis://redis:6379/0}"
# Extract host and port from URL like redis://redis:6379/0
REDIS_ADDR=$(echo "$REDIS_HOST" | sed -E 's|redis://([^/]+)/.*|\1|')
REDIS_H=$(echo "$REDIS_ADDR" | cut -d: -f1)
REDIS_P=$(echo "$REDIS_ADDR" | cut -d: -f2)

MAX_RETRIES=30
RETRY_COUNT=0

while ! python -c "
import socket
try:
    s = socket.create_connection(('$REDIS_H', $REDIS_P), timeout=1)
    s.close()
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
        echo -e "${RED}Redis not available after $MAX_RETRIES attempts. Exiting.${NC}"
        exit 1
    fi
    echo "  Redis not ready, retrying ($RETRY_COUNT/$MAX_RETRIES)..."
    sleep 1
done

echo -e "${GREEN}✓ Redis is available${NC}"

# ============================================================================
# Step 2: Run migrations
# ============================================================================

echo -e "${YELLOW}Running migrations...${NC}"
python manage.py migrate --no-input
echo -e "${GREEN}✓ Migrations complete${NC}"

# ============================================================================
# Step 3: Collect static files
# ============================================================================

echo -e "${YELLOW}Collecting static files...${NC}"
python manage.py collectstatic --no-input --clear 2>/dev/null || true
echo -e "${GREEN}✓ Static files collected${NC}"

# ============================================================================
# Step 4: Compile translation messages
# ============================================================================

echo -e "${YELLOW}Compiling translations...${NC}"
python manage.py compilemessages 2>/dev/null || echo -e "${YELLOW}⚠ compilemessages skipped${NC}"
echo -e "${GREEN}✓ Translations compiled${NC}"

# ============================================================================
# Step 5: Seed database (if BLOG_SEED_DB=true)
# ============================================================================

if [ "${BLOG_SEED_DB}" = "true" ]; then
    echo -e "${YELLOW}Seeding database...${NC}"
    python manage.py seed
    echo -e "${GREEN}✓ Database seeded${NC}"
fi

# ============================================================================
# Step 6: Execute CMD
# ============================================================================

echo -e "${GREEN}Starting: $@${NC}"
exec "$@"