import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from db import (
    get_db,
    get_raw_posts_by_batch,
    get_uncleaned_posts_by_batch,
    insert_cleaned_posts,
    count_cleaning_stats,
)
from cleaner import clean_text
from schemas import CleanBatchResponse, CleanedPostOut, BatchCleanStatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clean", tags=["cleaning"])


@router.post("/{batch_id}", response_model=CleanBatchResponse)
async def clean_batch(
    batch_id: str = Path(..., description="Batch ID from ingestion service"),
    session: AsyncSession = Depends(get_db),
):
    """
    Clean all raw posts for a specific batch_id.

    Flow:
    1. Fetch all raw posts matching the batch_id from raw_posts table
    2. Apply text cleaning rules to each post
    3. Insert cleaned results into cleaned_posts table
    4. Return JSON array of cleaned posts + BATCH_CLEAN_OK signal
    """
    try:
        # Fetch raw posts for this batch
        raw_posts = await get_raw_posts_by_batch(session, batch_id)

        if not raw_posts:
            logger.warning(f"No raw posts found for batch_id={batch_id}")
            raise HTTPException(
                status_code=404,
                detail="No raw posts found for this batch",
            )

        logger.info(f"Fetched {len(raw_posts)} raw posts for batch_id={batch_id}")

        # Clean each post
        cleaned_results = []
        db_records = []

        for raw_post in raw_posts:
            result = clean_text(raw_post.raw_text)

            # Build the response item
            cleaned_item = CleanedPostOut(
                post_id=raw_post.id,
                batch_id=batch_id,
                cleaned_text=result["cleaned_text"],
                language=result["language"],
                emoji_converted=result["emoji_converted"],
                status=result["status"],
                flags=result["flags"],
            )
            cleaned_results.append(cleaned_item)

            # Build the DB record for insertion
            # Only insert posts with actual cleaned text
            db_record = {
                "raw_post_id": raw_post.id,
                "batch_id": batch_id,
                "cleaned_text": result["cleaned_text"] if result["cleaned_text"] else "",
                "language": result["language"],
                "emoji_converted": result["emoji_converted"],
                "processed_at": datetime.utcnow(),
            }
            db_records.append(db_record)

        # Insert all cleaned posts
        # Note: Transaction is already managed by FastAPI dependency session
        inserted = await insert_cleaned_posts(session, db_records)
        await session.commit()
        logger.info(
            f"Cleaned batch_id={batch_id}: {inserted} posts inserted into cleaned_posts"
        )

        return CleanBatchResponse(
            status="success",
            batch_id=batch_id,
            total_processed=len(cleaned_results),
            results=cleaned_results,
            signal=f"BATCH_CLEAN_OK",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error cleaning batch_id={batch_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to process batch. Please contact support.",
        )


@router.get("/stats/{batch_id}", response_model=BatchCleanStatsResponse)
async def get_cleaning_stats(
    batch_id: str = Path(..., description="Batch ID to check cleaning progress"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get cleaning progress for a specific batch.

    Returns:
    - total_raw: Total raw posts in this batch
    - cleaned: Number of posts already cleaned
    - pending: Number still waiting for cleaning
    """
    try:
        stats = await count_cleaning_stats(session, batch_id)

        if stats["total_raw"] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No posts found for batch_id={batch_id}",
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting stats for batch_id={batch_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cleaning stats: {str(e)}",
        )
