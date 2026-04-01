"""Ingestion service module for Server 1.

This module reads device comments from a local source (CSV or PostgreSQL),
creates a batch id, inserts raw records into the `raw_posts` table, and
returns a JSON-serializable response for frontend tracking.
"""

import csv
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

RAW_POSTS_TABLE = "raw_posts"

# TODO: Adjust these mappings if your `raw_posts` schema uses different column names.
RAW_POSTS_COLUMN_MAPPING = {
    "batch_id": "batch_id",
    "keyword": "keyword",
    "comment_text": "comment_text",
    "created_at": "created_at",
    # "source": "source",
    # "status": "status",
}

DEFAULT_SOURCE_CONFIG: Dict[str, Any] = {
    "type": "csv",  # or "postgresql"
    "csv_path": "device_comments.csv",
    "csv_keyword_column": "device",
    "csv_comment_column": "comment",
    "postgresql_table": "device_comments",
    "postgresql_keyword_column": "device",
    "postgresql_comment_column": "comment",
    "postgresql_batch_column": None,
}


def get_db_config_from_env() -> Dict[str, str]:
    """Load database configuration from environment variables."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


def get_source_config_from_env() -> Dict[str, Any]:
    """Load source configuration from environment variables."""
    source_type = os.getenv("SOURCE_TYPE", DEFAULT_SOURCE_CONFIG["type"]).strip().lower()
    config: Dict[str, Any] = {**DEFAULT_SOURCE_CONFIG, "type": source_type}

    if source_type == "csv":
        config["csv_path"] = os.getenv("SOURCE_CSV_PATH", DEFAULT_SOURCE_CONFIG["csv_path"])
        config["csv_keyword_column"] = os.getenv(
            "SOURCE_CSV_KEYWORD_COLUMN", DEFAULT_SOURCE_CONFIG["csv_keyword_column"]
        )
        config["csv_comment_column"] = os.getenv(
            "SOURCE_CSV_COMMENT_COLUMN", DEFAULT_SOURCE_CONFIG["csv_comment_column"]
        )
    elif source_type == "postgresql":
        config["postgresql_table"] = os.getenv(
            "SOURCE_POSTGRESQL_TABLE", DEFAULT_SOURCE_CONFIG["postgresql_table"]
        )
        config["postgresql_keyword_column"] = os.getenv(
            "SOURCE_POSTGRESQL_KEYWORD_COLUMN", DEFAULT_SOURCE_CONFIG["postgresql_keyword_column"]
        )
        config["postgresql_comment_column"] = os.getenv(
            "SOURCE_POSTGRESQL_COMMENT_COLUMN", DEFAULT_SOURCE_CONFIG["postgresql_comment_column"]
        )
        config["source_db_config"] = {
            "host": os.getenv("SOURCE_DB_HOST", os.getenv("DB_HOST", "localhost")),
            "port": os.getenv("SOURCE_DB_PORT", os.getenv("DB_PORT", "5432")),
            "dbname": os.getenv("SOURCE_DB_NAME", os.getenv("DB_NAME", "postgres")),
            "user": os.getenv("SOURCE_DB_USER", os.getenv("DB_USER", "postgres")),
            "password": os.getenv("SOURCE_DB_PASSWORD", os.getenv("DB_PASSWORD", "")),
        }
    else:
        logger.warning("Unknown SOURCE_TYPE=%s, defaulting to CSV source.", source_type)
        config["type"] = "csv"

    return config


def get_db_connection(db_config: Dict[str, str]) -> Any:
    """Create a new PostgreSQL database connection."""
    if psycopg2 is None:
        raise ImportError(
            "psycopg2 is required for PostgreSQL access. Install it with `pip install psycopg2-binary`."
        )

    return psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        dbname=db_config["dbname"],
        user=db_config["user"],
        password=db_config["password"],
    )


def generate_batch_id(keyword: str) -> str:
    """Generate a stable batch identifier for ingestion."""
    normalized = keyword.strip().lower().replace(" ", "_")
    return f"{normalized}-{uuid.uuid4().hex[:8]}"


def load_comments_for_keyword(keyword: str, source_config: Dict[str, Any], limit: Optional[int] = None) -> List[str]:
    """Load comments from the configured source for the requested keyword.

    Args:
        keyword: device keyword to match in the source.
        source_config: source configuration loaded from env or defaults.
        limit: optional maximum number of comments to return.
    """
    if not keyword or not isinstance(keyword, str):
        raise ValueError("`keyword` must be a non-empty string.")

    keyword = keyword.strip()
    if not keyword:
        raise ValueError("`keyword` must not be empty after trimming whitespace.")

    source_type = source_config.get("type", "csv").lower()
    logger.info("Loading comments for keyword=%s from source=%s", keyword, source_type)

    if source_type == "csv":
        csv_path = source_config.get("csv_path")
        csv_keyword_column = source_config.get("csv_keyword_column")
        csv_comment_column = source_config.get("csv_comment_column")

        if not csv_path or not csv_keyword_column or not csv_comment_column:
            raise ValueError("CSV source configuration is incomplete.")

        comments: List[str] = []
        with open(csv_path, newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                raw_keyword = str(row.get(csv_keyword_column, "")).strip()
                if raw_keyword.lower() != keyword.lower():
                    continue
                comment = row.get(csv_comment_column)
                if comment:
                    comments.append(str(comment).strip())
                    if limit is not None and len(comments) >= limit:
                        break
        return comments

    if source_type == "postgresql":
        if psycopg2 is None:
            raise ImportError("psycopg2 is required for PostgreSQL source access.")

        sql_table = source_config.get("postgresql_table")
        sql_keyword_column = source_config.get("postgresql_keyword_column")
        sql_comment_column = source_config.get("postgresql_comment_column")
        source_db_config = source_config.get("source_db_config") or get_db_config_from_env()

        if not sql_table or not sql_keyword_column or not sql_comment_column:
            raise ValueError("PostgreSQL source configuration is incomplete.")

        query = f"SELECT {sql_comment_column} FROM {sql_table} WHERE {sql_keyword_column} ILIKE %s"
        if limit is not None:
            query = query + " LIMIT %s"
        comments = []
        with get_db_connection(source_db_config) as conn:
            with conn.cursor() as cursor:
                if limit is not None:
                    cursor.execute(query, (keyword, limit))
                else:
                    cursor.execute(query, (keyword,))
                for row in cursor.fetchall():
                    comment_value = row[0]
                    if comment_value is not None:
                        comments.append(str(comment_value).strip())
        return comments

    raise ValueError(f"Unsupported source type: {source_type}")


def insert_raw_posts(batch_id: str, keyword: str, comments: List[str], db_config: Dict[str, str]) -> int:
    """Insert a batch of raw comments into the raw_posts table."""
    if not comments:
        return 0

    columns = list(RAW_POSTS_COLUMN_MAPPING.values())
    rows = []
    created_at = datetime.now(timezone.utc)
    for comment in comments:
        row = [batch_id, keyword, comment, created_at]
        rows.append(row)

    placeholders = ", ".join(columns)
    insert_query = f"INSERT INTO {RAW_POSTS_TABLE} ({placeholders}) VALUES %s"
    logger.debug("Insert query: %s", insert_query)

    with get_db_connection(db_config) as conn:
        try:
            with conn.cursor() as cursor:
                execute_values(cursor, insert_query, rows)
            conn.commit()
            logger.info("Inserted %d rows into %s", len(rows), RAW_POSTS_TABLE)
            return len(rows)
        except Exception:
            conn.rollback()
            logger.exception("Failed to insert raw posts, transaction rolled back.")
            raise


def run_ingestion(keyword: str) -> Dict[str, Any]:
    """Execute the ingestion workflow end-to-end and return a response payload."""
    response = {
        "status": "error",
        "batch_id": "",
        "keyword": keyword,
        "records_inserted": 0,
        "message": "",
    }

    try:
        if not keyword or not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("`keyword` must be a non-empty string.")

        source_config = get_source_config_from_env()
        comments = load_comments_for_keyword(keyword, source_config)

        if not comments:
            response["message"] = f"No comments found for keyword '{keyword}'."
            logger.warning(response["message"])
            return response

        batch_id = generate_batch_id(keyword)
        db_config = get_db_config_from_env()
        inserted = insert_raw_posts(batch_id, keyword, comments, db_config)

        response.update(
            {
                "status": "success",
                "batch_id": batch_id,
                "records_inserted": inserted,
                "message": f"Inserted {inserted} comment(s) for keyword '{keyword}'.",
            }
        )
        return response

    except Exception as exc:
        logger.exception("Ingestion failed for keyword=%s", keyword)
        response["message"] = str(exc)
        return response


if __name__ == "__main__":
    # Sample local test run using the CSV source and the first 50 comments for a device.
    test_keyword = os.getenv("INGEST_KEYWORD", "Samsung S26")
    comment_limit = 50

    print("Using DB config:", get_db_config_from_env())
    source_config = get_source_config_from_env()
    print("Using source config:", source_config)

    comments = load_comments_for_keyword(test_keyword, source_config, limit=comment_limit)
    if not comments:
        print(f"No comments found for keyword '{test_keyword}'.")
    else:
        batch_id = generate_batch_id(test_keyword)
        inserted = insert_raw_posts(batch_id, test_keyword, comments, get_db_config_from_env())
        print(
            {
                "status": "success",
                "batch_id": batch_id,
                "keyword": test_keyword,
                "records_inserted": inserted,
                "message": f"Inserted {inserted} comments for keyword '{test_keyword}'.",
            }
        )


# Sample .env variables:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=my_database
# DB_USER=db_user
# DB_PASSWORD=secret_password
# SOURCE_TYPE=csv
# SOURCE_CSV_PATH=device_comments.csv
# SOURCE_CSV_KEYWORD_COLUMN=device
# SOURCE_CSV_COMMENT_COLUMN=comment
#
# To use a PostgreSQL source table instead:
# SOURCE_TYPE=postgresql
# SOURCE_POSTGRESQL_TABLE=device_comments
# SOURCE_POSTGRESQL_KEYWORD_COLUMN=device
# SOURCE_POSTGRESQL_COMMENT_COLUMN=comment
# SOURCE_DB_HOST=localhost
# SOURCE_DB_PORT=5432
# SOURCE_DB_NAME=source_database
# SOURCE_DB_USER=source_user
# SOURCE_DB_PASSWORD=source_secret
#
# FastAPI wrapping example:
# from fastapi import FastAPI
# from ingestion_service import run_ingestion
#
# app = FastAPI()
#
# @app.post("/fetch")
# async def fetch_keyword(payload: dict):
#     keyword = payload.get("keyword")
#     return run_ingestion(keyword)
