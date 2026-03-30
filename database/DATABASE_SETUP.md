# Complete Database Setup Guide

## ✅ Prerequisites

You already have PostgreSQL installed. Verify it's running:

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql
```

---

## 🚀 Quick Setup (5 minutes)

### Option 1: Using Setup Script (Recommended)

```bash
cd /home/nikh-on-linux/projectExhibition2/database

# Make executable
chmod +x setup_database.sh

# Run with defaults (creates user: emotion_app, password: emotion_password_123)
bash setup_database.sh

# Or with custom credentials
DB_USER=myuser DB_PASSWORD=mypass DB_NAME=mydb bash setup_database.sh
```

### Option 2: Manual Setup

```bash
# Step 1: Create user and database
sudo -u postgres psql << SQL
CREATE USER emotion_app WITH PASSWORD 'emotion_password_123';
CREATE DATABASE emotion_db OWNER emotion_app;
GRANT ALL PRIVILEGES ON DATABASE emotion_db TO emotion_app;
SQL

# Step 2: Create tables
cd /home/nikh-on-linux/projectExhibition2/database
psql -U emotion_app -d emotion_db -f 01_create_raw_posts_table.sql
psql -U emotion_app -d emotion_db -f 02_create_cleaned_posts_table.sql
psql -U emotion_app -d emotion_db -f 03_create_enriched_posts_table.sql

# Step 3: Load sample test data
psql -U emotion_app -d emotion_db -f 04_sample_data.sql
```

---

## 📊 Database Credentials (Default)

```
Host:     localhost
Port:     5432
User:     emotion_app
Password: emotion_password_123
Database: emotion_db
```

**For Python (.env file):**
```env
DATABASE_URL=postgresql+asyncpg://emotion_app:emotion_password_123@localhost:5432/emotion_db
```

---

## 📋 Verify Setup

```bash
# Check all tables exist
psql -U emotion_app -d emotion_db -c "\dt"

# Count data in each table
psql -U emotion_app -d emotion_db -c "
SELECT 'raw_posts' as table_name, COUNT(*) as count FROM raw_posts
UNION ALL
SELECT 'cleaned_posts', COUNT(*) FROM cleaned_posts
UNION ALL
SELECT 'enriched_posts', COUNT(*) FROM enriched_posts;
"

# View test batches
psql -U emotion_app -d emotion_db -c "
SELECT batch_id, COUNT(*) as posts FROM cleaned_posts GROUP BY batch_id;
"

# View sample cleaned posts
psql -U emotion_app -d emotion_db -c "
SELECT batch_id, id, cleaned_text 
FROM cleaned_posts 
WHERE batch_id='test-batch-001' 
LIMIT 5;
"
```

**Expected Output:**
- raw_posts: 40 posts
- cleaned_posts: 40 posts (3 batches: test-batch-001, test-batch-002, test-batch-003)
- enriched_posts: 0 posts (will populate after model analysis)

---

## 🧪 Test Data Overview

Three test batches are pre-loaded:

### test-batch-001 (20 posts)
- Topics: climate change, renewable energy, electric vehicles, green tech
- Emotions: mix of joy, anger, fear, disgust, surprise, neutral
- Purpose: General testing

### test-batch-002 (10 posts)
- Topics: net zero, energy transition, climate policy, conservation
- Purpose: Testing concurrent batch processing

### test-batch-003 (10 posts)
- Topics: renewable energy with specific emotions
- Purpose: Testing all 7 emotions (1 post per emotion + combinations)

---

## �� Database Schema

### raw_posts table
```sql
- id (SERIAL PRIMARY KEY)
- platform (VARCHAR)
- keyword (VARCHAR)
- raw_text (TEXT)
- created_at (TIMESTAMP)
- raw_json (JSONB)
- fetched_at (TIMESTAMP)
```

### cleaned_posts table
```sql
- id (SERIAL PRIMARY KEY)
- raw_post_id (INT, FK to raw_posts)
- batch_id (VARCHAR) ← Groups posts from same search
- cleaned_text (TEXT) ← Input to emotion model
- language (VARCHAR) ← Filtered for 'en' only
- emoji_converted (BOOLEAN)
- processed_at (TIMESTAMP)
```

### enriched_posts table
```sql
- id (SERIAL PRIMARY KEY)
- cleaned_post_id (INT, FK to cleaned_posts)
- emotion_label (VARCHAR) ← joy, anger, fear, disgust, sadness, surprise, neutral
- confidence (DECIMAL) ← 0-1 confidence score
- emotion_intensity (DECIMAL)
- emotion_distribution_data (JSONB) ← All 7 emotion scores
- batch_id (VARCHAR) ← Pass-through from cleaned_posts
- analyzed_at (TIMESTAMP)
```

---

## ✅ Testing with Model Service

After database is set up and data loaded:

### 1. Start Model Service
```bash
cd /home/nikh-on-linux/projectExhibition2/model
pip install -r requirements.txt
python download_model.py
uvicorn main:app --host 0.0.0.0 --port 4000
```

### 2. Test Health Check
```bash
curl -s http://localhost:4000/health | jq .
```

### 3. Queue Analysis on test-batch-001
```bash
curl -s -X POST http://localhost:4000/api/analyze/test-batch-001 | jq .
```

### 4. Check Progress
```bash
curl -s http://localhost:4000/api/batch/test-batch-001 | jq .
```

### 5. View Results (After Complete)
```bash
curl -s http://localhost:4000/results/test-batch-001 | jq '.results | .[0:3]'
```

### 6. Verify in Database
```bash
psql -U emotion_app -d emotion_db -c "
SELECT 
  batch_id,
  emotion_label,
  COUNT(*) as count,
  AVG(confidence) as avg_confidence
