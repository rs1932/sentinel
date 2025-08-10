"""
JWT utilities for token generation, validation, and management
"""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import uuid4
from jose import JWTError, jwt as jose_jwt
from jose.constants import ALGORITHMS

from src.schemas.auth import JWTClaims, JWTConfig
from src.config import settings


class JWTManager:
    """JWT token manager for encoding, decoding, and validating tokens"""
    
    def __init__(self, config: Optional[JWTConfig] = None):
        self.config = config or JWTConfig()
        # Use HS256 algorithm from settings for simplicity
        self.config.algorithm = settings.JWT_ALGORITHM if hasattr(settings, 'JWT_ALGORITHM') else "HS256"
        self._secret_key = self._load_secret_key()
    
    def _load_secret_key(self) -> str:
        """Load secret key for token signing (HS256)"""
        if hasattr(settings, 'JWT_SECRET_KEY'):
            return settings.JWT_SECRET_KEY
        
        # Development fallback
        return "development-secret-key-change-in-production"
    
    def generate_tokens(
        self,
        user_id: str,
        tenant_id: str,
        tenant_code: str,
        email: str,
        is_service_account: bool = False,
        scopes: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate access and refresh tokens"""
        now = datetime.utcnow()
        jti = str(uuid4())
        
        # Access token claims
        access_claims = {
            "sub": str(user_id),
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "exp": int((now + timedelta(minutes=self.config.access_token_expire_minutes)).timestamp()),
            "iat": int(now.timestamp()),
            "jti": jti,
            "tenant_id": str(tenant_id),
            "tenant_code": tenant_code,
            "email": email,
            "is_service_account": is_service_account,
            "scopes": scopes or [],
            "session_id": session_id,
            "token_type": "access"
        }
        
        # Refresh token claims (simpler, longer-lived)
        refresh_jti = str(uuid4())
        refresh_claims = {
            "sub": str(user_id),
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "exp": int((now + timedelta(days=self.config.refresh_token_expire_days)).timestamp()),
            "iat": int(now.timestamp()),
            "jti": refresh_jti,
            "tenant_id": str(tenant_id),
            "token_type": "refresh"
        }
        
        # Generate tokens
        access_token = jose_jwt.encode(
            access_claims,
            self._secret_key,
            algorithm=self.config.algorithm
        )
        
        refresh_token = jose_jwt.encode(
            refresh_claims,
            self._secret_key,
            algorithm=self.config.algorithm
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.config.access_token_expire_minutes * 60,
            "access_jti": jti,
            "refresh_jti": refresh_jti
        }
    
    def decode_token(self, token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """Decode and validate a JWT token"""
        try:
            # python-jose expects audience as a string, not a list
            audience = self.config.audience[0] if self.config.audience else None
            
            payload = jose_jwt.decode(
                token,
                self._secret_key,
                algorithms=[self.config.algorithm],
                audience=audience,
                issuer=self.config.issuer,
                options={"verify_exp": verify_exp}
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def validate_access_token(self, token: str) -> Dict[str, Any]:
        """Validate an access token and return claims"""
        claims = self.decode_token(token)
        
        if claims.get("token_type") != "access":
            raise ValueError("Invalid token type")
        
        return claims
    
    def validate_refresh_token(self, token: str) -> Dict[str, Any]:
        """Validate a refresh token and return claims"""
        claims = self.decode_token(token)
        
        if claims.get("token_type") != "refresh":
            raise ValueError("Invalid token type")
        
        return claims
    
    def extract_jti(self, token: str) -> str:
        """Extract JTI (JWT ID) from token without full validation"""
        try:
            # Decode without verification for JTI extraction
            unverified_payload = jose_jwt.get_unverified_claims(token)
            return unverified_payload.get("jti", "")
        except JWTError:
            return ""
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without throwing exception"""
        try:
            # First check expiration by comparing timestamps directly
            unverified_claims = jose_jwt.get_unverified_claims(token)
            exp_timestamp = unverified_claims.get("exp")
            if exp_timestamp:
                current_time = datetime.utcnow().timestamp()
                if exp_timestamp <= current_time:
                    return True
            
            # Also try full validation which might catch other issues
            self.decode_token(token, verify_exp=True)
            return False
        except ValueError as e:
            # Check for various expiration error messages from jose
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['expired', 'exp', 'expiry']):
                return True
            # For other errors, also consider expired (safer approach)
            return True
        except Exception:
            # Any other exception means token is invalid/expired
            return True
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Get token expiration time"""
        try:
            claims = self.decode_token(token, verify_exp=False)
            exp_timestamp = claims.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
            return None
        except (ValueError, Exception):
            # If we can't decode, try to get unverified claims
            try:
                unverified_claims = jose_jwt.get_unverified_claims(token)
                exp_timestamp = unverified_claims.get("exp")
                if exp_timestamp:
                    return datetime.fromtimestamp(exp_timestamp)
            except:
                pass
            return None
    
    def refresh_access_token(
        self,
        refresh_token: str,
        new_scopes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate new access token from refresh token"""
        refresh_claims = self.validate_refresh_token(refresh_token)
        
        # Extract user info from refresh token
        user_id = refresh_claims["sub"]
        tenant_id = refresh_claims["tenant_id"]
        
        # Note: We need to fetch additional user info from database
        # This is a simplified version - in practice, you'd query the database
        # for current user email, scopes, etc.
        
        now = datetime.utcnow()
        jti = str(uuid4())
        
        access_claims = {
            "sub": user_id,
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "exp": int((now + timedelta(minutes=self.config.access_token_expire_minutes)).timestamp()),
            "iat": int(now.timestamp()),
            "jti": jti,
            "tenant_id": tenant_id,
            "token_type": "access",
            "scopes": new_scopes or []
        }
        
        access_token = jose_jwt.encode(
            access_claims,
            self._secret_key,
            algorithm=self.config.algorithm
        )
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.config.access_token_expire_minutes * 60,
            "jti": jti
        }


