"""
Security utilities and authentication dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from src.core.database import get_db_session
from src.services.authentication import AuthenticationService
from src.schemas.auth import UserTokenInfo


security = HTTPBearer(auto_error=False)


class CurrentUser:
    """Current user information from JWT token"""
    
    def __init__(self, token_info: UserTokenInfo, session_id: Optional[str] = None):
        self.user_id = token_info.user_id
        self.email = token_info.email
        self.tenant_id = token_info.tenant_id
        self.tenant_code = token_info.tenant_code
        self.is_service_account = token_info.is_service_account
        self.scopes = token_info.scopes
        self.session_id = session_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> CurrentUser:
    """
    Get current authenticated user from JWT token
    
    Raises HTTPException if token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_token",
                "error_description": "Access token required"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = AuthenticationService(db)
    validation = await auth_service.validate_token(credentials.credentials)
    
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "error_description": "Token is invalid or expired"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create user token info
    from src.utils.jwt import jwt_manager
    try:
        claims = jwt_manager.validate_access_token(credentials.credentials)
        token_info = UserTokenInfo(
            user_id=validation.user_id,
            email=claims.get("email", ""),
            tenant_id=validation.tenant_id,
            tenant_code=claims.get("tenant_code", ""),
            is_service_account=validation.is_service_account,
            scopes=validation.scopes or []
        )
        return CurrentUser(token_info, session_id=claims.get("session_id"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "error_description": "Token is malformed"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[CurrentUser]:
    """
    Get current authenticated user from JWT token, but don't raise exception if missing
    
    Returns None if no valid token is provided
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_scopes(*required_scopes: str):
    """
    Dependency to require specific scopes
    """
    async def scope_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        user_scopes = set(current_user.scopes)
        missing_scopes = [scope for scope in required_scopes if scope not in user_scopes]
        
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_scope",
                    "error_description": f"Missing required scopes: {', '.join(missing_scopes)}"
                }
            )
        
        return current_user
    
    return scope_checker


def require_service_account():
    """
    Dependency to require service account authentication
    """
    async def service_account_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.is_service_account:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "invalid_client",
                    "error_description": "Service account required"
                }
            )
        
        return current_user
    
    return service_account_checker


def require_tenant(tenant_id: UUID):
    """
    Dependency to require specific tenant context
    """
    async def tenant_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "invalid_tenant",
                    "error_description": "Access denied for this tenant"
                }
            )
        
        return current_user
    
    return tenant_checker