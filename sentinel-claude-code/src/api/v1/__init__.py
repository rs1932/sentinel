from fastapi import APIRouter
from src.api.v1.tenants import router as tenants_router
from src.api.v1.auth import router as auth_router

api_router = APIRouter(prefix="/api/v1")

# Include routers
api_router.include_router(auth_router)
api_router.include_router(tenants_router)

__all__ = ["api_router"]