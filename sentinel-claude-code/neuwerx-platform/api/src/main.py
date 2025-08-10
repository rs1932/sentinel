"""
Unified Neuwerx Platform API Server
===================================

This main.py creates a unified FastAPI server that serves both Sentinel RBAC 
and Metamorphic field management APIs. The architecture is designed for easy 
separation into microservices later if needed.

Key Design Principles:
1. Domain separation - Sentinel and Metamorphic routes are clearly separated
2. Shared utilities - Common functionality is in the shared/ directory  
3. Clean interfaces - Cross-domain calls use well-defined interfaces
4. Modular configuration - Easy to split configs when separating services
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import structlog
from pathlib import Path
import sys

# Add the platform root to the Python path so we can import shared modules
platform_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(platform_root))

# Add the src directory to path for v1 imports
src_root = Path(__file__).parent
sys.path.insert(0, str(src_root))

# Import shared utilities
from shared.config import get_settings, initialize_settings
from shared.database import DatabaseManager, db_manager
from shared.auth import AuthService, auth_service

# Import domain-specific modules
from v1.sentinel.api import api_router as sentinel_router
# from v1.metamorphic.api import api_router as metamorphic_router  # TODO: Create when implementing Metamorphic

# Initialize configuration
# The .env file should be in the api/ directory or platform root
env_file_path = platform_root / "api" / ".env"
if not env_file_path.exists():
    env_file_path = platform_root / ".env"

settings = initialize_settings(str(env_file_path) if env_file_path.exists() else None)

# Configure structured logging
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

logger = structlog.get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    description="Unified API server for Sentinel RBAC and Metamorphic field management",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    redirect_slashes=False,  # Disable automatic trailing slash redirects
)

# Configure CORS
if settings.CORS_ENABLED:
    app.add_middleware(
        CORSMiddleware,
        **settings.get_cors_config()
    )

# Import and add middleware (keeping domain-specific middleware separate)
from v1.sentinel.middleware.auth import AuthenticationMiddleware, TenantContextMiddleware
from v1.sentinel.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    sentinel_exception_handler,
    general_exception_handler
)
from v1.sentinel.utils.exceptions import SentinelException

# Add Sentinel-specific middleware
# Note: In separate services, each would have its own middleware
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(TenantContextMiddleware)

# Add exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)  
app.add_exception_handler(SentinelException, sentinel_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routers with proper prefixes
# This structure makes it easy to separate services later:
# - Sentinel routes: /api/v1/sentinel/*
# - Metamorphic routes: /api/v1/metamorphic/* (when implemented)
app.include_router(sentinel_router, prefix="/api/v1/sentinel")
# app.include_router(metamorphic_router, prefix="/api/v1/metamorphic")  # TODO: Add when ready

@app.on_event("startup")
async def startup_event():
    """
    Initialize all platform services.
    This startup sequence is designed to be easily adaptable for separate services.
    """
    logger.info("Starting Neuwerx Platform API Server", version=settings.VERSION)
    
    try:
        # Initialize shared database manager
        global db_manager
        db_manager = DatabaseManager(
            database_url=settings.get_database_url("sentinel"),
            schema=settings.DATABASE_SCHEMA
        )
        db_manager.initialize()
        
        # Test database connection
        if not await db_manager.check_connection():
            raise Exception("Database connection failed")
        
        # Initialize shared authentication service
        global auth_service
        auth_service = AuthService(
            jwt_secret=settings.sentinel.JWT_SECRET_KEY,
            jwt_algorithm=settings.sentinel.JWT_ALGORITHM
        )
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize platform services", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup platform resources."""
    logger.info("Shutting down Neuwerx Platform API Server")

@app.get("/")
async def root():
    """
    Platform health and information endpoint.
    This endpoint provides information about all available services.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "services": {
            "sentinel": {
                "status": "available",
                "endpoints": "/api/v1/sentinel/*"
            },
            "metamorphic": {
                "status": "coming_soon",
                "endpoints": "/api/v1/metamorphic/*"
            }
        }
    }

@app.get("/health")
async def health_check():
    """
    Comprehensive health check for all platform services.
    In separate services, this would aggregate health from multiple endpoints.
    """
    try:
        # Check database connectivity
        db_healthy = await db_manager.check_connection() if db_manager else False
        
        # Check other services
        services_status = {
            "database": "ok" if db_healthy else "failed",
            "authentication": "ok" if auth_service else "failed",
            "sentinel": "ok",  # Could check Sentinel-specific health
            "metamorphic": "not_implemented"  # Placeholder for future service
        }
        
        overall_status = "healthy" if all(
            status in ["ok", "not_implemented"] for status in services_status.values()
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "services": services_status
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": settings.VERSION
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )