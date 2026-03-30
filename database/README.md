# Database Setup Guide

PostgreSQL database initialization scripts for the Emotion Analysis Pipeline. This directory contains all SQL schemas and setup tools needed to get your database ready.

## Quick Start (Recommended)

### Option 1: Automated Setup (Easiest)

```bash
cd /home/nikh-on-linux/projectExhibition2/database
chmod +x setup_database.sh
./setup_database.sh
```

This script will:
- Create PostgreSQL database (`emotion_db`)
- Create database user (`emotion_app` with password `emotion_password_123`)
- Create all three tables with batch_id support
- Grant necessary permissions
- Verify the setup

### Option 2: Manual Step-by-Step Setup

**Step 1: Connect to PostgreSQL**
```bash
sudo -u postgres psql
```

**Step 2: Create Database**
```sql
CREATE DATABASE emotion_db;
```

**Step 3: Create Database User**
```sql
CREATE USER emotion_app WITH PASSWORD 'emotion_password_123';
```

**Step 4: Grant Privileges**
```sql
GRANT ALL PRIVILEGES ON DATABASE emotion_db TO emotion_app;
```

**Step 5: Connect to the new database**
```sql
\c emotion_db
```

**Step 6: Grant Schema Privileges**
```sql
GRANT ALL PRIVILEGES ON SCHEMA public TO emotion_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO emotion_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO emotion_app;
```

**Step 7: Exit psql**
```sql
\q
```

**Step 8: Create Tables**
```bash
psql -U postgres -d emotion_db -f 01_create_raw_posts_table.sql
psql -U postgres -d emotion_db -f 02_create_cleaned_posts_table.sql
psql -U postgres -d emotion_db -f 03_create_enriched_posts_table.sql
```

### Option 3: One-Line Setup (For Advanced Users)

```bash
sudo -u postgres psql -c "CREATE DATABASE emotion_db;" && \
sudo -u postgres psql -c "CREATE USER emotion_app WITH PASSWORD 'emotion_password_123';" && \
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE emotion_db TO emotion_app;" && \
psql -U postgres -d emotion_db -f /home/nikh-on-linux/projectExhibition2/database/01_create_raw_posts_table.sql && \
psql -U postgres -d emotion_db -f /home/nikh-on-linux/projectExhibition2/database/02_create_cleaned_posts_table.sql && \
psql -U postgres -d emotion_db -f /home/nikh-on-linux/projectExhibition2/database/03_create_enriched_posts_table.sql && \
psql -U postgres -d emotion_db -c "GRANT ALL PRIVILEGES ON SCHEMA public TO emotion_app;" && \
psql -U postgres -d emotion_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO emotion_app;" && \
psql -U postgres -d emotion_db -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO emotion_app;"
```

## Configuration

### Database Connection String

Add this to your `.env` file in the model directory:

```
DATABASE_URL=postgresql+asyncpg://emotion_app:emotion_password_123@localhost:5432/emotion_db
```

### Change Credentials

If you prefer different credentials, edit `setup_database.sh`:

```bash
DB_USER="your_username"
DB_PASSWORD="your_password"
DB_NAME="your_database_name"
DB_HOST="localhost"  # or your server address
DB_PORT="5432"       # or your PostgreSQL port
```

Then run:
```bash
./setup_database.sh
```

## Verify Setup

### Check Tables Exist

```bash
psql -U emotion_app -d emotion_db -c "\dt"
```

Should output:
```
               List of relations
 Schema |       Name       | Type  |     Owner
--------+------------------+-------+-----------
 public | cleaned_posts    | table | postgres
 public | enriched_posts   | table | postgres
 public | raw_posts        | table | postgres
(3 rows)
```

### Check Table Structure

```bash
# Check raw_posts
psql -U emotion_app -d emotion_db -c "\d raw_posts"

# Check cleaned_posts
psql -U emotion_app -d emotion_db -c "\d cleaned_posts"

# Check enriched_posts
psql -U emotion_app -d emotion_db -c "\d enriched_posts"
```

### Test Connection

```bash
psql -U emotion_app -d emotion_db -c "SELECT 1;"
```

Should output:
```
 ?column?
----------
        1
(1 row)
```

## Database Schema

### raw_posts Table
Stores original posts from ingestion service.

**Columns:**
- `id` (INT PRIMARY KEY) - Auto-incrementing post ID
- `batch_id` (VARCHAR 255) - Batch identifier from ingestion service
- `platform` (VARCHAR 50) - Source platform (twitter, reddit, etc.)
- `platform_post_id` (VARCHAR 255) - Original post ID on platform
- `author_id` (VARCHAR 255) - Author identifier
- `created_at` (TIMESTAMP) - Post creation timestamp
- `text` (TEXT) - Original post text
- `metadata_json` (JSONB) - Additional metadata
- `ingested_at` (TIMESTAMP) - When ingested

**Indexes:**
- Primary key on `id`
- `idx_raw_posts_batch_id` on `batch_id` (for batch queries)

### cleaned_posts Table
Stores processed posts from cleaning service.