class TokenValidator:
    """Utility class for token validation operations"""
    
    def __init__(self, jwt_manager: JWTManager):
        self.jwt_manager = jwt_manager
    
    def validate_token_format(self, token: str) -> bool:
        """Validate JWT token format"""
        if not token:
            return False
        
        # JWT should have 3 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            return False
        
        # Each part should be base64url encoded (no padding required for JWT)
        try:
            import base64
            for part in parts:
                # JWT uses base64url encoding which may not have padding
                # Add padding if needed for standard base64 decoding
                padded = part + '=' * (4 - len(part) % 4)
                try:
                    base64.urlsafe_b64decode(padded)
                except:
                    # Fallback to standard b64decode in case urlsafe fails
                    base64.b64decode(padded)
        except Exception:
            return False
        
        return True
    
    def extract_claims_without_validation(self, token: str) -> Dict[str, Any]:
        """Extract claims without signature validation (for debugging)"""
        try:
            return jose_jwt.get_unverified_claims(token)
        except JWTError:
            return {}


class TokenBlacklistManager:
    """Manager for token blacklisting operations"""
    
    def __init__(self, jwt_manager: JWTManager):
        self.jwt_manager = jwt_manager
    
    def blacklist_token(self, token: str, token_type: str = "access") -> str:
        """Add token to blacklist and return JTI"""
        jti = self.jwt_manager.extract_jti(token)
        if not jti:
            raise ValueError("Cannot extract JTI from token")
        
        # Get token expiry for cleanup
        expires_at = self.jwt_manager.get_token_expiry(token)
        if not expires_at:
            raise ValueError("Cannot determine token expiry")
        
        # In practice, this would interact with database
        # For now, return the JTI that should be blacklisted
        return jti
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        jti = self.jwt_manager.extract_jti(token)
        if not jti:
            return True  # Invalid tokens are considered blacklisted
        
        # In practice, check database for blacklisted JTI
        # This is a placeholder that always returns False
        return False
    
    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from blacklist"""
        # In practice, delete expired entries from database
        # Return count of deleted entries
        return 0


# Global JWT manager instance
jwt_manager = JWTManager()
token_validator = TokenValidator(jwt_manager)
blacklist_manager = TokenBlacklistManager(jwt_manager)