# Local Database Setup Guide

Complete guide to set up PostgreSQL locally and populate test data for the emotion analysis pipeline.

## Prerequisites

- PostgreSQL installed (version 12+)
- psql command-line tool
- 500MB free disk space

## Step 1: Start PostgreSQL

### On Linux:
```bash
sudo systemctl start postgresql
```

### On macOS (Homebrew):
```bash
brew services start postgresql
```

### On Windows:
- Open Services and find "PostgreSQL" or start via PostgreSQL application

Verify it's running:
```bash
psql --version
```

## Step 2: Create Database & User

Connect to PostgreSQL as superuser:
```bash
sudo -u postgres psql
```

Then run these SQL commands:
```sql
-- Create database
CREATE DATABASE emotion_db;

-- Create user with password
CREATE USER emotion_app WITH PASSWORD 'emotion_password_123';

-- Grant all privileges
ALTER ROLE emotion_app WITH CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE emotion_db TO emotion_app;

-- Connect to the new database
\c emotion_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO emotion_app;

-- Exit
\q
```

## Step 3: Create Tables

Navigate to database directory and run SQL files in order:

```bash
cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/database

# Create tables
psql -U emotion_app -d emotion_db -f 01_create_raw_posts_table.sql
psql -U emotion_app -d emotion_db -f 02_create_cleaned_posts_table.sql
psql -U emotion_app -d emotion_db -f 03_create_enriched_posts_table.sql
```

You'll be prompted for the password: `emotion_password_123`

## Step 4: Add Test Data

Option A: Using provided sample data
```bash
psql -U emotion_app -d emotion_db -f 04_sample_data.sql
```

Option B: Using the custom test data (see below)
```bash
psql -U emotion_app -d emotion_db -f test_data_comprehensive.sql
```

## Step 5: Verify Setup

Connect to database and check tables exist:
```bash
psql -U emotion_app -d emotion_db

-- List tables
\dt

-- Count records
SELECT COUNT(*) FROM raw_posts;
SELECT COUNT(*) FROM cleaned_posts;

-- View sample data
SELECT * FROM raw_posts LIMIT 5;
```

## Step 6: Update .env File

Create or update `.env` file in the cleaning directory:

```bash
cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/cleaning
```

Create `.env` with:
```
DATABASE_URL=postgresql+asyncpg://emotion_app:emotion_password_123@localhost:5432/emotion_db
PORT=5000
BATCH_SIZE=50
```

## Step 7: Install Python Dependencies

```bash
cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/cleaning

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 8: Test the Setup

Run the unit tests:
```bash
pytest tests/test_cleaner.py -v
```

Start the FastAPI server:
```bash
python main.py
```

Server should start on `http://localhost:5000`

## Quick Commands Reference

### Check if PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

### Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Access database directly:
```bash
psql -U emotion_app -d emotion_db
```

### View raw posts:
```sql
SELECT id, batch_id, keyword, raw_text FROM raw_posts LIMIT 10;
```

### View cleaned posts:
```sql
SELECT id, raw_post_id, batch_id, cleaned_text, language FROM cleaned_posts LIMIT 10;
```

### Reset database (WARNING - deletes all data):
```bash
psql -U emotion_app -d emotion_db -c "DROP TABLE IF EXISTS cleaned_posts, raw_posts, enriched_posts CASCADE;"
psql -U emotion_app -d emotion_db -f 01_create_raw_posts_table.sql
psql -U emotion_app -d emotion_db -f 02_create_cleaned_posts_table.sql
psql -U emotion_app -d emotion_db -f 03_create_enriched_posts_table.sql
```

### Delete and repopulate test data:
```bash
psql -U emotion_app -d emotion_db -c "DELETE FROM cleaned_posts; DELETE FROM raw_posts;"
psql -U emotion_app -d emotion_db -f test_data_comprehensive.sql
```

## Troubleshooting

### "FATAL: role 'emotion_app' does not exist"
- Update password in `.env` to correct value (default: `emotion_password_123`)

### "could not translate host name 'localhost' to address"
- PostgreSQL service is not running. Start it first.

### "connection refused" on port 5432
- PostgreSQL might be running on a different port. Check with: `sudo lsof -i :5432`

### "peer authentication failed"
- Use full connection string with -U flag: `psql -U emotion_app -d emotion_db`

## Testing the Cleaning API

### Start the server:
```bash
cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/cleaning
python main.py
```

### Test cleaning endpoint with curl:
```bash
# Clean a batch (batch_id must exist in raw_posts)
curl -X POST http://localhost:5000/api/clean/test-batch-001

# Get cleaning stats
curl http://localhost:5000/api/clean/stats/test-batch-001

# Health check
curl http://localhost:5000/health
```

### Test with Python:
```python
import requests
import json

BASE_URL = "http://localhost:5000"

# Clean a batch
response = requests.post(f"{BASE_URL}/api/clean/test-batch-001")
print(json.dumps(response.json(), indent=2))

# Get stats
response = requests.get(f"{BASE_URL}/api/clean/stats/test-batch-001")
print(json.dumps(response.json(), indent=2))

# Health check
response = requests.get(f"{BASE_URL}/health")
print(json.dumps(response.json(), indent=2))
```

---

**Next Steps:**
1. Follow steps 1-5 above to set up database
2. Create `.env` file with database connection string
3. Run tests: `pytest tests/test_cleaner.py -v`
4. Start server: `python main.py`
5. Test endpoints with curl or Python
