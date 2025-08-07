from sqlalchemy import create_engine, MetaData, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from src.config import settings

logger = logging.getLogger(__name__)

metadata = MetaData(schema=settings.DATABASE_SCHEMA)

# Create engine with different configurations for debug vs production
if settings.DEBUG:
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        echo=settings.DEBUG,
        connect_args={
            "options": f"-csearch_path={settings.DATABASE_SCHEMA},public"
        }
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        connect_args={
            "options": f"-csearch_path={settings.DATABASE_SCHEMA},public"
        }
    )

@event.listens_for(engine, "connect")
def set_schema_on_connect(dbapi_conn, connection_record):
    with dbapi_conn.cursor() as cursor:
        cursor.execute(f"SET search_path TO {settings.DATABASE_SCHEMA}, public")

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base(metadata=metadata)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.DATABASE_SCHEMA}"))
        conn.commit()
    
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized with schema: {settings.DATABASE_SCHEMA}")

def check_database_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def get_tenant_filter(tenant_id: str):
    return {"tenant_id": tenant_id}