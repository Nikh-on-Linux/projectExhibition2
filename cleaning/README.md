# Cleaning Service

Service that cleans, processes, and normalizes raw Reddit posts for emotion analysis.

## Architecture

This microservice sits between `raw_posts` and `cleaned_posts` in the PostgreSQL pipeline:

```
[Ingestion] → raw_posts → [Cleaning Service] → cleaned_posts → [Model Service] → enriched_posts
```

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run the service
python main.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/clean/{batch_id}` | Clean all raw posts for a batch |
| `GET` | `/api/clean/stats/{batch_id}` | Get cleaning progress stats |
| `GET` | `/health` | Health check |

## Cleaning Rules

- **Emojis**: Replaced with descriptive names (e.g. `😠` → `_angry_face_`)
- **URLs**: Stripped entirely (http/https/www)
- **@Mentions**: Stripped entirely
- **Hashtags**: `#` removed, meaningful words kept, noise hashtags dropped
- **Encoding**: `&amp;` → `and`, `&lt;` → `<`, etc.
- **Punctuation**: `!!!!!` → `!`, `......` → `...`
- **Separators**: ASCII art and separator lines removed
- **Whitespace**: Collapsed and trimmed
- **Preserved**: Negations, contractions, slang, capitalisation, word order

## Running Tests

```bash
python -m pytest tests/test_cleaner.py -v
```
