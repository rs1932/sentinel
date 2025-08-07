"""
Async database utilities and session management for FastAPI
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text, event
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from src.config import settings


logger = logging.getLogger(__name__)

# Create async engine
if settings.DEBUG:
    async_engine = create_async_engine(
        settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
        echo=settings.DEBUG,
        pool_pre_ping=True,
        connect_args={
            "server_settings": {
                "search_path": f"{settings.DATABASE_SCHEMA},public"
            }
        }
    )
else:
    async_engine = create_async_engine(
        settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        connect_args={
            "server_settings": {
                "search_path": f"{settings.DATABASE_SCHEMA},public"
            }
        }
    )

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session for FastAPI endpoints
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """
    Context manager for async database operations
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_async_db():
    """
    Initialize async database and create schema
    """
    async with async_engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.DATABASE_SCHEMA}"))
        
        # Import all models to ensure they're registered
        from src.models import Tenant, User, RefreshToken, TokenBlacklist
        
        # Create tables (only works with async_engine.begin())
        from src.models.base import BaseModel
        await conn.run_sync(BaseModel.metadata.create_all)
    
    logger.info(f"Async database initialized with schema: {settings.DATABASE_SCHEMA}")


async def check_async_database_connection():
    """
    Check async database connection health
    """
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
        logger.info("Async database connection successful")
        return True
    except Exception as e:
        logger.error(f"Async database connection failed: {str(e)}")
        return False