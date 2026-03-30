import logging

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from config import PORT, MODEL_NAME
from db import get_db, get_enriched_posts_by_batch
from schemas import HealthResponse, BatchResultsResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["status"])


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """
    Health check endpoint - no database required.
    """
    return {
        "status": "ok",
        "service": "model",
        "port": PORT,
    }


@router.get("/results/{batch_id}", response_model=BatchResultsResponse)
async def get_batch_results(
    batch_id: str = Path(..., description="Batch ID to retrieve results for"),
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve emotion analysis results for a specific batch.
    
    This endpoint is called by the frontend to get the enriched data
    after the analysis is complete.
    
    Returns:
    - batch_id: The batch ID
    - total_results: Number of results for this batch
    - results: List of enriched posts with emotion analysis
    """
    try:
        enriched_posts = await get_enriched_posts_by_batch(session, batch_id)
        
        if not enriched_posts:
            logger.warning(f"No results found for batch_id={batch_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No emotion analysis results found for batch_id={batch_id}"
            )
        
        logger.info(f"Retrieved {len(enriched_posts)} results for batch_id={batch_id}")
        
        return {
            "batch_id": batch_id,
            "total_results": len(enriched_posts),
            "results": enriched_posts,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving results for batch_id={batch_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve results: {str(e)}"
        )