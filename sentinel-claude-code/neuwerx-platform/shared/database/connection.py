"""
Shared database connection management for the neuwerx-platform.
This module provides database connectivity that can be used by both Sentinel and Metamorphic systems.
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
import logging
import structlog

logger = structlog.get_logger(__name__)

class DatabaseManager:
    """
    Centralized database management for the platform.
    Designed to be easily separable for microservices architecture.
    """
    
    def __init__(self, database_url: str, schema: str = None):
        self.database_url = database_url
        self.schema = schema
        self.engine = None
        self.SessionLocal = None
        self._base = declarative_base()
    
    def initialize(self):
        """Initialize database connection and session factory."""
        self.engine = create_engine(
            self.database_url,
            poolclass=NullPool,  # Disable connection pooling for development
            echo=False
        )
        
        # Set search path for PostgreSQL schema
        if self.schema:
            @event.listens_for(self.engine, "connect", insert=True)
            def set_search_path(dbapi_connection, connection_record):
                with dbapi_connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {self.schema}")
        
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine
        )
        
        logger.info("Database connection initialized", 
                   url=self.database_url.split("@")[1] if "@" in self.database_url else "unknown",
                   schema=self.schema)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with proper cleanup.
        This pattern makes it easy to separate services later.
        """
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            session.close()
    
    async def check_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error("Database connection check failed", error=str(e))
            return False
    
    @property
    def Base(self):
        """Base class for SQLAlchemy models."""
        return self._base

# Global database manager instance
# This will be initialized by the main application
db_manager: DatabaseManager = None

def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting database sessions.
    This function signature stays the same whether unified or separate services.
    """
    if not db_manager:
        raise RuntimeError("Database manager not initialized")
    
    with db_manager.get_session() as session:
        yield session