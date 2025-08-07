"""
Password reset service for secure password recovery workflows
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import hashlib
import secrets
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from src.models.user import User
from src.models.password_reset_token import PasswordResetToken
from src.models.tenant import Tenant
from src.utils.password import password_manager
from src.core.exceptions import NotFoundError, ValidationError, AuthenticationError
from src.utils.email import email_service  # We'll need to implement this

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service for handling password reset workflows"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.password_manager = password_manager
    
    async def request_password_reset(
        self, 
        email: str, 
        tenant_code: str,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request a password reset for a user
        
        Args:
            email: User's email address
            tenant_code: Tenant code for multi-tenant isolation
            request_ip: IP address of the request
            user_agent: User agent string
            
        Returns:
            Dict with reset request information
        """
        # Find tenant
        tenant_result = await self.db.execute(
            select(Tenant).where(
                and_(
                    Tenant.code == tenant_code.upper(),
                    Tenant.is_active == True
                )
            )
        )
        tenant = tenant_result.scalar_one_or_none()
        
        if not tenant:
            # Don't reveal if tenant exists
            logger.warning(f"Password reset requested for invalid tenant: {tenant_code}")
            return {
                "message": "If the email exists, a reset link has been sent",
                "success": True
            }
        
        # Find user
        user_result = await self.db.execute(
            select(User).where(
                and_(
                    User.email == email.lower(),
                    User.tenant_id == tenant.id,
                    User.is_active == True,
                    User.is_service_account == False  # Service accounts can't reset passwords
                )
            )
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if user exists (security best practice)
            logger.info(f"Password reset requested for non-existent user: {email}")
            return {
                "message": "If the email exists, a reset link has been sent",
                "success": True
            }
        
        # Check for recent reset requests (rate limiting)
        recent_tokens_result = await self.db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.created_at > datetime.utcnow() - timedelta(minutes=5)
                )
            )
        )
        recent_tokens = recent_tokens_result.scalars().all()
        
        if len(recent_tokens) >= 3:
            logger.warning(f"Too many password reset requests for user: {user.id}")
            raise ValidationError("Too many reset requests. Please wait before trying again.")
        
        # Invalidate any existing unused tokens
        await self.db.execute(
            update(PasswordResetToken)
            .where(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.is_used == False
                )
            )
            .values(is_used=True)
        )
        
        # Create new reset token
        reset_token = PasswordResetToken.create_for_user(
            user_id=user.id,
            request_ip=request_ip,
            user_agent=user_agent,
            expires_in_hours=1
        )
        
        self.db.add(reset_token)
        await self.db.commit()
        
        # Send reset email (placeholder - implement email service)
        reset_url = f"https://app.example.com/reset-password?token={reset_token.token}"
        
        # In production, this would send an actual email
        logger.info(f"Password reset token created for user {user.id}: {reset_token.token}")
        
        # TODO: Implement actual email sending
        # await email_service.send_password_reset_email(
        #     to_email=user.email,
        #     reset_url=reset_url,
        #     expires_in_hours=1
        # )
        
        return {
            "message": "If the email exists, a reset link has been sent",
            "success": True,
            # In development only - remove in production
            "debug_token": reset_token.token if logger.level <= logging.DEBUG else None,
            "debug_url": reset_url if logger.level <= logging.DEBUG else None
        }
    
    async def validate_reset_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a password reset token
        
        Args:
            token: The reset token to validate
            
        Returns:
            Dict with validation result
        """
        # Find token
        token_result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == token
            )
        )
        reset_token = token_result.scalar_one_or_none()
        
        if not reset_token:
            raise NotFoundError("Invalid or expired reset token")
        
        if not reset_token.is_valid():
            raise ValidationError("Reset token has expired or been used")
        
        # Get user information (don't expose sensitive data)
        user_result = await self.db.execute(
            select(User).where(User.id == reset_token.user_id)
        )
        user = user_result.scalar_one()
        
        return {
            "valid": True,
            "user_email": user.email,
            "expires_at": reset_token.expires_at.isoformat()
        }
    
    async def reset_password(
        self, 
        token: str, 
        new_password: str,
        confirm_password: str
    ) -> Dict[str, Any]:
        """
        Reset a user's password using a valid token
        
        Args:
            token: The reset token
            new_password: The new password
            confirm_password: Password confirmation
            
        Returns:
            Dict with reset result
        """
        # Validate passwords match
        if new_password != confirm_password:
            raise ValidationError("Passwords do not match")
        
        # Validate password strength
        from src.utils.password import default_password_policy
        policy_result = default_password_policy.enforce_policy(new_password)
        if not policy_result['valid']:
            raise ValidationError(f"Password does not meet requirements: {', '.join(policy_result['errors'])}")
        
        # Find and validate token
        token_result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == token
            )
        )
        reset_token = token_result.scalar_one_or_none()
        
        if not reset_token:
            raise NotFoundError("Invalid or expired reset token")
        
        if not reset_token.is_valid():
            raise ValidationError("Reset token has expired or been used")
        
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == reset_token.user_id)
        )
        user = user_result.scalar_one()
        
        # Hash new password
        new_password_hash = self.password_manager.hash_password(new_password)
        
        # Update user password
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                password_hash=new_password_hash,
                failed_login_count=0,  # Reset failed login count
                locked_until=None,  # Unlock account if locked
                updated_at=datetime.utcnow()
            )
        )
        
        # Mark token as used
        reset_token.mark_as_used()
        
        # Invalidate all other reset tokens for this user
        await self.db.execute(
            update(PasswordResetToken)
            .where(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.id != reset_token.id
                )
            )
            .values(is_used=True)
        )
        
        await self.db.commit()
        
        logger.info(f"Password successfully reset for user {user.id}")
        
        # TODO: Send confirmation email
        # await email_service.send_password_reset_confirmation(
        #     to_email=user.email
        # )
        
        return {
            "success": True,
            "message": "Password has been successfully reset"
        }
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired password reset tokens
        
        Returns:
            Number of tokens cleaned up
        """
        from sqlalchemy import delete
        
        result = await self.db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.expires_at < datetime.utcnow()
            )
        )
        
        await self.db.commit()
        
        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired password reset tokens")
        
        return deleted_count