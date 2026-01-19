#!/bin/bash
# Production entrypoint script for STM Intelligence Brief System backend
# This script handles database migrations and graceful startup

set -e  # Exit on error

echo "[$(date)] Starting STM Intelligence Brief System backend..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Extract database connection parameters from DATABASE_URL if provided
if [ -n "$DATABASE_URL" ]; then
    log_info "Extracting database connection from DATABASE_URL..."
    log_info "DATABASE_URL format detected"
    # Parse DATABASE_URL (format: postgresql://user:password@host:port/dbname)
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:\/]*\).*/\1/p')
    DB_USER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    log_info "Extracted DB_HOST: ${DB_HOST}"
    log_info "Extracted DB_USER: ${DB_USER}"
    export DB_HOST DB_USER
fi

# Wait for database to be ready
log_info "Waiting for database to be ready..."
MAX_RETRIES=60
RETRY_COUNT=0

# Temporarily disable 'exit on error' for database connection retries
set +e

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    pg_isready -h "${DB_HOST:-postgres}" -U "${DB_USER:-postgres}" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "Database is ready!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        log_error "Database did not become ready in time after $MAX_RETRIES attempts."
        log_error "DB_HOST: ${DB_HOST:-postgres}"
        log_error "DB_USER: ${DB_USER:-postgres}"
        exit 1
    fi
    log_warn "Database not ready yet. Retrying in 3 seconds... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done

# Re-enable 'exit on error'
set -e

# Enable pgvector extension if not already enabled
log_info "Enabling pgvector extension..."
python - <<PGVECTOR_EOF
from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Enable pgvector extension (idempotent - won't fail if already exists)
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("[INFO] pgvector extension enabled")
except Exception as e:
    print(f"[WARN] Could not enable pgvector extension: {e}")
    print("[INFO] Continuing anyway - extension may already be enabled")
PGVECTOR_EOF

log_info "pgvector extension check completed"

# Run database migrations
log_info "Running database migrations..."
if alembic upgrade head; then
    log_info "Migrations completed successfully"
else
    log_error "Migration failed! Check alembic logs."
    exit 1
fi

# Verify database tables exist
log_info "Verifying database schema..."
python - <<EOF
from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
        table_count = result.scalar()
        if table_count < 3:
            raise Exception(f"Expected at least 3 tables, found {table_count}")
        print(f"[INFO] Found {table_count} tables in database")
except Exception as e:
    print(f"[ERROR] Database verification failed: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    log_error "Database verification failed"
    exit 1
fi

log_info "Database schema verified"

# Check required environment variables
log_info "Checking environment configuration..."

REQUIRED_VARS=(
    "DATABASE_URL"
    "CURATOR_TOKEN"
    "ALLOWED_ORIGINS"
)

MISSING_VARS=()
for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        MISSING_VARS+=("$VAR")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    log_error "Missing required environment variables:"
    for VAR in "${MISSING_VARS[@]}"; do
        echo "  - $VAR"
    done
    exit 1
fi

log_info "Environment configuration OK"

# Warn if using default token
if [ "$CURATOR_TOKEN" = "dev-token-change-in-production" ]; then
    log_warn "=================================================="
    log_warn "WARNING: Using default CURATOR_TOKEN!"
    log_warn "This is INSECURE for production."
    log_warn "Generate a secure token with:"
    log_warn "  python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    log_warn "=================================================="
fi

# Set default log level if not specified
export LOG_LEVEL=${LOG_LEVEL:-INFO}
log_info "Log level set to: $LOG_LEVEL"

# Start the application
log_info "Starting FastAPI application..."
log_info "Listening on ${HOST:-0.0.0.0}:${PORT:-8000}"

exec uvicorn app.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --log-level "${LOG_LEVEL,,}" \
    --no-access-log
