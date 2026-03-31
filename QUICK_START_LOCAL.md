# 🚀 Quick Start Guide - Local Testing

Complete step-by-step guide to set up and test the emotion analysis pipeline locally.

## ⏱️ Time Required: ~10-15 minutes

---

## Step 1: Start PostgreSQL (1 minute)

```bash
# Linux
sudo systemctl start postgresql

# macOS
brew services start postgresql

# Windows - Open PostgreSQL in Services or application
```

Verify it's running:
```bash
psql --version
```

---

## Step 2: Create Database & User (2 minutes)

Open PostgreSQL:
```bash
sudo -u postgres psql
```

Run these commands:
```sql
CREATE DATABASE emotion_db;
CREATE USER emotion_app WITH PASSWORD 'emotion_password_123';
ALTER ROLE emotion_app WITH CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE emotion_db TO emotion_app;
\c emotion_db
GRANT ALL ON SCHEMA public TO emotion_app;
\q
```

---

## Step 3: Create Tables (1 minute)

```bash
cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/database

# Create all tables (use PGPASSWORD environment variable)
export PGPASSWORD="emotion_password_123"
psql -U emotion_app -d emotion_db -f 01_create_raw_posts_table.sql
psql -U emotion_app -d emotion_db -f 02_create_cleaned_posts_table.sql
psql -U emotion_app -d emotion_db -f 03_create_enriched_posts_table.sql
```

**Note:** If you get "peer authentication failed" errors, see the troubleshooting section.

---

## Step 4: Add Test Data (1 minute)

```bash
# Use this command to load 40 test posts (3 batches)
export PGPASSWORD="emotion_password_123"
psql -U emotion_app -d emotion_db -f 04_sample_data.sql

# Verify 40 posts were loaded
psql -U emotion_app -d emotion_db -c "SELECT COUNT(*) FROM raw_posts;"
```

**Expected output:** `count: 40` (or similar positive number)

---

## Step 5: Setup Python Environment (2 minutes)

```bash
cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/cleaning

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
# On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 6: Configure .env (1 minute)

```bash
# Copy example
cp .env.example .env

# Verify it contains:
cat .env
```

Should show:
```
DATABASE_URL=postgresql+asyncpg://emotion_app:emotion_password_123@localhost:5432/emotion_db
PORT=5000
BATCH_SIZE=50
```

---

## Step 7: Run Tests (2 minutes)

```bash
cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/cleaning

# Run unit tests
pytest tests/test_cleaner.py -v

# Expected: 40+ tests should PASS ✅
```

---

## Step 8: Start the API Server (1 minute)

```bash
cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/cleaning

python main.py
```

Server should start on: `http://localhost:5000`

---

## Step 9: Test the API (3 minutes)

Open another terminal and run:

```bash
# Option A: Use Python test script (comprehensive tests)
cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/cleaning
python test_api.py

# Option B: Test specific batches with curl
curl http://localhost:5000/health

curl -X POST http://localhost:5000/api/clean/test-batch-001

curl http://localhost:5000/api/clean/stats/test-batch-001

# Option C: Test all batches
for batch in test-batch-{001,002,003}; do
  echo "Testing $batch..."
  curl -X POST http://localhost:5000/api/clean/$batch | head -20
done
```

---

## 📊 Test Data Available

You have **3 batches with 40 total posts** loaded and ready to test:

### `test-batch-001` (20 posts)
- Climate, renewable energy, electric vehicles topics
- Various emotions (joy, anger, sadness, fear, surprise)
- Emoji usage, URLs, mentions, hashtags
- **Best for:** Comprehensive testing of cleaning pipeline

### `test-batch-002` (10 posts)
- Net zero, energy transition, climate policy topics
- Mixed emotional content
- Real discussion format
- **Best for:** Testing domain-specific content

### `test-batch-003` (10 posts)
- Renewable energy focus
- Full spectrum of emotions
- Various text formatting challenges
- **Best for:** Testing emotion detection and edge cases

---

## 🔍 Verify Your Setup

Check database has data:
```bash
export PGPASSWORD="emotion_password_123"
psql -U emotion_app -d emotion_db -c "SELECT COUNT(*) FROM raw_posts;"

# Should show: count
#       ----
#        40 (40 posts loaded from sample data)
```

