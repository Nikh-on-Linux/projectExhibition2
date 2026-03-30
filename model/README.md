# Model Service - Batch-Based Emotion Analysis

> 🎯 **TL;DR:** Model service analyzes emotions in cleaned posts grouped by `batch_id`, stores results with the same `batch_id`, enabling end-to-end correlation through the 4-service pipeline.

**Port:** 4000

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Model (Optional but Recommended)
```bash
python download_model.py
```
Pre-caches the HuggingFace model (~500MB) to `~/.cache/huggingface/` for faster startup.

### 3. Configure Environment
Create `.env` file:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/emotion_db
MODEL_NAME=j-hartmann/emotion-english-distilroberta-base
BATCH_SIZE=32
PORT=4000
```

### 4. Start Service
```bash
uvicorn main:app --host 0.0.0.0 --port 4000
```

### 5. Test It
```bash
# Health check
curl http://localhost:4000/health

# Start analysis for batch
curl -X POST http://localhost:4000/api/analyze/batch-123

# Check progress
curl http://localhost:4000/api/batch/batch-123

# Get results
curl http://localhost:4000/results/batch-123
```

## 📖 API Endpoints

### 1. Health Check
```
GET /health
```
Response: `{"status": "ok", "service": "model", "port": 4000}`

### 2. Queue Analysis
```
POST /api/analyze/{batch_id}
```
Queues emotion analysis for a batch.
Response: `{"status": "queued", "processed": 0, "batch_id": "..."}`

### 3. Check Progress
```
GET /api/batch/{batch_id}
```
Returns: `{"batch_id": "...", "total_posts": 50, "analyzed": 35, "pending": 15}`

### 4. Get Results
```
GET /results/{batch_id}
```
Returns enriched posts with emotion analysis for frontend.

**See `QUICK_REF.txt` for complete API reference**

## 🎭 Emotion Model

Uses HuggingFace: `j-hartmann/emotion-english-distilroberta-base`

**7 Emotions:** joy, anger, fear, disgust, sadness, surprise, neutral

Output per text includes confidence score and distribution for all 7 emotions.

## 🔄 Pipeline Integration

```
Ingestion → raw_posts (batch_id)
    ↓
Cleaning → cleaned_posts (batch_id)
    ↓
Model Service (YOU ARE HERE)
    ↓
enriched_posts (batch_id + emotion analysis)
    ↓
Frontend (GET /results/{batch_id})
```

## 📚 Documentation

| File | Purpose |
|------|---------|
| **QUICK_REF.txt** | API reference |
| **00_ARCHITECTURE.md** | System design |
| **01_INTEGRATION_GUIDE.md** | Integration with other services |
| **02_MANUAL_TESTING.md** | Testing with curl |
| **REBUILD_SUMMARY.md** | What changed from v1 |

## 🧪 Testing

```bash
pytest tests/test_model.py -v
```

## 📊 Running

### Development
```bash
uvicorn main:app --host 0.0.0.0 --port 4000 --reload
```

### Production (Docker)
```bash
docker build -t emotion-model:latest .
docker run -p 4000:4000 --env-file .env emotion-model:latest
```

## API Endpoints

### GET /health
Health check endpoint
```json
{
  "status": "ok",
  "service": "model",
  "port": 4000
}
```

### GET /status
Service status with analysis progress
```json
{
  "service": "model",
  "port": 4000,
  "model": "j-hartmann/emotion-english-distilroberta-base",
  "total_enriched": 150,
  "pending": 42
}
```

### POST /api/analyze
Analyze unprocessed posts
```json
{
  "limit": 100
}
```

**Parameters:**
- `limit`: 1-500 (default: 100)
  - `<= 100`: Runs synchronously
  - `> 100`: Runs as background task

**Response:**
```json
{
  "status": "success|queued|no_data",
  "processed": 3,
  "job_id": "uuid-string",
  "message": "Optional context"
}
```

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test
```bash
pytest tests/test_model.py::test_health_endpoint -v
```

**Coverage:**
- Async endpoint tests
- Database mocking
- Inference error handling
- Batch processing
- Input validation

## Database

**Reads from:** `cleaned_posts`
- Filters: English language only (`language = 'en'`)
- Joins: Left join with `enriched_posts` to find unanalyzed posts

**Writes to:** `enriched_posts`
- 7 emotion scores: joy, anger, fear, disgust, sadness, surprise, neutral
- Primary emotion label + confidence score
- Timestamp of analysis

## Model Information

**Model:** `j-hartmann/emotion-english-distilroberta-base`
- **Type:** DistilRoBERTa fine-tuned for emotion classification
- **Languages:** English
- **Output:** 7 emotion classes
- **Size:** ~500MB
- **License:** Apache 2.0
- **Hugging Face:** https://huggingface.co/j-hartmann/emotion-english-distilroberta-base

## Architecture

```
main.py                    → FastAPI app entry point
│
├── routes/
│   ├── analyze.py         → POST /api/analyze (emotion classification)
│   └── status.py          → GET /status (progress tracking)
│
├── config.py              → Environment variables
├── db.py                  → SQLAlchemy 2.0 async ORM
├── inference.py           → HuggingFace pipeline wrapper
├── schemas.py             → Pydantic models
│
└── tests/
    ├── conftest.py        → pytest fixtures + async client
    └── test_model.py      → Unit & integration tests
```

## Performance

- **Model Load:** Once at startup (lazy init)
- **Inference:** ~50-100ms per text (CPU)
- **Batch Size:** Configurable (default: 32)
- **Async I/O:** All DB operations are async
- **Background Tasks:** For large batches (`limit > 100`)
