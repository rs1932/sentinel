"""
Token service for JWT token operations and management
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
import uuid

from src.models.user import User
from src.models.tenant import Tenant
from src.models.refresh_token import RefreshToken
from src.models.token_blacklist import TokenBlacklist
from src.schemas.auth import (
    TokenValidationResponse, RefreshTokenInfo, 
    UserTokenInfo, JWTClaims
)
from src.utils.jwt import jwt_manager, blacklist_manager
from src.core.exceptions import AuthenticationError, NotFoundError


class TokenService:
    """Service for JWT token operations and lifecycle management"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.jwt_manager = jwt_manager
        self.blacklist_manager = blacklist_manager
    
    async def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a token
        """
        try:
            claims = self.jwt_manager.decode_token(token, verify_exp=False)
            
            is_expired = self.jwt_manager.is_token_expired(token)
            is_blacklisted = await self.blacklist_manager.is_token_blacklisted(token)
            
            return {
                "valid": not is_expired and not is_blacklisted,
                "expired": is_expired,
                "blacklisted": is_blacklisted,
                "claims": claims,
                "token_type": claims.get("token_type", "unknown"),
                "user_id": claims.get("sub"),
                "tenant_id": claims.get("tenant_id"),
                "expires_at": datetime.fromtimestamp(claims["exp"]) if claims.get("exp") else None,
                "issued_at": datetime.fromtimestamp(claims["iat"]) if claims.get("iat") else None,
                "jti": claims.get("jti"),
                "scopes": claims.get("scopes", [])
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "claims": {}
            }
    
    async def get_user_token_info(self, token: str) -> Optional[UserTokenInfo]:
        """
        Extract user information from token
        """
        try:
            claims = self.jwt_manager.validate_access_token(token)
            
            return UserTokenInfo(
                user_id=uuid.UUID(claims["sub"]),
                email=claims["email"],
                tenant_id=uuid.UUID(claims["tenant_id"]),
                tenant_code=claims["tenant_code"],
                is_service_account=claims.get("is_service_account", False),
                scopes=claims.get("scopes", [])
            )
        except Exception:
            return None
    
    async def get_user_active_tokens(self, user_id: uuid.UUID) -> List[RefreshTokenInfo]:
        """
        Get all active refresh tokens for a user
        """
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_active == True,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            ).order_by(RefreshToken.created_at.desc())
        )
        tokens = result.scalars().all()
        
        return [
            RefreshTokenInfo(
                id=token.id,
                device_info=token.device_info,
                created_at=token.created_at,
                last_used_at=token.last_used_at,
                expires_at=token.expires_at
            )
            for token in tokens
        ]
    
    async def revoke_user_tokens(
        self,
        user_id: uuid.UUID,
        token_id: Optional[uuid.UUID] = None,
        keep_current_session: Optional[str] = None
    ) -> int:
        """
        Revoke refresh tokens for a user
        
        Args:
            user_id: User ID
            token_id: Specific token to revoke (if None, revoke all)
            keep_current_session: Session ID to keep active
            
        Returns:
            Number of tokens revoked
        """
        query = update(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_active == True
            )
        )
        
        # Filter by specific token if provided
        if token_id:
            query = query.where(RefreshToken.id == token_id)
        
        # Exclude current session if provided
        if keep_current_session:
            query = query.where(RefreshToken.session_id != keep_current_session)
        
        result = await self.db.execute(
            query.values(
                is_active=False,
                revoked_at=datetime.utcnow()
            )
        )
        
        await self.db.commit()
        return result.rowcount
    
    async def cleanup_expired_tokens(self) -> Dict[str, int]:
        """
        Clean up expired tokens from database
        
        Returns:
            Count of cleaned up tokens by type
        """
        counts = {"refresh_tokens": 0, "blacklist_entries": 0}
        
        # Clean up expired refresh tokens
        refresh_result = await self.db.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.utcnow()
            )
        )
        counts["refresh_tokens"] = refresh_result.rowcount
        
        # Clean up expired blacklist entries
        blacklist_result = await self.db.execute(
            delete(TokenBlacklist).where(
                TokenBlacklist.expires_at < datetime.utcnow()
            )
        )
        counts["blacklist_entries"] = blacklist_result.rowcount
        
        await self.db.commit()
        return counts
    
    async def rotate_refresh_token(self, old_token: str, device_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Rotate a refresh token (generate new one and revoke old)
        """
        try:
            # Validate old token
            claims = self.jwt_manager.validate_refresh_token(old_token)
            user_id = uuid.UUID(claims["sub"])
            
            # Find stored refresh token
            token_hash = self._hash_token(old_token)
            result = await self.db.execute(
                select(RefreshToken).where(
                    and_(
                        RefreshToken.user_id == user_id,
                        RefreshToken.token_hash == token_hash,
                        RefreshToken.is_active == True
                    )
                )
            )
            old_refresh_token = result.scalar_one_or_none()
            
            if not old_refresh_token:
                raise AuthenticationError("Refresh token not found")
            
            # Get user and tenant info
            user_result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one()
            
            tenant_result = await self.db.execute(
                select(Tenant).where(Tenant.id == user.tenant_id)
            )
            tenant = tenant_result.scalar_one()
            
            # Generate new tokens
            new_tokens = self.jwt_manager.generate_tokens(
                user_id=str(user.id),
                tenant_id=str(tenant.id),
                tenant_code=tenant.code,
                email=user.email,
                is_service_account=user.is_service_account,
                scopes=await self._get_user_scopes(user),
                session_id=old_refresh_token.session_id
            )
            
            # Revoke old token
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.id == old_refresh_token.id)
                .values(
                    is_active=False,
                    revoked_at=datetime.utcnow()
                )
            )
            
            # Store new refresh token
            new_refresh_token = RefreshToken(
                user_id=user.id,
                token_hash=self._hash_token(new_tokens["refresh_token"]),
                jti=new_tokens["refresh_jti"],
                device_info=device_info or old_refresh_token.device_info,
                expires_at=datetime.utcnow() + timedelta(days=30),
                session_id=old_refresh_token.session_id
            )
            
            self.db.add(new_refresh_token)
            await self.db.commit()
            
            return {
                "access_token": new_tokens["access_token"],
                "refresh_token": new_tokens["refresh_token"],
                "token_type": new_tokens["token_type"],
                "expires_in": new_tokens["expires_in"]
            }
            
        except Exception as e:
            await self.db.rollback()
            raise AuthenticationError(f"Token rotation failed: {str(e)}")
    
    async def blacklist_token_by_jti(self, jti: str, token_type: str = "access", reason: str = "revoked") -> bool:
        """
        Add token to blacklist by JTI
        """
        try:
            # Check if already blacklisted
            existing = await self.db.execute(
                select(TokenBlacklist).where(TokenBlacklist.jti == jti)
            )
            if existing.scalar_one_or_none():
                return True  # Already blacklisted
            
            # Calculate expiry (tokens should be short-lived)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            blacklist_entry = TokenBlacklist(
                jti=jti,
                token_type=token_type,
                expires_at=expires_at,
                reason=reason
            )
            
            self.db.add(blacklist_entry)
            await self.db.commit()
            return True
            
        except Exception:
            await self.db.rollback()
            return False
    
    async def is_token_blacklisted_by_jti(self, jti: str) -> bool:
        """
        Check if token is blacklisted by JTI
        """
        result = await self.db.execute(
            select(TokenBlacklist).where(
                and_(
                    TokenBlacklist.jti == jti,
                    TokenBlacklist.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def get_token_statistics(self, user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """
        Get token usage statistics
        """
        stats = {
            "active_refresh_tokens": 0,
            "expired_refresh_tokens": 0,
            "blacklisted_tokens": 0,
            "user_sessions": 0
        }
        
        # Base queries
        refresh_query = select(RefreshToken)
        blacklist_query = select(TokenBlacklist)
        
        if user_id:
            refresh_query = refresh_query.where(RefreshToken.user_id == user_id)
        
        # Active refresh tokens
        active_result = await self.db.execute(
            refresh_query.where(
                and_(
                    RefreshToken.is_active == True,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            )
        )
        stats["active_refresh_tokens"] = len(active_result.scalars().all())
        
        # Expired refresh tokens
        expired_result = await self.db.execute(
            refresh_query.where(
                or_(
                    RefreshToken.is_active == False,
                    RefreshToken.expires_at <= datetime.utcnow()
                )
            )
        )
        stats["expired_refresh_tokens"] = len(expired_result.scalars().all())
        
        # Blacklisted tokens
        blacklist_result = await self.db.execute(
            blacklist_query.where(
                TokenBlacklist.expires_at > datetime.utcnow()
            )
        )
        stats["blacklisted_tokens"] = len(blacklist_result.scalars().all())
        
        # Unique user sessions (if not filtering by user)
        if not user_id:
            session_result = await self.db.execute(
                select(RefreshToken.user_id).distinct().where(
                    and_(
                        RefreshToken.is_active == True,
                        RefreshToken.expires_at > datetime.utcnow()
                    )
                )
            )
            stats["user_sessions"] = len(session_result.scalars().all())
        
        return stats
    
    async def validate_token_claims(self, token: str, required_scopes: List[str] = None) -> TokenValidationResponse:
        """
        Validate token and check required scopes
        """
        try:
            claims = self.jwt_manager.validate_access_token(token)
            
            # Check if blacklisted
            if await self.is_token_blacklisted_by_jti(claims.get("jti", "")):
                return TokenValidationResponse(valid=False)
            
            # Check scopes if required
            token_scopes = claims.get("scopes", [])
            if required_scopes:
                missing_scopes = [scope for scope in required_scopes if scope not in token_scopes]
                if missing_scopes:
                    return TokenValidationResponse(
                        valid=False,
                        user_id=uuid.UUID(claims["sub"]),
                        tenant_id=uuid.UUID(claims["tenant_id"])
                    )
            
            return TokenValidationResponse(
                valid=True,
                user_id=uuid.UUID(claims["sub"]),
                tenant_id=uuid.UUID(claims["tenant_id"]),
                scopes=token_scopes,
                expires_at=datetime.fromtimestamp(claims["exp"]),
                is_service_account=claims.get("is_service_account", False)
            )
            
        except Exception:
            return TokenValidationResponse(valid=False)
    
    # Private helper methods
    
    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def _get_user_scopes(self, user: User) -> List[str]:
        """Get user scopes (placeholder for role system)"""
        # TODO: Implement proper role-based scope resolution
        if user.is_service_account:
            return ["api:read", "api:write"]
        else:
            return ["user:profile", "tenant:read"]