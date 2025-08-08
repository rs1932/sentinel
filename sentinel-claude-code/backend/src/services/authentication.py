"""
Authentication service for user login, logout, and token management
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, delete
import uuid
import hashlib
import secrets

from src.models.user import User
from src.models.tenant import Tenant
from src.models.refresh_token import RefreshToken
from src.models.token_blacklist import TokenBlacklist
from src.schemas.auth import (
    LoginRequest, ServiceAccountTokenRequest, TokenResponse,
    RefreshTokenRequest, RevokeTokenRequest, LogoutRequest,
    TokenValidationResponse, DeviceInfo
)
from src.utils.jwt import jwt_manager, blacklist_manager
from src.utils.password import password_manager, default_password_policy
from src.core.exceptions import AuthenticationError, ValidationError, NotFoundError


class AuthenticationService:
    """Service for handling user authentication operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.jwt_manager = jwt_manager
        self.password_manager = password_manager
        self.password_policy = default_password_policy
    
    async def authenticate_user(self, login_request: LoginRequest, device_info: Optional[DeviceInfo] = None) -> TokenResponse:
        """
        Authenticate user with email/password and return tokens
        """
        # Find tenant by code
        tenant_result = await self.db.execute(
            select(Tenant).where(
                and_(
                    Tenant.code == login_request.tenant_code.upper(),
                    Tenant.is_active == True
                )
            )
        )
        tenant = tenant_result.scalar_one_or_none()
        
        if not tenant:
            raise AuthenticationError("Invalid tenant code")
        
        # Find user by email and tenant
        user_result = await self.db.execute(
            select(User).where(
                and_(
                    User.email == login_request.email.lower(),
                    User.tenant_id == tenant.id,
                    User.is_active == True
                )
            )
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise AuthenticationError("Account is temporarily locked due to failed login attempts")
        
        # Verify password
        if not user.password_hash:
            raise AuthenticationError("Account not configured for password login")
        
        if not self.password_manager.verify_password(login_request.password, user.password_hash):
            await self._handle_failed_login(user)
            raise AuthenticationError("Invalid credentials")
        
        # Handle MFA if enabled (placeholder for future implementation)
        if login_request.mfa_code:
            # TODO: Implement MFA validation
            pass
        
        # Reset failed login attempts on successful login
        if user.failed_login_count and user.failed_login_count > 0:
            await self.db.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    failed_login_count=0,
                    locked_until=None,
                    last_login=datetime.utcnow(),
                    login_count=(user.login_count or 0) + 1
                )
            )
        
        # Generate tokens
        session_id = str(uuid.uuid4())
        tokens = self.jwt_manager.generate_tokens(
            user_id=str(user.id),
            tenant_id=str(tenant.id),
            tenant_code=tenant.code,
            email=user.email,
            is_service_account=user.is_service_account,
            scopes=self._get_user_scopes(user),
            session_id=session_id
        )
        
        # Store refresh token
        if tokens.get("refresh_token"):
            await self._store_refresh_token(
                user=user,
                token_hash=self._hash_token(tokens["refresh_token"]),
                refresh_jti=tokens["refresh_jti"],
                device_info=device_info,
                remember_me=login_request.remember_me
            )
        
        await self.db.commit()
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user_id=user.id,
            tenant_id=tenant.id,
            scope=" ".join(self._get_user_scopes(user)) if self._get_user_scopes(user) else None
        )
    
    async def authenticate_service_account(self, request: ServiceAccountTokenRequest) -> TokenResponse:
        """
        Authenticate service account with client credentials
        """
        # Find user by service account key
        user_result = await self.db.execute(
            select(User).where(
                and_(
                    User.service_account_key == request.client_id,
                    User.is_service_account == True,
                    User.is_active == True
                )
            )
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("Invalid client credentials")
        
        # Verify client secret (stored as password hash)
        if not user.password_hash:
            raise AuthenticationError("Service account not properly configured")
        
        if not self.password_manager.verify_password(request.client_secret, user.password_hash):
            raise AuthenticationError("Invalid client credentials")
        
        # Get tenant information
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == user.tenant_id)
        )
        tenant = tenant_result.scalar_one()
        
        # Validate tenant if specified
        if request.tenant_id:
            if request.tenant_id != str(tenant.id) and request.tenant_id != tenant.code:
                raise AuthenticationError("Invalid tenant specification")
        
        # Parse and validate scopes
        requested_scopes = request.scope.split() if request.scope else []
        granted_scopes = await self._validate_service_account_scopes(user, requested_scopes)
        
        # Generate access token (no refresh token for service accounts)
        tokens = self.jwt_manager.generate_tokens(
            user_id=str(user.id),
            tenant_id=str(tenant.id),
            tenant_code=tenant.code,
            email=user.email,
            is_service_account=True,
            scopes=granted_scopes
        )
        
        # Update last access time
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login=datetime.utcnow())
        )
        
        await self.db.commit()
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=None,  # No refresh tokens for service accounts
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user_id=user.id,
            tenant_id=tenant.id,
            scope=" ".join(granted_scopes) if granted_scopes else None
        )
    
    async def refresh_token(self, request: RefreshTokenRequest, device_info: Optional[DeviceInfo] = None) -> TokenResponse:
        """
        Refresh access token using refresh token
        """
        try:
            # Validate refresh token
            claims = self.jwt_manager.validate_refresh_token(request.refresh_token)
        except ValueError as e:
            raise AuthenticationError(f"Invalid refresh token: {str(e)}")
        
        # Check if token is blacklisted
        if blacklist_manager.is_token_blacklisted(request.refresh_token):
            raise AuthenticationError("Refresh token has been revoked")
        
        user_id = UUID(claims["sub"])
        token_hash = self._hash_token(request.refresh_token)
        
        # Find and validate stored refresh token
        refresh_token_result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            )
        )
        stored_token = refresh_token_result.scalar_one_or_none()
        
        if not stored_token:
            raise AuthenticationError("Refresh token not found or expired")
        
        # Get user and tenant
        user_result = await self.db.execute(
            select(User).where(
                and_(
                    User.id == user_id,
                    User.is_active == True
                )
            )
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("User not found or inactive")
        
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == user.tenant_id)
        )
        tenant = tenant_result.scalar_one()
        
        # Update refresh token usage
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == stored_token.id)
            .values(
                last_used_at=datetime.utcnow()
            )
        )
        
        # Generate new access token
        tokens = self.jwt_manager.generate_tokens(
            user_id=str(user.id),
            tenant_id=str(tenant.id),
            tenant_code=tenant.code,
            email=user.email,
            is_service_account=user.is_service_account,
            scopes=self._get_user_scopes(user),
            session_id=str(stored_token.id)  # Use refresh token ID as session ID
        )
        
        await self.db.commit()
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=None,  # Don't issue new refresh token unless requested
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user_id=user.id,
            tenant_id=tenant.id
        )
    
    async def revoke_token(self, request: RevokeTokenRequest) -> bool:
        """
        Revoke a specific token (access or refresh)
        """
        if request.token_type == "refresh_token":
            return await self._revoke_refresh_token(request.token)
        else:
            return await self._revoke_access_token(request.token)
    
    async def logout_user(self, access_token: str, request: LogoutRequest) -> bool:
        """
        Logout user and revoke tokens
        """
        try:
            claims = self.jwt_manager.validate_access_token(access_token)
        except ValueError:
            return False  # Invalid token, consider logout successful
        
        user_id = UUID(claims["sub"])
        session_id = claims.get("session_id")
        
        # Revoke access token
        await self._revoke_access_token(access_token)
        
        if request.revoke_all_devices:
            # Delete all refresh tokens for user (since we don't have is_active/revoked_at fields)
            await self.db.execute(
                f"DELETE FROM sentinel.refresh_tokens WHERE user_id = '{user_id}'"
            )
        # For now, we'll just revoke all tokens since we don't have session tracking
        
        await self.db.commit()
        return True
    
    def validate_token(self, token: str) -> TokenValidationResponse:
        """
        Validate an access token and return token information
        """
        try:
            claims = self.jwt_manager.validate_access_token(token)
        except ValueError as e:
            return TokenValidationResponse(
                valid=False,
                expires_at=None
            )
        
        # Check if token is blacklisted
        if blacklist_manager.is_token_blacklisted(token):
            return TokenValidationResponse(valid=False)
        
        return TokenValidationResponse(
            valid=True,
            user_id=UUID(claims["sub"]),
            tenant_id=UUID(claims["tenant_id"]),
            scopes=claims.get("scopes", []),
            expires_at=datetime.fromtimestamp(claims["exp"]),
            is_service_account=claims.get("is_service_account", False)
        )
    
    # Private helper methods
    
    async def _handle_failed_login(self, user: User):
        """Handle failed login attempt"""
        failed_attempts = (user.failed_login_count or 0) + 1
        
        # Check if account should be locked
        max_attempts = 5  # Could be configurable
        lockout_duration = timedelta(minutes=30)  # Could be configurable
        
        updates = {
            "failed_login_count": failed_attempts
        }
        
        if failed_attempts >= max_attempts:
            updates.update({
                "locked_until": datetime.utcnow() + lockout_duration
            })
        
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(**updates)
        )
        await self.db.commit()
    
    def _get_user_scopes(self, user: User) -> List[str]:
        """Get user permissions/scopes (placeholder for future role system)"""
        # TODO: Implement proper role-based scope resolution
        # For now, return basic scopes based on user type
        
        # Check if user is super admin (on PLATFORM tenant)
        platform_tenant_id = "00000000-0000-0000-0000-000000000000"
        is_super_admin = str(user.tenant_id) == platform_tenant_id
        
        if user.is_service_account:
            return [
                "api:read", "api:write",
                "tenant:read", "tenant:write", "tenant:admin",
                "user:read", "user:write", "user:admin",
                "service_account:read", "service_account:write", "service_account:admin",
                "role:read", "role:write", "role:admin",
                "group:read", "group:write", "group:admin",
                "permission:read", "permission:write", "permission:admin"
            ]
        elif is_super_admin:
            # Super admin gets global scopes across all tenants
            return [
                "user:profile",
                "platform:admin",  # Global platform administration
                "tenant:read", "tenant:write", "tenant:admin", "tenant:global",
                "user:read", "user:write", "user:admin", "user:global",
                "service_account:read", "service_account:write", "service_account:admin", "service_account:global",
                "role:read", "role:write", "role:admin", "role:global",
                "group:read", "group:write", "group:admin", "group:global",
                "permission:read", "permission:write", "permission:admin", "permission:global",
                "system:admin",  # System-level administration
                "audit:read", "audit:write"  # Audit log access
            ]
        else:
            # Regular tenant users
            return [
                "user:profile",
                "tenant:read", "tenant:write", "tenant:admin",
                "user:read", "user:write", "user:admin",
                "service_account:read", "service_account:write", "service_account:admin",
                "role:read", "role:write", "role:admin",
                "group:read", "group:write", "group:admin",
                "permission:read", "permission:write", "permission:admin"
            ]
    
    async def _validate_service_account_scopes(self, user: User, requested_scopes: List[str]) -> List[str]:
        """Validate and filter requested scopes for service account"""
        # TODO: Implement proper scope validation based on service account permissions
        # For now, grant basic scopes
        available_scopes = ["api:read", "api:write", "tenant:read", "user:read"]
        
        if not requested_scopes:
            return ["api:read"]
        
        # Filter to only available scopes
        granted_scopes = [scope for scope in requested_scopes if scope in available_scopes]
        
        return granted_scopes or ["api:read"]
    
    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def _store_refresh_token(
        self,
        user: User,
        token_hash: str,
        refresh_jti: str,
        device_info: Optional[DeviceInfo],
        remember_me: bool = False
    ):
        """Store refresh token in database"""
        expires_days = 90 if remember_me else 30
        
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            device_info=device_info.dict() if device_info else {},
            expires_at=datetime.utcnow() + timedelta(days=expires_days)
        )
        
        self.db.add(refresh_token)
    
    async def _revoke_refresh_token(self, token: str) -> bool:
        """Revoke a refresh token by deleting it"""
        token_hash = self._hash_token(token)
        
        # Delete the refresh token from database
        from sqlalchemy import delete
        result = await self.db.execute(
            delete(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        
        await self.db.commit()
        return result.rowcount > 0
    
    async def _revoke_access_token(self, token: str) -> bool:
        """Revoke an access token by adding to blacklist"""
        try:
            jti = blacklist_manager.blacklist_token(token, "access")
            
            # Store in database blacklist
            expires_at = self.jwt_manager.get_token_expiry(token)
            if not expires_at:
                return False
            
            blacklist_entry = TokenBlacklist(
                jti=jti,
                token_type="access",
                expires_at=expires_at,
                reason="revoked"
            )
            
            self.db.add(blacklist_entry)
            await self.db.commit()
            return True
        except Exception:
            return False