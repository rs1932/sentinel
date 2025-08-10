"""
Sentinel API router module.

This module creates the main API router for Sentinel RBAC functionality.
The router is designed to be easily extractable for microservices architecture.
"""
from fastapi import APIRouter

# Import all route modules
from ..routes import (
    auth,
    users,
    tenants,
    roles,
    permissions,
    resources,
    groups,
    terminology,
    navigation,
    field_definitions,
    service_accounts,
    password_reset,
    avatars
)

# Create the main Sentinel API router
api_router = APIRouter()

# Health check endpoint
@api_router.get("/health")
async def sentinel_health():
    """Sentinel service health check."""
    return {"service": "sentinel", "status": "ok"}

# Include all route modules with appropriate prefixes and tags
# Authentication routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# User management routes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["User Management"]
)

# Tenant management routes
api_router.include_router(
    tenants.router,
    prefix="/tenants",
    tags=["Tenant Management"]
)

# Role management routes
api_router.include_router(
    roles.router,
    prefix="/roles",
    tags=["Role Management"]
)

# Permission management routes
api_router.include_router(
    permissions.router,
    prefix="/permissions",
    tags=["Permission Management"]
)

# Resource management routes
api_router.include_router(
    resources.router,
    prefix="/resources",
    tags=["Resource Management"]
)

# Group management routes
api_router.include_router(
    groups.router,
    prefix="/groups",
    tags=["Group Management"]
)

# Terminology routes
api_router.include_router(
    terminology.router,
    prefix="/terminology",
    tags=["Terminology Management"]
)

# Navigation/Menu routes
api_router.include_router(
    navigation.router,
    prefix="/navigation",
    tags=["Navigation Management"]
)

# Field definitions routes (Module 8)
api_router.include_router(
    field_definitions.router,
    prefix="/field-definitions",
    tags=["Field Definitions"]
)

# Service account routes
api_router.include_router(
    service_accounts.router,
    prefix="/service-accounts",
    tags=["Service Accounts"]
)

# Password reset routes
api_router.include_router(
    password_reset.router,
    prefix="/password-reset",
    tags=["Password Reset"]
)

# Avatar management routes
api_router.include_router(
    avatars.router,
    prefix="/avatars",
    tags=["Avatar Management"]
)