"""
Password reset API endpoints for secure password recovery
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from ..services.password_reset_service import PasswordResetService
from ..schemas.auth import (
    PasswordResetRequest, PasswordResetValidation, 
    PasswordResetConfirm, PasswordResetResponse
)
from ..core.exceptions import NotFoundError, ValidationError
from ..core.rate_limiting import rate_limit

router = APIRouter(tags=["Password Reset"])


def get_client_info(request: Request) -> tuple[str, str]:
    """Extract client IP and user agent from request"""
    user_agent = request.headers.get("user-agent", "")
    x_forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.client.host
    return client_ip, user_agent


@router.post("/request", response_model=PasswordResetResponse)
@rate_limit(calls=3, period=300)  # 3 requests per 5 minutes per IP
async def request_password_reset(
    reset_request: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset email
    
    **Rate Limited**: 3 requests per 5 minutes per IP
    
    This endpoint always returns success to prevent email enumeration attacks.
    """
    client_ip, user_agent = get_client_info(request)
    
    try:
        service = PasswordResetService(db)
        result = await service.request_password_reset(
            email=reset_request.email,
            tenant_code=reset_request.tenant_code,
            request_ip=client_ip,
            user_agent=user_agent
        )
        return PasswordResetResponse(**result)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except Exception as e:
        # Log error but return success to prevent enumeration
        import logging
        logging.error(f"Password reset request error: {e}")
        return PasswordResetResponse(
            message="If the email exists, a reset link has been sent",
            success=True
        )


@router.post("/validate", response_model=PasswordResetValidation)
async def validate_reset_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate a password reset token
    
    Check if a reset token is valid before showing the password reset form.
    """
    try:
        service = PasswordResetService(db)
        result = await service.validate_reset_token(token)
        return PasswordResetValidation(**result)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired reset token"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/confirm", response_model=PasswordResetResponse)
@rate_limit(calls=5, period=300)  # 5 attempts per 5 minutes
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset with new password
    
    **Rate Limited**: 5 attempts per 5 minutes per IP
    
    Use the token received via email to set a new password.
    """
    try:
        service = PasswordResetService(db)
        result = await service.reset_password(
            token=reset_confirm.token,
            new_password=reset_confirm.new_password,
            confirm_password=reset_confirm.confirm_password
        )
        return PasswordResetResponse(**result)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired reset token"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )