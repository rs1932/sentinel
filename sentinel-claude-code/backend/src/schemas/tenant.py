from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re
from enum import Enum

# Define enums locally to avoid circular imports
class TenantType(str, Enum):
    ROOT = "root"
    SUB_TENANT = "sub_tenant"

class IsolationMode(str, Enum):
    SHARED = "shared"
    DEDICATED = "dedicated"

class TenantBase(BaseModel):
    class Config:
        use_enum_values = True
    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    code: str = Field(..., min_length=1, max_length=50, description="Unique tenant code")
    type: TenantType = Field(default=TenantType.ROOT, description="Tenant type")
    isolation_mode: IsolationMode = Field(default=IsolationMode.SHARED, description="Isolation mode")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Tenant settings")
    features: List[str] = Field(default_factory=list, description="Enabled features")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator("code")
    def validate_code(cls, v):
        if not re.match(r"^[A-Z0-9][A-Z0-9-]*$", v):
            raise ValueError("Code must contain only uppercase letters, numbers, and hyphens, and start with a letter or number")
        return v
    
    @validator("features")
    def validate_features(cls, v):
        allowed_features = [
            "multi_factor_auth",
            "advanced_audit",
            "ai_insights",
            "custom_workflows",
            "api_access",
            "sso",
            "field_encryption",
            "compliance_reporting"
        ]
        for feature in v:
            if feature not in allowed_features:
                raise ValueError(f"Unknown feature: {feature}")
        return v

class TenantCreate(TenantBase):
    parent_tenant_id: Optional[UUID] = Field(None, description="Parent tenant ID for sub-tenants")
    
    @validator("parent_tenant_id")
    def validate_parent_tenant(cls, v, values):
        if "type" in values:
            if values["type"] == TenantType.ROOT and v is not None:
                raise ValueError("Root tenants cannot have a parent")
            if values["type"] == TenantType.SUB_TENANT and v is None:
                raise ValueError("Sub-tenants must have a parent")
        return v

class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    settings: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @validator("features")
    def validate_features(cls, v):
        if v is not None:
            allowed_features = [
                "multi_factor_auth",
                "advanced_audit",
                "ai_insights",
                "custom_workflows",
                "api_access",
                "sso",
                "field_encryption",
                "compliance_reporting"
            ]
            for feature in v:
                if feature not in allowed_features:
                    raise ValueError(f"Unknown feature: {feature}")
        return v

class TenantQuery(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    type: Optional[TenantType] = None
    parent_tenant_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class TenantResponse(BaseModel):
    id: UUID
    name: str
    code: str
    type: TenantType
    parent_tenant_id: Optional[UUID]
    isolation_mode: IsolationMode
    settings: Dict[str, Any]
    features: List[str]
    metadata: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True
        populate_by_name = True

class TenantDetailResponse(TenantResponse):
    sub_tenants_count: int = 0
    users_count: int = 0
    hierarchy: List["TenantResponse"] = []
    
    class Config:
        from_attributes = True
        use_enum_values = True

class TenantListResponse(BaseModel):
    items: List[TenantResponse]
    total: int
    limit: int
    offset: int
    
    class Config:
        from_attributes = True

class SubTenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Sub-tenant name")
    code: str = Field(..., min_length=1, max_length=50, description="Unique sub-tenant code")
    isolation_mode: IsolationMode = Field(default=IsolationMode.SHARED, description="Isolation mode")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Tenant settings")
    features: List[str] = Field(default_factory=list, description="Enabled features")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator("code")
    def validate_code(cls, v):
        if not re.match(r"^[A-Z0-9][A-Z0-9-]*$", v):
            raise ValueError("Code must contain only uppercase letters, numbers, and hyphens, and start with a letter or number")
        return v