# Frontend Dashboard (Streamlit)

Neon-styled dark mode dashboard that now acts as the full pipeline controller.

## What This Frontend Does

The UI now performs end-to-end orchestration:

1. Enter keyword in UI.
2. Search matching rows in `raw_posts` (keyword or raw_text match).
3. Assign a new common `batch_id` to those rows.
4. Trigger cleaning service (`POST /api/clean/{batch_id}`).
5. Trigger model service (`POST /api/analyze/{batch_id}`).
6. Poll batch progress and render final joined output.

## Features

- Pipeline control panel (assign batch + trigger cleaning + trigger model)
- Hero section showing active batch and processing counts
- Donut chart for 7 emotions: joy, anger, fear, disgust, sadness, surprise, neutral
- Interactive explorer with:
	- search
	- emotion filter
	- confidence filter
	- emotion badges and confidence bars
- Live joined view from `raw_posts`, `cleaned_posts`, and `enriched_posts`

## Required Services

- Cleaning service running (default: `http://localhost:5000`)
- Model service running (default: `http://localhost:4000`)
- PostgreSQL with project tables populated

## Environment Variables

Set these before running Streamlit (optional if defaults work):

- `CLEANING_BASE_URL` (default: `http://localhost:5000`)
- `MODEL_BASE_URL` (default: `http://localhost:4000`)
- `DATABASE_URL` (default: `postgresql://emotion_app:emotion_password_123@localhost:5432/emotion_db`)

Note: If your existing env uses SQLAlchemy async format (`postgresql+asyncpg://...`), this frontend auto-normalizes it to psycopg format.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py --server.port 8000
```

## Expected Backend Endpoints

Cleaning service:
- `POST /api/clean/{batch_id}`
- `GET /api/clean/stats/{batch_id}`

Model service:
- `POST /api/analyze/{batch_id}`
- `GET /api/batch/{batch_id}`
- `GET /results/{batch_id}`