FROM enriched_posts
GROUP BY batch_id, emotion_label
ORDER BY batch_id, count DESC;
"
```

---

## 🚨 Troubleshooting

### PostgreSQL Connection Error

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Enable auto-start on boot
sudo systemctl enable postgresql
```

### "database emotion_db already exists" error

```bash
# Drop and recreate
psql -U postgres -c "DROP DATABASE emotion_db;"
psql -U postgres -c "DROP USER emotion_app;"

# Then run setup again
bash setup_database.sh
```

### "permission denied" for user

```bash
# Grant proper permissions
sudo -u postgres psql << SQL
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO emotion_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO emotion_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO emotion_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO emotion_app;
SQL
```

### "Cannot connect to database from Python"

1. Verify credentials in .env:
   ```bash
   cat /home/nikh-on-linux/projectExhibition2/model/.env
   ```

2. Verify DATABASE_URL format:
   ```
   postgresql+asyncpg://emotion_app:emotion_password_123@localhost:5432/emotion_db
   ```

3. Test connection:
   ```bash
   psql -U emotion_app -d emotion_db -c "SELECT 1;"
   ```

### Reset Everything (Full Clean Slate)

```bash
# Stop PostgreSQL
sudo systemctl stop postgresql

# Remove PostgreSQL data (WARNING: Deletes all databases!)
sudo rm -rf /var/lib/postgresql/*/main/*

# Start PostgreSQL fresh
sudo systemctl start postgresql

# Run setup again
bash /home/nikh-on-linux/projectExhibition2/database/setup_database.sh
```

---

## 📝 SQL Queries for Testing

### View all batches and post counts
```sql
SELECT batch_id, COUNT(*) as post_count 
FROM cleaned_posts 
GROUP BY batch_id;
```

### View unanalyzed posts
```sql
SELECT cp.batch_id, COUNT(cp.id) as unanalyzed
FROM cleaned_posts cp
LEFT JOIN enriched_posts ep ON cp.id = ep.cleaned_post_id
WHERE ep.id IS NULL
GROUP BY cp.batch_id;
```

### View emotion distribution for a batch
```sql
SELECT 
  batch_id,
  emotion_label,
  COUNT(*) as count,
  ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM enriched_posts WHERE batch_id='test-batch-001') * 100, 2) as percentage
FROM enriched_posts
WHERE batch_id = 'test-batch-001'
GROUP BY batch_id, emotion_label
ORDER BY count DESC;
```

### View average confidence by emotion
```sql
SELECT 
  emotion_label,
  COUNT(*) as count,
  ROUND(AVG(confidence)::numeric, 4) as avg_confidence,
  ROUND(MIN(confidence)::numeric, 4) as min_confidence,
  ROUND(MAX(confidence)::numeric, 4) as max_confidence
FROM enriched_posts
GROUP BY emotion_label
ORDER BY avg_confidence DESC;
```

---

## 🎯 Next Steps

1. ✅ Database created with tables and sample data
2. Set DATABASE_URL in .env file
3. Install model service: `pip install -r requirements.txt`
4. Download emotion model: `python download_model.py`
5. Start service: `uvicorn main:app --port 4000`
6. Test with sample batches using curl commands
7. Monitor database as results populate

---

## 📞 Support

For issues:
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify credentials: `psql -U emotion_app -d emotion_db -c "SELECT 1;"`
3. Check table structure: `psql -U emotion_app -d emotion_db -c "\d cleaned_posts"`
4. View sample data: `psql -U emotion_app -d emotion_db -c "SELECT * FROM cleaned_posts LIMIT 5;"`
