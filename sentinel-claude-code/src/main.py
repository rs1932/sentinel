from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import structlog

from src.config import settings
from src.database import init_db, check_database_connection
from src.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    sentinel_exception_handler,
    general_exception_handler
)
from src.utils.exceptions import SentinelException
from src.api.v1 import api_router
from src.middleware.auth import AuthenticationMiddleware, TenantContextMiddleware, SecurityHeadersMiddleware

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = structlog.get_logger()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)

if settings.CORS_ENABLED:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

# Add authentication and security middleware
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SentinelException, sentinel_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include all API routes
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Sentinel Access Platform", version=settings.VERSION)
    
    if not check_database_connection():
        logger.error("Failed to connect to database")
        raise Exception("Database connection failed")
    
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Sentinel Access Platform")

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    db_status = check_database_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "checks": {
            "database": "ok" if db_status else "failed",
            "cache": "ok",
        },
        "version": settings.VERSION
    }