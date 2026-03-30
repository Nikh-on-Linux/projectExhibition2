import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from sqlalchemy import Column, String, Boolean, Float, select, insert, func, and_, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column
from sqlalchemy.types import UUID as SQLALCHEMY_UUID

from config import DATABASE_URL

# Database engine setup
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args={"server_settings": {"jit": "off"}},
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


# ORM Models
class CleanedPost(Base):
    __tablename__ = "cleaned_posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    raw_post_id: Mapped[int]
    cleaned_text: Mapped[str]
    language: Mapped[str]
    emoji_converted: Mapped[bool]
    batch_id: Mapped[str]  # Batch ID to group posts from same search
    processed_at: Mapped[datetime]


class EnrichedPost(Base):
    __tablename__ = "enriched_posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    cleaned_post_id: Mapped[int]
    emotion_label: Mapped[str]
    confidence: Mapped[float]
    emotion_intensity: Mapped[float]
    emotion_distribution_data: Mapped[dict] = mapped_column(JSON)  # JSON store for all 7 emotions
    batch_id: Mapped[str]  # Same batch_id for retrieval by frontend
    analyzed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# Session context manager
@asynccontextmanager
async def get_session():
    """Async context manager for database sessions"""
    async with async_session_factory() as session:
        yield session


# Query functions
async def get_unanalyzed_posts_by_batch(session: AsyncSession, batch_id: str) -> list[CleanedPost]:
    """
    Fetch cleaned posts for a specific batch that haven't been analyzed yet.
    
    Filters:
    - Only posts from the specific batch_id
    - Only English posts (language = 'en')
    - Not yet in enriched_posts table
    """
    query = select(CleanedPost).where(
        and_(
            CleanedPost.batch_id == batch_id,
            CleanedPost.language == "en",
            ~select(EnrichedPost.cleaned_post_id)
            .where(EnrichedPost.cleaned_post_id == CleanedPost.id)
            .correlate(CleanedPost)
            .exists()
        )
    )
    
    result = await session.execute(query)
    return result.scalars().all()


async def get_enriched_posts_by_batch(session: AsyncSession, batch_id: str) -> list[EnrichedPost]:
    """
    Fetch all enriched posts (emotion analysis results) for a specific batch.
    Used by frontend to retrieve results for displaying.
    """
    query = select(EnrichedPost).where(
        EnrichedPost.batch_id == batch_id
    ).order_by(EnrichedPost.analyzed_at.desc())
    
    result = await session.execute(query)
    return result.scalars().all()


async def insert_enriched_posts(session: AsyncSession, records: list[dict]) -> int:
    """
    Bulk insert emotion analysis results into enriched_posts.
    
    Args:
        session: AsyncSession instance
        records: List of dicts with emotion analysis results
        
    Returns:
        Number of rows inserted
    """
    if not records:
        return 0
    
    # Simple bulk insert - each cleaned_post should only be analyzed once
    stmt = insert(EnrichedPost).values(records)
    
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount


async def count_batch_stats(session: AsyncSession, batch_id: str) -> dict:
    """
    Get analysis statistics for a specific batch.
    
    Returns:
        {
            "batch_id": str,
            "total_posts": Total posts in batch,
            "analyzed": Number of analyzed posts,
            "pending": Number of posts still pending analysis
        }
    """
    # Count total posts in batch
    total_query = select(func.count(CleanedPost.id)).where(
        CleanedPost.batch_id == batch_id
    )
    total_result = await session.execute(total_query)
    total_posts = total_result.scalar() or 0
    
    # Count analyzed posts in batch
    analyzed_query = select(func.count(EnrichedPost.id)).where(
        EnrichedPost.batch_id == batch_id
    )
    analyzed_result = await session.execute(analyzed_query)
    analyzed = analyzed_result.scalar() or 0
    
    pending = total_posts - analyzed
    
    return {
        "batch_id": batch_id,
        "total_posts": total_posts,
        "analyzed": analyzed,
        "pending": pending,
    }


# FastAPI dependency
async def get_db() -> AsyncSession:
    """Dependency for FastAPI to get DB session"""
    async with async_session_factory() as session:
        yield session
