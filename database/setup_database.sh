#!/bin/bash

################################################################################
# Database Setup Script for Emotion Analysis Pipeline
# Run this script to set up PostgreSQL database with all tables and user
################################################################################

set -e  # Exit on error

# Configuration
DB_USER="${DB_USER:-emotion_app}"
DB_PASSWORD="${DB_PASSWORD:-emotion_password_123}"
DB_NAME="${DB_NAME:-emotion_db}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check PostgreSQL is installed
print_info "Checking PostgreSQL installation..."
if ! command -v psql &> /dev/null; then
    print_error "PostgreSQL is not installed. Please install PostgreSQL first."
    exit 1
fi
print_info "PostgreSQL found: $(psql --version)"

# Check PostgreSQL is running
print_info "Checking if PostgreSQL is running..."
if ! sudo systemctl is-active --quiet postgresql; then
    print_warn "PostgreSQL not running, attempting to start..."
    sudo systemctl start postgresql
    sleep 2
fi
print_info "PostgreSQL is running"

# Create database
print_info "Creating database '$DB_NAME'..."
if psql -U postgres -p 5432 -h localhost -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
    print_warn "Database '$DB_NAME' already exists, skipping creation"
else
    psql -U postgres -p 5432 -h localhost -c "CREATE DATABASE $DB_NAME;"
    print_info "Database '$DB_NAME' created successfully"
fi

# Create database user
print_info "Creating database user '$DB_USER'..."
if psql -U postgres -p 5432 -h localhost -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1; then
    print_warn "User '$DB_USER' already exists, skipping creation"
else
    psql -U postgres -p 5432 -h localhost -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    print_info "User '$DB_USER' created successfully"
fi

# Grant database privileges
print_info "Granting database privileges to '$DB_USER'..."
psql -U postgres -p 5432 -h localhost -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
print_info "Database privileges granted"

# Create tables
print_info "Creating tables in database '$DB_NAME'..."

DB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$DB_DIR/01_create_raw_posts_table.sql" ]; then
    print_error "Schema file not found: $DB_DIR/01_create_raw_posts_table.sql"
    exit 1
fi

print_info "Running 01_create_raw_posts_table.sql..."
psql -U postgres -p 5432 -h localhost -d $DB_NAME -f "$DB_DIR/01_create_raw_posts_table.sql" > /dev/null
print_info "raw_posts table created"

print_info "Running 02_create_cleaned_posts_table.sql..."
psql -U postgres -p 5432 -h localhost -d $DB_NAME -f "$DB_DIR/02_create_cleaned_posts_table.sql" > /dev/null
print_info "cleaned_posts table created"

print_info "Running 03_create_enriched_posts_table.sql..."
psql -U postgres -p 5432 -h localhost -d $DB_NAME -f "$DB_DIR/03_create_enriched_posts_table.sql" > /dev/null
print_info "enriched_posts table created"

# Grant schema privileges
print_info "Granting schema privileges to '$DB_USER'..."
psql -U postgres -p 5432 -h localhost -d $DB_NAME -c "GRANT ALL PRIVILEGES ON SCHEMA public TO $DB_USER;" > /dev/null
psql -U postgres -p 5432 -h localhost -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;" > /dev/null
psql -U postgres -p 5432 -h localhost -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;" > /dev/null
print_info "Schema privileges granted"

# Verify setup
print_info "Verifying setup..."
echo ""
print_info "Tables in database:"
psql -U postgres -p 5432 -h localhost -d $DB_NAME -c "\dt"

echo ""
print_info "Database connection string for .env:"
echo "DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo ""
print_info "Testing connection as '$DB_USER'..."
if psql -U $DB_USER -d $DB_NAME -p 5432 -h localhost -c "SELECT 1;" > /dev/null 2>&1; then
    print_info "Connection successful!"
else
    print_error "Connection failed. Check your credentials."
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
print_info "Database setup completed successfully!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "1. Create .env file in model directory with:"
echo "   DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo ""
echo "2. Install model dependencies:"
echo "   cd /home/nikh-on-linux/projectExhibition2/model"
echo "   pip install -r requirements.txt"
echo ""
echo "3. Start the model service:"
echo "   uvicorn main:app --host 0.0.0.0 --port 4000"
echo ""
echo "═══════════════════════════════════════════════════════════════"
