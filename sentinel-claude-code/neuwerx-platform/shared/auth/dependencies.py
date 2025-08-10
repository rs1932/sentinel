"""
Shared authentication dependencies and utilities.
These can be used by both Sentinel and Metamorphic endpoints.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import jwt
import structlog

from ..database import get_database_session

logger = structlog.get_logger(__name__)
security = HTTPBearer()

class AuthenticationError(Exception):
    """Custom authentication exception."""
    pass

class AuthService:
    """
    Centralized authentication service.
    This interface stays consistent whether services are unified or separate.
    """
    
    def __init__(self, jwt_secret: str, jwt_algorithm: str = "HS256"):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token.
        In separate services, this could become an HTTP API call.
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    async def get_current_user(self, token: str, db_session: Session) -> Dict[str, Any]:
        """
        Get current user from token.
        This method signature makes it easy to replace with HTTP calls later.
        """
        try:
            payload = self.decode_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            
            # In a separate service architecture, this would be an HTTP call
            # to the Sentinel user service
            return await self._get_user_by_id(user_id, db_session)
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Authentication error", error=str(e))
            raise AuthenticationError("Authentication failed")
    
    async def _get_user_by_id(self, user_id: str, db_session: Session) -> Dict[str, Any]:
        """
        Internal method to get user by ID.
        In separate services, this becomes a call to Sentinel API.
        """
        # Import here to avoid circular imports
        # This makes it easier to separate services later
        try:
            from ...api.src.v1.sentinel.services import UserService
            user_service = UserService(db_session)
            user = await user_service.get_by_id(user_id)
            if not user:
                raise AuthenticationError("User not found")
            return user
        except ImportError:
            # Fallback for when services are separated
            raise AuthenticationError("User service not available")

# Global auth service instance
auth_service: Optional[AuthService] = None

def get_auth_service() -> AuthService:
    """Get the global authentication service."""
    if not auth_service:
        raise RuntimeError("Authentication service not initialized")
    return auth_service

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """
    FastAPI dependency for getting the current authenticated user.
    This dependency can be used by both Sentinel and Metamorphic endpoints.
    """
    try:
        auth = get_auth_service()
        user = await auth.get_current_user(credentials.credentials, db)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user if they are active."""
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

class RequirePermission:
    """
    Permission dependency factory.
    Usage: @app.get("/", dependencies=[Depends(RequirePermission("read_users"))])
    """
    
    def __init__(self, permission: str):
        self.permission = permission
    
    async def __call__(
        self,
        current_user: Dict[str, Any] = Depends(get_current_active_user),
        db: Session = Depends(get_database_session)
    ):
        """Check if user has required permission."""
        try:
            # In separate services, this would be an HTTP call to Sentinel
            from ...api.src.v1.sentinel.services import PermissionService
            permission_service = PermissionService(db)
            
            has_permission = await permission_service.user_has_permission(
                current_user["id"], self.permission
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{self.permission}' required"
                )
            
            return current_user
            
        except ImportError:
            # Fallback for separated services
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Permission service not available"
            )