Check API is responding:
```bash
curl http://localhost:5000/health | python -m json.tool

# Should show:
# {
#   "status": "ok",
#   "service": "cleaning",
#   "port": 5000,
#   "timestamp": "2026-03-31T..."
# }
```

---

## 🐛 Troubleshooting

### "Peer authentication failed" error

This means PostgreSQL is using socket authentication instead of password. **Fix:**

```bash
# 1. Modify PostgreSQL authentication config
sudo sed -i 's/^local   all             all                                     peer/local   all             all                                     md5/' /etc/postgresql/*/main/pg_hba.conf

# 2. Restart PostgreSQL
sudo systemctl restart postgresql

# 3. Grant permissions
sudo -u postgres psql -d emotion_db -c "GRANT ALL ON SCHEMA public TO emotion_app; GRANT CREATE ON SCHEMA public TO emotion_app;"

# 4. Test connection (use PGPASSWORD)
export PGPASSWORD="emotion_password_123"
psql -U emotion_app -d emotion_db -c "SELECT version();"
```

After this fix, all subsequent psql commands should work with `export PGPASSWORD="emotion_password_123"` before them.

### Server won't start
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill existing process
kill -9 <PID>

# Try different port
PORT=5001 python main.py
```

### Database connection error
```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Test connection with password
export PGPASSWORD="emotion_password_123"
psql -U emotion_app -d emotion_db -c "SELECT 1;"

# Update .env if needed
cat .env  # verify DATABASE_URL is correct
```

### "No module named 'fastapi'"
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Tests are failing
```bash
# Check database is populated
psql -U emotion_app -d emotion_db -c "SELECT * FROM raw_posts LIMIT 1;"

# Verify .env settings in the cleaning directory
cat /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/cleaning/.env
```

---

## 📝 Sample Test Requests

### Clean a batch (POST)
```bash
curl -X POST http://localhost:5000/api/clean/test-batch-001 | python -m json.tool
```

Response example:
```json
{
  "status": "success",
  "batch_id": "test-batch-001",
  "total_processed": 20,
  "signal": "BATCH_CLEAN_OK",
  "results": [
    {
      "post_id": 1,
      "batch_id": "test-batch-001",
      "cleaned_text": "i love renewable energy so happy",
      "language": "en",
      "emoji_converted": true,
      "status": "ok",
      "flags": ["had_emojis"]
    }
    // ... more results
  ]
}
```

### Get stats for batch (GET)
```bash
curl http://localhost:5000/api/clean/stats/test-batch-001 | python -m json.tool
```

Response example:
```json
{
  "batch_id": "test-batch-001",
  "total_raw": 20,
  "cleaned": 20,
  "pending": 0
}
```

### Health check (GET)
```bash
curl http://localhost:5000/health | python -m json.tool
```

---

## 🎯 Next Steps After Setup

1. **Run the test suite:**
   ```bash
   pytest tests/ -v --cov=cleaning
   ```

2. **Test with different batches:**
   ```bash
   python test_api.py
   ```

3. **Examine cleaned posts in database:**
   ```bash
   export PGPASSWORD="emotion_password_123"
   psql -U emotion_app -d emotion_db
   SELECT cleaned_text, status, flags FROM cleaned_posts LIMIT 5;
   ```

4. **Add your own posts to test:**
   ```sql
   INSERT INTO raw_posts (batch_id, platform, keyword, raw_text)
   VALUES ('my-batch', 'reddit', 'test', 'Your test text here 😊');
   ```

5. **Test the new batch:**
   ```bash
   curl -X POST http://localhost:5000/api/clean/my-batch
   ```

---

## ✅ Checklist

- [ ] PostgreSQL running
- [ ] Database created: `emotion_db`
- [ ] User created: `emotion_app`
- [ ] Tables created (3 tables)
- [ ] Test data loaded (50+ posts)
- [ ] Python venv activated
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Unit tests passing ✅
- [ ] API server running
- [ ] Health check working
- [ ] Can clean batches
- [ ] Can get statistics

---

## 📞 Need Help?

Check these files for more details:
- Setup guide: `LOCAL_SETUP.md`
- Database info: `database/README.md`
- Test examples: `test_api.py`
- Code review: `CLEANUP_REPORT.md` (if available)

