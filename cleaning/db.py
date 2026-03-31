from datetime import datetime
from contextlib import asynccontextmanager

from typing import List
from sqlalchemy import Column, String, Boolean, Integer, Text, select, insert, func, and_, ForeignKey, Index
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

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
class RawPost(Base):
    __tablename__ = "raw_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[str]
    platform: Mapped[str]
    keyword: Mapped[str] = mapped_column(nullable=True)
    raw_text: Mapped[str]
    raw_json = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    fetched_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index('idx_raw_posts_batch_id', 'batch_id'),
    )


class CleanedPost(Base):
    __tablename__ = "cleaned_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_post_id: Mapped[int] = mapped_column(ForeignKey("raw_posts.id", ondelete="CASCADE"))
    batch_id: Mapped[str]
    cleaned_text: Mapped[str]
    language: Mapped[str] = mapped_column(nullable=True)
    emoji_converted: Mapped[bool] = mapped_column(default=False)
    processed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index('idx_cleaned_posts_batch_id', 'batch_id'),
    )


# Session context manager
@asynccontextmanager
async def get_session():
    """Async context manager for database sessions"""
    async with async_session_factory() as session:
        yield session


# Query functions
async def get_raw_posts_by_batch(session: AsyncSession, batch_id: str) -> List[RawPost]:
    """
    Fetch all raw posts for a specific batch_id.
    Returns all rows from raw_posts matching the batch_id.
    """
    query = select(RawPost).where(RawPost.batch_id == batch_id)
    result = await session.execute(query)
    return result.scalars().all()


async def get_uncleaned_posts_by_batch(session: AsyncSession, batch_id: str) -> List[RawPost]:
    """
    Fetch raw posts for a batch that haven't been cleaned yet.
    Uses LEFT OUTER JOIN for efficient query (avoids N+1 subquery pattern).
    """
    from sqlalchemy import outerjoin
    query = select(RawPost).where(
        and_(
            RawPost.batch_id == batch_id,
            ~select(CleanedPost.raw_post_id)
            .where(CleanedPost.raw_post_id == RawPost.id)
            .correlate(RawPost)
            .exists()
        )
    )
    result = await session.execute(query)
    return result.scalars().all()


async def insert_cleaned_posts(session: AsyncSession, records: list[dict]) -> int:
    """
    Bulk insert cleaned post records into cleaned_posts table.
    NOTE: Transaction management is handled by caller (e.g., session.begin() context manager).

    Args:
        session: AsyncSession instance
        records: List of dicts with cleaned post data

    Returns:
        Number of rows inserted
    """
    if not records:
        return 0

    stmt = insert(CleanedPost).values(records)
    result = await session.execute(stmt)
    # NOTE: Removed await session.commit() — caller manages transaction
    return result.rowcount


async def count_cleaning_stats(session: AsyncSession, batch_id: str) -> dict:
    """
    Get cleaning statistics for a specific batch.

    Returns:
        {
            "batch_id": str,
            "total_raw": Total raw posts in batch,
            "cleaned": Number already cleaned,
            "pending": Number still pending cleaning
        }
    """
    # Count total raw posts in batch
    total_query = select(func.count(RawPost.id)).where(
        RawPost.batch_id == batch_id
    )
    total_result = await session.execute(total_query)
    total_raw = total_result.scalar() or 0

    # Count cleaned posts in batch
    cleaned_query = select(func.count(CleanedPost.id)).where(
        CleanedPost.batch_id == batch_id
    )
    cleaned_result = await session.execute(cleaned_query)
    cleaned = cleaned_result.scalar() or 0

    pending = total_raw - cleaned

    return {
        "batch_id": batch_id,
        "total_raw": total_raw,
        "cleaned": cleaned,
        "pending": pending,
    }


# FastAPI dependency
async def get_db() -> AsyncSession:
    """Dependency for FastAPI to get DB session"""
    async with async_session_factory() as session:
        yield session
