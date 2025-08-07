"""
Test FastAPI application configuration that bypasses database connections
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from unittest.mock import patch, MagicMock

from src.config import settings
from src.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    sentinel_exception_handler,
    general_exception_handler
)
from src.utils.exceptions import SentinelException
from src.api.v1 import api_router

# Create test app without database dependencies
test_app = FastAPI(
    title=f"{settings.APP_NAME} - Test",
    version=settings.VERSION,
    debug=True,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

if settings.CORS_ENABLED:
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

test_app.add_exception_handler(StarletteHTTPException, http_exception_handler)
test_app.add_exception_handler(RequestValidationError, validation_exception_handler)
test_app.add_exception_handler(SentinelException, sentinel_exception_handler)
test_app.add_exception_handler(Exception, general_exception_handler)

# Include all API routes
test_app.include_router(api_router)

@test_app.on_event("startup")
async def test_startup_event():
    """Test startup - no database connection required"""
    logging.info("Starting test application - database mocked")

@test_app.on_event("shutdown") 
async def test_shutdown_event():
    """Test shutdown"""
    logging.info("Shutting down test application")

@test_app.get("/")
async def root():
    return {
        "name": f"{settings.APP_NAME} - Test",
        "version": settings.VERSION,
        "status": "operational"
    }

@test_app.get("/health")
async def health_check():
    """Mock health check for testing"""
    return {
        "status": "healthy",
        "checks": {
            "database": "ok",  # Mocked as ok
            "cache": "ok",
        },
        "version": settings.VERSION
    }