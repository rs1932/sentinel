from fastapi import APIRouter
from src.api.v1.tenants import router as tenants_router
from src.api.v1.auth import router as auth_router
from src.api.v1.users import router as users_router
from src.api.v1.service_accounts import router as service_accounts_router
from src.api.v1.password_reset import router as password_reset_router
from src.api.v1.avatars import router as avatars_router
from src.api.v1.roles import router as roles_router
from src.api.v1.groups import router as groups_router

api_router = APIRouter(prefix="/api/v1")

# Include routers
api_router.include_router(auth_router)
api_router.include_router(password_reset_router)
api_router.include_router(avatars_router)
api_router.include_router(tenants_router)
api_router.include_router(users_router)
api_router.include_router(service_accounts_router)
api_router.include_router(roles_router)
api_router.include_router(groups_router)

__all__ = ["api_router"]