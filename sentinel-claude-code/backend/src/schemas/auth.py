"""
Authentication schemas for login, token management, and security
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import re


class LoginRequest(BaseModel):
    """Request schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=255, description="User password")
    tenant_code: str = Field(..., min_length=1, max_length=50, description="Tenant code")
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=8, description="Optional MFA code")
    remember_me: Optional[bool] = Field(False, description="Whether to issue long-lived refresh token")
    
    @validator("tenant_code")
    def validate_tenant_code(cls, v):
        if not re.match(r"^[A-Z0-9][A-Z0-9-]*$", v):
            raise ValueError("Tenant code must contain only uppercase letters, numbers, and hyphens")
        return v


class ServiceAccountTokenRequest(BaseModel):
    """Request schema for service account authentication"""
    client_id: str = Field(..., min_length=1, max_length=100, description="Service account client ID")
    client_secret: str = Field(..., min_length=1, max_length=255, description="Service account secret")
    tenant_id: Optional[str] = Field(None, description="Tenant ID or code")
    scope: Optional[str] = Field(None, description="Requested scopes (space-separated)")
    
    @validator("scope")
    def validate_scope(cls, v):
        if v:
            # Basic scope validation - must be space-separated words
            scopes = v.split()
            for scope in scopes:
                if not re.match(r"^[a-z_:]+$", scope):
                    raise ValueError("Invalid scope format")
        return v


class TokenResponse(BaseModel):
    """Response schema for successful authentication"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token for token rotation")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token lifetime in seconds")
    scope: Optional[str] = Field(None, description="Granted scopes")
    user_id: Optional[UUID] = Field(None, description="Authenticated user ID")
    tenant_id: Optional[UUID] = Field(None, description="User's tenant ID")


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh"""
    refresh_token: str = Field(..., min_length=1, description="Valid refresh token")
    
    
class RevokeTokenRequest(BaseModel):
    """Request schema for token revocation"""
    token: str = Field(..., min_length=1, description="Token to revoke")
    token_type: str = Field(default="access_token", description="Token type: 'access_token' or 'refresh_token'")
    
    @validator("token_type")
    def validate_token_type(cls, v):
        if v not in ["access_token", "refresh_token"]:
            raise ValueError("token_type must be 'access_token' or 'refresh_token'")
        return v


class LogoutRequest(BaseModel):
    """Request schema for user logout (revoke all tokens)"""
    revoke_all_devices: bool = Field(default=False, description="Whether to revoke tokens from all devices")


class TokenValidationResponse(BaseModel):
    """Response schema for token validation"""
    valid: bool = Field(..., description="Whether the token is valid")
    user_id: Optional[UUID] = Field(None, description="Token owner user ID")
    tenant_id: Optional[UUID] = Field(None, description="User's tenant ID")
    scopes: Optional[List[str]] = Field(None, description="Token scopes")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    is_service_account: bool = Field(default=False, description="Whether token belongs to service account")


class UserTokenInfo(BaseModel):
    """User information embedded in JWT tokens"""
    user_id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    tenant_id: UUID = Field(..., description="Tenant ID")
    tenant_code: str = Field(..., description="Tenant code")
    is_service_account: bool = Field(default=False, description="Whether user is a service account")
    scopes: Optional[List[str]] = Field(default_factory=list, description="User permissions/scopes")


class DeviceInfo(BaseModel):
    """Device information for refresh tokens"""
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    device_name: Optional[str] = Field(None, description="Device name/identifier")
    platform: Optional[str] = Field(None, description="Platform (web, mobile, api)")
    location: Optional[str] = Field(None, description="Approximate location")


class RefreshTokenInfo(BaseModel):
    """Refresh token information for responses"""
    id: UUID = Field(..., description="Token ID")
    device_info: Dict[str, Any] = Field(default_factory=dict, description="Device information")
    created_at: datetime = Field(..., description="Token creation time")
    last_used_at: Optional[datetime] = Field(None, description="Last usage time")
    expires_at: datetime = Field(..., description="Token expiration time")


class AuthErrorResponse(BaseModel):
    """Error response schema for authentication failures"""
    error: str = Field(..., description="Error type")
    error_description: str = Field(..., description="Human-readable error description")
    error_code: Optional[str] = Field(None, description="Specific error code")
    retry_after: Optional[int] = Field(None, description="Retry delay in seconds for rate limiting")


