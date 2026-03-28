# Frontend Dashboard (Streamlit)

Neon-styled dark mode dashboard for the Reddit emotion analysis pipeline.

## Features

- System Status hero section (not generic KPI cards)
- Donut chart for the 7 emotion classes
- Interactive post explorer with:
	- text search
	- emotion filter dropdown
	- confidence threshold slider
	- emotion color badges and confidence bars
- API-first data loading with mock fallbacks if backend endpoints are not ready

## API Endpoints

The app fetches from `http://localhost:8000` (configurable via `DASHBOARD_API_URL`):

- `GET /overview`
- `GET /emotions`
- `GET /posts`

If these endpoints are unreachable or return invalid payloads, the app uses realistic mock responses.

## Quick Start

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run app (configured on port 8000):

```bash
streamlit run app.py
```

4. Optional: override API base URL:

```bash
set DASHBOARD_API_URL=http://localhost:8000
streamlit run app.py
```

## Data Shape Expected

### `/overview`
```json
{
	"total_posts": 1842,
	"platform_split": {"reddit": 1842},
	"date_range": {"start": "2026-02-27", "end": "2026-03-28"}
}
```

### `/emotions`
```json
{
	"distribution": {
		"joy": 372,
		"anger": 214,
		"fear": 177,
		"disgust": 122,
		"sadness": 313,
		"surprise": 198,
		"neutral": 446
	}
}
```

### `/posts`
```json
{
	"posts": [
		{
			"raw_text": "...",
			"cleaned_text": "...",
			"emotion_label": "joy",
			"confidence": 0.94,
			"platform": "reddit",
			"created_at": "2026-03-28T15:41:00"
		}
	]
}
```
