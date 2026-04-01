from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# Response schemas
class CleanedPostOut(BaseModel):
    """Single cleaned post in the batch response."""
    post_id: int = Field(..., description="Original raw_post_id")
    batch_id: str = Field(..., description="Batch ID")
    cleaned_text: Optional[str] = Field(None, description="Cleaned text or null if too_short/gibberish")
    language: str = Field(..., description="Detected language (ISO 639-1)")
    emoji_converted: bool = Field(..., description="Whether emojis were found and converted")
    status: str = Field(..., description="ok, too_short, non_latin_script, or gibberish")
    flags: list[str] = Field(default_factory=list, description="Cleaning flags applied")


class CleanBatchResponse(BaseModel):
    """Response from POST /api/clean/{batch_id}"""
    status: str = Field(..., description="'success' or 'no_data'")
    batch_id: str
    total_processed: int = Field(..., description="Number of posts cleaned")
    results: list[CleanedPostOut]
    signal: str = Field(..., description="Status signal: BATCH_CLEAN_OK")


class BatchCleanStatsResponse(BaseModel):
    """Response from GET /api/clean/stats/{batch_id}"""
    batch_id: str = Field(..., description="Batch ID from ingestion")
    total_raw: int = Field(..., description="Total raw posts in batch")
    cleaned: int = Field(..., description="Posts successfully cleaned")
    pending: int = Field(..., description="Posts still pending cleaning")


class HealthResponse(BaseModel):
    """Response from GET /health"""
    status: str = Field(..., description="Service status: ok, degraded, or error")
    service: str = Field(..., description="Service name")
    port: int = Field(..., description="Service port")
    timestamp: str = Field(..., description="ISO 8601 timestamp for monitoring freshness")
