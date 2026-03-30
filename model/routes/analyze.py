import logging
import json
from datetime import datetime

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from config import BATCH_SIZE
from db import (
    get_db,
    get_unanalyzed_posts_by_batch,
    get_enriched_posts_by_batch,
    insert_enriched_posts,
    count_batch_stats,
)
from inference import run_inference
from schemas import AnalyzeResponse, BatchStatsResponse, BatchResultsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


async def _process_batch_background(batch_id: str, session: AsyncSession):
    """Background task: fetch posts from batch, run inference, insert results"""
    try:
        logger.info(f"Starting background analysis for batch_id={batch_id}")
        
        # Fetch unanalyzed posts from this batch
        posts = await get_unanalyzed_posts_by_batch(session, batch_id)
        
        if not posts:
            logger.info(f"No unanalyzed posts found for batch_id={batch_id}")
            return
        
        logger.info(f"Fetched {len(posts)} unanalyzed posts for batch_id={batch_id}")
        
        # Extract cleaned texts
        texts = [post.cleaned_text for post in posts]
        post_ids = [post.id for post in posts]
        
        # Run inference
        emotions = run_inference(texts, BATCH_SIZE)
        
        # Build enriched post records with batch_id and emotion_distribution_data
        records = []
        for post_id, emotion in zip(post_ids, emotions):
            record = {
                "cleaned_post_id": post_id,
                "emotion_label": emotion["emotion_label"],
                "confidence": emotion["confidence"],
                "emotion_intensity": emotion["confidence"],  # Main confidence as intensity
                "emotion_distribution_data": {
                    "joy": emotion["joy"],
                    "anger": emotion["anger"],
                    "fear": emotion["fear"],
                    "disgust": emotion["disgust"],
                    "sadness": emotion["sadness"],
                    "surprise": emotion["surprise"],
                    "neutral": emotion["neutral"],
                },
                "batch_id": batch_id,
                "analyzed_at": datetime.utcnow(),
            }
            records.append(record)
        
        # Insert into DB
        inserted = await insert_enriched_posts(session, records)
        logger.info(f"Background analysis for batch_id={batch_id} completed: {inserted} posts inserted")
        
    except Exception as e:
        logger.error(f"Background analysis for batch_id={batch_id} failed: {e}", exc_info=True)


@router.post("/analyze/{batch_id}", response_model=AnalyzeResponse)
async def analyze_batch(
    batch_id: str = Path(..., description="Batch ID from search/ingestion service"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    session: AsyncSession = Depends(get_db),
):
    """
    Analyze posts from a specific batch and insert emotion analysis results.
    
    Flow:
    1. Receive batch_id from cleaning service
    2. Fetch unanalyzed posts from cleaned_posts table with this batch_id
    3. Run emotion inference on cleaned text
    4. Store results in enriched_posts table with same batch_id
    5. Frontend uses batch_id to retrieve results
    
    Queues as background task to avoid timeout on large batches.
    """
    try:
        # Check how many posts are in this batch
        stats = await count_batch_stats(session, batch_id)
        
        if stats["total_posts"] == 0:
            logger.warning(f"No posts found for batch_id={batch_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No posts found for batch_id={batch_id}"
            )
        
        logger.info(f"Processing batch_id={batch_id} with {stats['total_posts']} total posts")
        
        # Always use background task for consistency and to avoid timeouts
        background_tasks.add_task(_process_batch_background, batch_id, session)
        
        return AnalyzeResponse(
            status="queued",
            processed=0,
            batch_id=batch_id,
            message=f"Analysis queued for batch_id={batch_id}, total posts: {stats['total_posts']}",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queuing analysis for batch_id={batch_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue analysis: {str(e)}"
        )


@router.get("/batch/{batch_id}", response_model=BatchStatsResponse)
async def get_batch_stats(
    batch_id: str = Path(..., description="Batch ID to check status"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get analysis progress for a specific batch.
    
    Returns:
    - total_posts: Total posts in this batch
    - analyzed: Number of posts with emotion analysis
    - pending: Number of posts still waiting for analysis
    """
    try:
        stats = await count_batch_stats(session, batch_id)
        
        if stats["total_posts"] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No posts found for batch_id={batch_id}"
            )
        
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for batch_id={batch_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch stats: {str(e)}"
        )