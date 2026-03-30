import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# Request schemas
class AnalyzeByBatchRequest(BaseModel):
    """Request body for POST /analyze/{batch_id}"""
    batch_id: str = Field(..., description="Batch ID from search/ingestion service")


class RetrieveResultsRequest(BaseModel):
    """Request body for GET /results/{batch_id}"""
    batch_id: str = Field(..., description="Batch ID to retrieve results for")


# Response schemas
class AnalyzeResponse(BaseModel):
    """Response from POST /analyze/{batch_id}"""
    status: str = Field(..., description="'success', 'queued', or 'no_data'")
    processed: int = Field(..., description="Number of posts analyzed")
    batch_id: str = Field(..., description="Batch ID being processed")
    message: Optional[str] = Field(None, description="Additional context message")


class BatchStatsResponse(BaseModel):
    """Response from GET /batch/{batch_id}"""
    batch_id: str
    total_posts: int
    analyzed: int
    pending: int


class HealthResponse(BaseModel):
    """Response from GET /health"""
    status: str
    service: str
    port: int


class EmotionDistribution(BaseModel):
    """All emotion confidence scores (7 emotions)"""
    joy: float
    anger: float
    fear: float
    disgust: float
    sadness: float
    surprise: float
    neutral: float


class EnrichedPostResponse(BaseModel):
    """Enriched post with emotion analysis - single result"""
    id: int
    cleaned_post_id: int
    emotion_label: str
    confidence: float
    emotion_intensity: float
    emotion_distribution_data: dict  # JSON with all 7 emotion scores
    batch_id: str
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchResultsResponse(BaseModel):
    """Response from GET /results/{batch_id} - all results for a batch"""
    batch_id: str
    total_results: int
    results: List[EnrichedPostResponse]
