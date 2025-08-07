"""
Pydantic schemas for user management (Module 3)
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum
import uuid

from uuid import UUID


class BulkOperationType(str, Enum):
    """Available bulk operations for users"""
    activate = "activate"
    deactivate = "deactivate" 
    delete = "delete"
    assign_role = "assign_role"
    remove_role = "remove_role"


class SortField(str, Enum):
    """Available sort fields for user listing"""
    email = "email"
    username = "username" 
    created_at = "created_at"
    last_login = "last_login"
    login_count = "login_count"


class SortOrder(str, Enum):
    """Sort order options"""
    asc = "asc"
    desc = "desc"


# Request Schemas
class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    username: Optional[str] = None
    password: Optional[str] = None  # Optional for invite flow
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_active: bool = True
    send_invitation: bool = False
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 100:
                raise ValueError('Username must be less than 100 characters')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None and len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v


class UserQuery(BaseModel):
    """Schema for user query parameters"""
    tenant_id: Optional[UUID] = None
    role: Optional[str] = None
    group: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None  # Search by email/username
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)
    sort: SortField = Field(default=SortField.created_at)
    order: SortOrder = Field(default=SortOrder.desc)


class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr
    tenant_code: str


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserBulkOperation(BaseModel):
    """Schema for bulk user operations"""
    operation: BulkOperationType
    user_ids: List[UUID]
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Service Account Schemas
class ServiceAccountCreate(BaseModel):
    """Schema for creating a service account"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_active: bool = True
    
    @validator('name')
    def validate_name(cls, v):
        # Service account names should be unique and follow naming convention
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Service account name can only contain letters, numbers, hyphens and underscores')
        return v


class ServiceAccountUpdate(BaseModel):
    """Schema for updating a service account"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CredentialRotation(BaseModel):
    """Schema for credential rotation request"""
    revoke_existing: bool = True  # Whether to immediately revoke existing credentials


# Response Schemas
class UserResponse(BaseModel):
    """Basic user response schema"""
    id: UUID
    tenant_id: UUID
    email: EmailStr
    username: Optional[str]
    attributes: Dict[str, Any]
    preferences: Dict[str, Any]
    is_active: bool
    last_login: Optional[datetime]
    login_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v)
        }


class UserDetailResponse(UserResponse):
    """Detailed user response with additional fields"""
    failed_login_count: int
    locked_until: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v)
        }


class UserListResponse(BaseModel):
    """Paginated user list response"""
    items: List[UserResponse]
    total: int
    page: int
    limit: int
    pages: int
    
    class Config:
        from_attributes = True


class UserPermissionsResponse(BaseModel):
    """User permissions response (placeholder for future role integration)"""
    user_id: UUID
    tenant_id: UUID
    direct_permissions: List[Dict[str, Any]]
    inherited_permissions: List[Dict[str, Any]]
    effective_permissions: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: lambda v: str(v)
        }


class ServiceAccountResponse(BaseModel):
    """Service account response schema"""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    attributes: Dict[str, Any]
    client_id: str  # This is the service_account_key from user model
    is_active: bool
    last_login: Optional[datetime]
    login_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v)
        }


class ServiceAccountDetailResponse(ServiceAccountResponse):
    """Detailed service account response"""
    failed_login_count: int
    locked_until: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v)
        }


class ServiceAccountListResponse(BaseModel):
    """Paginated service account list response"""
    items: List[ServiceAccountResponse]
    total: int
    page: int
    limit: int
    pages: int
    
    class Config:
        from_attributes = True


class CredentialResponse(BaseModel):
    """Response for credential operations"""
    client_id: str
    client_secret: str  # Only returned during creation/rotation
    created_at: datetime
    expires_at: Optional[datetime] = None  # For future expiring credentials
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class BulkOperationResponse(BaseModel):
    """Response for bulk operations"""
    operation: BulkOperationType
    total_requested: int
    successful: int
    failed: int
    failed_ids: List[UUID] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            UUID: lambda v: str(v)
        }