**Columns:**
- `id` (INT PRIMARY KEY) - Auto-incrementing post ID
- `raw_post_id` (INT FK) - Reference to raw_posts
- `batch_id` (VARCHAR 255) - Batch identifier (matches raw_posts)
- `cleaned_text` (TEXT) - Processed text
- `language` (VARCHAR 20) - Detected language
- `emoji_converted` (BOOLEAN) - Whether emojis were converted
- `processing_notes` (TEXT) - Processing details
- `processed_at` (TIMESTAMP) - When processed

**Indexes:**
- Primary key on `id`
- Foreign key on `raw_post_id`
- `idx_cleaned_posts_batch_id` on `batch_id` (for batch queries)

### enriched_posts Table
Stores emotion analysis results from model service.

**Columns:**
- `id` (INT PRIMARY KEY) - Auto-incrementing post ID
- `cleaned_post_id` (INT FK) - Reference to cleaned_posts
- `batch_id` (VARCHAR 255) - Batch identifier (matches cleaned_posts)
- `emotion_label` (VARCHAR 20) - Detected emotion
- `confidence` (FLOAT) - Confidence score (0-1)
- `emotion_intensity` (FLOAT) - Intensity of emotion
- `emotion_distribution_data` (JSONB) - Full emotion distribution
- `analyzed_at` (TIMESTAMP) - When analyzed

**Indexes:**
- Primary key on `id`
- Foreign key on `cleaned_post_id`
- `idx_enriched_posts_batch_id` on `batch_id` (for batch queries)

## Batch Processing Flow

The database supports the 4-service pipeline with batch_id correlation:

```
Ingestion Service
    ↓
    Creates batch_id, stores in raw_posts.batch_id
    ↓
Cleaning Service
    ↓
    Reads raw_posts by batch_id
    Creates cleaned_posts with same batch_id
    ↓
Model Service
    ↓
    Reads cleaned_posts by batch_id
    Creates enriched_posts with same batch_id
    ↓
Frontend Service
    ↓
    Queries enriched_posts by batch_id
    Displays results
```

## Troubleshooting

### Connection Refused
- Make sure PostgreSQL is running: `sudo systemctl status postgresql`
- Start PostgreSQL: `sudo systemctl start postgresql`
- Check if listening on port 5432: `sudo netstat -tulpn | grep postgres`

### Permission Denied
- Ensure emotion_app user has proper permissions (script handles this)
- Manually grant: `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO emotion_app;`

### Table Already Exists
- Drop existing tables: `psql -U postgres -d emotion_db -c "DROP TABLE IF EXISTS enriched_posts CASCADE;"`
- Then run setup script again

### Can't Connect as emotion_app
- Verify user exists: `psql -U postgres -c "\du"`
- Verify database exists: `psql -U postgres -c "\l"`
- Reset password: `psql -U postgres -c "ALTER USER emotion_app WITH PASSWORD 'emotion_password_123';"`

### Port Already in Use
- Find what's using port 5432: `sudo lsof -i :5432`
- Change port in `setup_database.sh`: `DB_PORT="5433"`

## Backup & Restore

### Backup Database
```bash
pg_dump -U emotion_app -d emotion_db > emotion_db_backup.sql
```

### Restore Database
```bash
# Drop existing database (if needed)
psql -U postgres -c "DROP DATABASE emotion_db;"

# Recreate database
psql -U postgres -c "CREATE DATABASE emotion_db;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE emotion_db TO emotion_app;"

# Restore from backup
psql -U postgres -d emotion_db -f emotion_db_backup.sql
```

### Export Data
```bash
# Export raw posts as CSV
psql -U emotion_app -d emotion_db -c "\COPY raw_posts TO 'raw_posts.csv' WITH CSV HEADER;"

# Export cleaned posts as CSV
psql -U emotion_app -d emotion_db -c "\COPY cleaned_posts TO 'cleaned_posts.csv' WITH CSV HEADER;"

# Export enriched posts as CSV
psql -U emotion_app -d emotion_db -c "\COPY enriched_posts TO 'enriched_posts.csv' WITH CSV HEADER;"
```

## Next Steps

1. **Run Setup**
   ```bash
   cd /home/nikh-on-linux/projectExhibition2/database
   chmod +x setup_database.sh
   ./setup_database.sh
   ```

2. **Configure Model Service**
   ```bash
   cd /home/nikh-on-linux/projectExhibition2/model
   cat > .env << EOF
   DATABASE_URL=postgresql+asyncpg://emotion_app:emotion_password_123@localhost:5432/emotion_db
   MODEL_NAME=j-hartmann/emotion-english-distilroberta-base
   BATCH_SIZE=32
   PORT=4000
   EOF
   ```

3. **Start Model Service**
   ```bash
   pip install -r requirements.txt
   python download_model.py
   uvicorn main:app --host 0.0.0.0 --port 4000
   ```

4. **Test Connection**
   ```bash
   psql -U emotion_app -d emotion_db -c "SELECT COUNT(*) FROM raw_posts;"
   ```

## Support

For issues, check:
- PostgreSQL logs: `/var/log/postgresql/`
- Model service logs: Check console output
- Database schema files: `01_create_raw_posts_table.sql`, etc.

---

**Last Updated:** 2024
**Status:** ✅ All tables include batch_id support for 4-service pipeline
