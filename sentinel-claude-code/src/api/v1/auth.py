"""
Authentication API endpoints for user login, token management, and security
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from src.core.database import get_db_session
from src.services.authentication import AuthenticationService
from src.services.token import TokenService
from src.schemas.auth import (
    LoginRequest, ServiceAccountTokenRequest, TokenResponse,
    RefreshTokenRequest, RevokeTokenRequest, LogoutRequest,
    TokenValidationResponse, DeviceInfo, AuthErrorResponse,
    PasswordRequirements, SecurityEventRequest, RefreshTokenInfo
)
from src.core.exceptions import AuthenticationError, ValidationError
from src.core.rate_limiting import rate_limit
from src.core.security_utils import get_current_user, get_current_user_optional


router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


def get_device_info(request: Request) -> DeviceInfo:
    """Extract device information from request"""
    user_agent = request.headers.get("user-agent", "")
    x_forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.client.host
    
    return DeviceInfo(
        ip_address=client_ip,
        user_agent=user_agent,
        platform="web"  # Could be enhanced to detect mobile/api/etc
    )


@router.post("/login", 
             response_model=TokenResponse,
             responses={
                 400: {"model": AuthErrorResponse},
                 401: {"model": AuthErrorResponse},
                 429: {"model": AuthErrorResponse}
             })
@rate_limit(calls=10, period=60)  # 10 login attempts per minute
async def login(
    login_request: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Authenticate user with email/password and return JWT tokens
    
    **Rate Limited**: 10 attempts per minute per IP
    """
    try:
        auth_service = AuthenticationService(db)
        device_info = get_device_info(request)
        
        token_response = await auth_service.authenticate_user(login_request, device_info)
        return token_response
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "authentication_failed",
                "error_description": str(e)
            }
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "error_description": str(e)
            }
        )


@router.post("/token",
             response_model=TokenResponse,
             responses={
                 400: {"model": AuthErrorResponse},
                 401: {"model": AuthErrorResponse}
             })
async def service_account_token(
    token_request: ServiceAccountTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Authenticate service account and return JWT access token
    
    Uses client_credentials grant type for service-to-service authentication
    """
    try:
        auth_service = AuthenticationService(db)
        token_response = await auth_service.authenticate_service_account(token_request)
        return token_response
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_client",
                "error_description": str(e)
            }
        )


@router.post("/refresh",
             response_model=TokenResponse,
             responses={
                 400: {"model": AuthErrorResponse},
                 401: {"model": AuthErrorResponse}
             })
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Refresh access token using refresh token
    """
    try:
        auth_service = AuthenticationService(db)
        device_info = get_device_info(request)
        
        token_response = await auth_service.refresh_token(refresh_request, device_info)
        return token_response
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_grant",
                "error_description": str(e)
            }
        )


@router.post("/revoke",
             responses={
                 200: {"description": "Token revoked successfully"},
                 400: {"model": AuthErrorResponse},
                 401: {"model": AuthErrorResponse}
             })
