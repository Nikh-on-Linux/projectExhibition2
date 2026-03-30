#!/bin/bash

echo "🚀 Quick Database Setup"
echo "======================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking PostgreSQL status...${NC}"
if ! sudo systemctl is-active --quiet postgresql; then
    echo -e "${RED}PostgreSQL is not running. Starting...${NC}"
    sudo systemctl start postgresql
    sleep 2
fi

echo -e "${GREEN}✓ PostgreSQL is running${NC}"

# Set credentials
DB_USER=${DB_USER:-emotion_app}
DB_PASSWORD=${DB_PASSWORD:-emotion_password_123}
DB_NAME=${DB_NAME:-emotion_db}

echo -e "${YELLOW}Setting up database: $DB_NAME${NC}"

# Drop existing (optional - uncomment to reset)
# sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
# sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;"

# Create user and database
echo -e "${YELLOW}Creating user and database...${NC}"
sudo -u postgres psql << SQL
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
SQL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ User and database created${NC}"
else
    echo -e "${YELLOW}⚠ User/database may already exist (that's OK)${NC}"
fi

# Create tables
echo -e "${YELLOW}Creating tables...${NC}"
psql -U $DB_USER -d $DB_NAME -f 01_create_raw_posts_table.sql > /dev/null 2>&1
psql -U $DB_USER -d $DB_NAME -f 02_create_cleaned_posts_table.sql > /dev/null 2>&1
psql -U $DB_USER -d $DB_NAME -f 03_create_enriched_posts_table.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Tables created${NC}"
else
    echo -e "${RED}✗ Error creating tables${NC}"
    exit 1
fi

# Load sample data
echo -e "${YELLOW}Loading sample test data...${NC}"
psql -U $DB_USER -d $DB_NAME -f 04_sample_data.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Sample data loaded${NC}"
else
    echo -e "${RED}✗ Error loading sample data${NC}"
    exit 1
fi

# Verify data
echo -e "${YELLOW}Verifying data...${NC}"
psql -U $DB_USER -d $DB_NAME << SQL
SELECT 
  'raw_posts' as table_name, COUNT(*) as count FROM raw_posts
UNION ALL
SELECT 'cleaned_posts', COUNT(*) FROM cleaned_posts
UNION ALL
SELECT 'enriched_posts', COUNT(*) FROM enriched_posts;
SQL

echo ""
echo -e "${GREEN}✅ Database setup complete!${NC}"
echo ""
echo "Credentials:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo "  Database: $DB_NAME"
echo ""
echo "Test batches loaded:"
psql -U $DB_USER -d $DB_NAME -c "SELECT batch_id, COUNT(*) as posts FROM cleaned_posts GROUP BY batch_id ORDER BY batch_id;"
echo ""
echo "Next steps:"
echo "  1. Update .env file in model/ with DATABASE_URL"
echo "  2. cd /home/nikh-on-linux/projectExhibition2/model"
echo "  3. pip install -r requirements.txt"
echo "  4. python download_model.py"
echo "  5. uvicorn main:app --host 0.0.0.0 --port 4000"
echo ""