class PasswordRequirements(BaseModel):
    """Password complexity requirements"""
    min_length: int = Field(default=8, description="Minimum password length")
    require_uppercase: bool = Field(default=True, description="Require uppercase letters")
    require_lowercase: bool = Field(default=True, description="Require lowercase letters")
    require_numbers: bool = Field(default=True, description="Require numbers")
    require_symbols: bool = Field(default=True, description="Require special characters")
    forbidden_patterns: List[str] = Field(default_factory=list, description="Forbidden password patterns")


class SecurityEventRequest(BaseModel):
    """Request schema for security event logging"""
    event_type: str = Field(..., description="Type of security event")
    severity: str = Field(default="info", description="Event severity: info, warning, error, critical")
    description: str = Field(..., description="Event description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    user_id: Optional[UUID] = Field(None, description="Related user ID")
    ip_address: Optional[str] = Field(None, description="Source IP address")


class JWTClaims(BaseModel):
    """JWT token claims structure"""
    sub: UUID = Field(..., description="Subject (user ID)")
    iss: str = Field(..., description="Issuer")
    aud: List[str] = Field(..., description="Audience")
    exp: int = Field(..., description="Expiration time (Unix timestamp)")
    iat: int = Field(..., description="Issued at (Unix timestamp)")
    jti: str = Field(..., description="JWT ID (unique token identifier)")
    
    # Custom claims
    tenant_id: UUID = Field(..., description="Tenant ID")
    tenant_code: str = Field(..., description="Tenant code")
    email: str = Field(..., description="User email")
    is_service_account: bool = Field(default=False, description="Service account flag")
    scopes: List[str] = Field(default_factory=list, description="Token scopes")
    session_id: Optional[str] = Field(None, description="Session identifier")
    

# Configuration models
class JWTConfig(BaseModel):
    """JWT configuration"""
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token lifetime in minutes")
    refresh_token_expire_days: int = Field(default=30, description="Refresh token lifetime in days")
    issuer: str = Field(default="sentinel-platform", description="Token issuer")
    audience: List[str] = Field(default_factory=lambda: ["sentinel-api"], description="Token audience")


class AuthConfig(BaseModel):
    """Authentication configuration"""
    jwt: JWTConfig = Field(default_factory=JWTConfig, description="JWT settings")
    password_requirements: PasswordRequirements = Field(default_factory=PasswordRequirements, description="Password requirements")
    max_login_attempts: int = Field(default=5, description="Max failed login attempts before lockout")
    lockout_duration_minutes: int = Field(default=30, description="Account lockout duration")
    require_email_verification: bool = Field(default=True, description="Require email verification for new accounts")
    enable_mfa: bool = Field(default=False, description="Enable multi-factor authentication")
    rate_limit_requests_per_minute: int = Field(default=60, description="Rate limit for auth endpoints")


# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    """Request schema for password reset"""
    email: EmailStr = Field(..., description="User email address")
    tenant_code: str = Field(..., min_length=1, max_length=50, description="Tenant code")
    
    @validator("tenant_code")
    def validate_tenant_code(cls, v):
        if not re.match(r"^[A-Z0-9][A-Z0-9-]*$", v.upper()):
            raise ValueError("Tenant code must contain only letters, numbers, and hyphens")
        return v.upper()


class PasswordResetValidation(BaseModel):
    """Response schema for token validation"""
    valid: bool = Field(..., description="Whether the token is valid")
    user_email: str = Field(..., description="Email of user (masked)")
    expires_at: str = Field(..., description="Token expiration time")


class PasswordResetConfirm(BaseModel):
    """Request schema for confirming password reset"""
    token: str = Field(..., min_length=1, description="Reset token from email")
    new_password: str = Field(..., min_length=8, max_length=255, description="New password")
    confirm_password: str = Field(..., min_length=8, max_length=255, description="Password confirmation")
    
    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordResetResponse(BaseModel):
    """Response schema for password reset operations"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Result message")
    debug_token: Optional[str] = Field(None, description="Debug only - reset token")
    debug_url: Optional[str] = Field(None, description="Debug only - reset URL")