async def revoke_token(
    revoke_request: RevokeTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Revoke an access or refresh token
    """
    try:
        auth_service = AuthenticationService(db)
        success = await auth_service.revoke_token(revoke_request)
        
        if success:
            return {"message": "Token revoked successfully"}
        else:
            return {"message": "Token not found or already revoked"}
            
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_request",
                "error_description": str(e)
            }
        )


@router.post("/logout",
             responses={
                 200: {"description": "Logout successful"},
                 401: {"model": AuthErrorResponse}
             })
async def logout(
    logout_request: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Logout user and revoke tokens
    
    Requires valid access token in Authorization header
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_token",
                "error_description": "Access token required"
            }
        )
    
    try:
        auth_service = AuthenticationService(db)
        success = await auth_service.logout_user(credentials.credentials, logout_request)
        
        return {"message": "Logout successful"}
        
    except Exception:
        # Always return success for logout to prevent information disclosure
        return {"message": "Logout successful"}


@router.get("/validate",
            response_model=TokenValidationResponse,
            responses={
                401: {"model": AuthErrorResponse}
            })
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Validate access token and return token information
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_token",
                "error_description": "Access token required"
            }
        )
    
    auth_service = AuthenticationService(db)
    validation_response = await auth_service.validate_token(credentials.credentials)
    
    if not validation_response.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "error_description": "Token is invalid or expired"
            }
        )
    
    return validation_response


@router.get("/me/tokens",
            response_model=List[RefreshTokenInfo])
async def get_my_tokens(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get user's active refresh tokens (sessions)
    
    Requires authentication
    """
    token_service = TokenService(db)
    tokens = await token_service.get_user_active_tokens(current_user.user_id)
    return tokens


@router.delete("/me/tokens/{token_id}")
async def revoke_my_token(
    token_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Revoke a specific refresh token (logout from device)
    
    Requires authentication
    """
    token_service = TokenService(db)
    revoked_count = await token_service.revoke_user_tokens(
        user_id=current_user.user_id,
        token_id=token_id
    )
    
    if revoked_count > 0:
        return {"message": "Token revoked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )


@router.delete("/me/tokens")
async def revoke_all_my_tokens(
    keep_current: bool = True,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Revoke all user's refresh tokens (logout from all devices)
    
    **Parameters:**
    - keep_current: Whether to keep the current session active (default: true)
    
    Requires authentication
    """
    token_service = TokenService(db)
    session_id = current_user.session_id if keep_current else None
    
    revoked_count = await token_service.revoke_user_tokens(
        user_id=current_user.user_id,
        keep_current_session=session_id
    )
    
    return {
        "message": f"Revoked {revoked_count} tokens",
        "revoked_count": revoked_count
    }


@router.get("/password-requirements",
            response_model=PasswordRequirements)
async def get_password_requirements():
    """
    Get password complexity requirements
    
    Public endpoint - no authentication required
    """
    from src.utils.password import default_password_policy
    return default_password_policy.requirements


@router.post("/security-event",
             responses={201: {"description": "Security event logged"}})
async def log_security_event(
    event: SecurityEventRequest,
    current_user = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Log security event for monitoring and alerting
    
    Can be called with or without authentication
    """
    # TODO: Implement security event logging to audit system
    # For now, just return success
    return {"message": "Security event logged", "event_id": "placeholder"}


@router.get("/health")
async def auth_health():
    """
    Authentication service health check
    
    Public endpoint for monitoring
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": "2024-01-01T00:00:00Z"  # Would use real timestamp
    }


# Token introspection endpoint (RFC 7662)
@router.post("/introspect",
             responses={
                 200: {"description": "Token introspection result"},
                 401: {"model": AuthErrorResponse}
             })
async def introspect_token(
    token: str,
    token_type_hint: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Token introspection endpoint (RFC 7662)
    
    Requires client authentication (service account)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client authentication required"
        )
    
    # Validate client credentials (service account)
    auth_service = AuthenticationService(db)
    validation = await auth_service.validate_token(credentials.credentials)
    
    if not validation.valid or not validation.is_service_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    # Introspect the provided token
    token_service = TokenService(db)
    token_info = await token_service.get_token_info(token)
    
    # Return RFC 7662 compliant response
    return {
        "active": token_info.get("valid", False),
        "sub": token_info.get("user_id"),
        "aud": token_info.get("claims", {}).get("aud"),
        "iss": token_info.get("claims", {}).get("iss"),
        "exp": token_info.get("claims", {}).get("exp"),
        "iat": token_info.get("claims", {}).get("iat"),
        "scope": " ".join(token_info.get("scopes", [])),
        "client_id": token_info.get("user_id") if token_info.get("claims", {}).get("is_service_account") else None,
        "token_type": token_info.get("token_type", "access_token"),
        "tenant_id": token_info.get("tenant_id")
    }