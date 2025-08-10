"""
Pydantic schemas for Role Management (Module 4)
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID
from enum import Enum

# Define RoleType enum locally to avoid circular imports
class RoleType(str, Enum):
    SYSTEM = "system"
    CUSTOM = "custom"


class RoleBase(BaseModel):
    """Base role schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    display_name: Optional[str] = Field(None, max_length=255, description="Human-readable role name")
    description: Optional[str] = Field(None, description="Role description")
    type: RoleType = Field(RoleType.CUSTOM, description="Role type")
    parent_role_id: Optional[UUID] = Field(None, description="Parent role ID for inheritance")
    is_assignable: bool = Field(True, description="Whether role can be assigned to users")
    priority: int = Field(0, description="Role priority for conflict resolution")
    role_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional role metadata")
    is_active: bool = Field(True, description="Whether role is active")


class RoleCreate(RoleBase):
    """Schema for creating a new role."""
    
    @validator('name')
    def validate_name(cls, v):
        """Validate role name."""
        if not v.strip():
            raise ValueError("Role name cannot be empty")
        # Role names should be snake_case or kebab-case for consistency
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError("Role name can only contain letters, numbers, hyphens, underscores, and periods")
        return v.strip().lower()
    
    @validator('type')
    def validate_type(cls, v):
        """Validate role type."""
        if v not in [RoleType.SYSTEM, RoleType.CUSTOM]:
            raise ValueError(f"Invalid role type. Must be one of: {[t.value for t in RoleType]}")
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority range."""
        if v < 0 or v > 1000:
            raise ValueError("Priority must be between 0 and 1000")
        return v


class RoleUpdate(BaseModel):
    """Schema for updating an existing role."""
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    parent_role_id: Optional[UUID] = None
    is_assignable: Optional[bool] = None
    priority: Optional[int] = None
    role_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority range."""
        if v is not None and (v < 0 or v > 1000):
            raise ValueError("Priority must be between 0 and 1000")
        return v


class RoleQuery(BaseModel):
    """Schema for role query parameters."""
    tenant_id: Optional[UUID] = None
    type: Optional[RoleType] = None
    is_assignable: Optional[bool] = None
    is_active: Optional[bool] = None
    parent_role_id: Optional[UUID] = None
    search: Optional[str] = Field(None, description="Search in name and display_name")
    
    # Pagination
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of records to return")
    
    # Sorting
    sort_by: str = Field("name", description="Field to sort by")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class RoleResponse(BaseModel):
    """Basic role response schema."""
    id: UUID
    tenant_id: UUID
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    type: RoleType
    parent_role_id: Optional[UUID] = None
    is_assignable: bool
    priority: int
    role_metadata: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class RoleDetailResponse(RoleResponse):
    """Detailed role response with additional information."""
    # Hierarchy information
    parent_role: Optional['RoleResponse'] = None
    child_roles: List['RoleResponse'] = Field(default_factory=list)
    
    # Assignment counts
    user_count: int = Field(0, description="Number of users assigned this role")
    
    # Effective permissions will be added when permissions are implemented
    # effective_permissions: List[PermissionResponse] = Field(default_factory=list)


class RoleListResponse(BaseModel):
    """Paginated role list response."""
    items: List[RoleResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


# User Role Assignment Schemas
class UserRoleAssignmentBase(BaseModel):
    """Base schema for user-role assignments."""
    user_id: UUID
    role_id: UUID
    expires_at: Optional[datetime] = None
    is_active: bool = True


class UserRoleAssignmentCreate(UserRoleAssignmentBase):
    """Schema for creating user-role assignments."""
    pass


class UserRoleAssignmentUpdate(BaseModel):
    """Schema for updating user-role assignments."""
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class UserRoleAssignmentResponse(UserRoleAssignmentBase):
    """Response schema for user-role assignments."""
    id: UUID
    granted_by: Optional[UUID] = None
    granted_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Related data
    role: Optional[RoleResponse] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class BulkRoleAssignmentRequest(BaseModel):
    """Schema for bulk role assignments."""
    user_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    role_ids: List[UUID] = Field(..., min_items=1, max_items=20)
    expires_at: Optional[datetime] = None
    
    @validator('user_ids')
    def validate_unique_user_ids(cls, v):
        """Ensure user IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate user IDs are not allowed")
        return v
    
    @validator('role_ids')
    def validate_unique_role_ids(cls, v):
        """Ensure role IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate role IDs are not allowed")
        return v


class BulkRoleAssignmentResponse(BaseModel):
    """Response schema for bulk role assignments."""
    successful_assignments: int
    failed_assignments: int
    errors: List[str] = Field(default_factory=list)
    assignment_ids: List[UUID] = Field(default_factory=list)


class RoleHierarchyResponse(BaseModel):
    """Response schema for role hierarchy."""
    role: RoleResponse
    ancestors: List[RoleResponse] = Field(default_factory=list, description="Parent roles up the chain")
    descendants: List[RoleResponse] = Field(default_factory=list, description="Child roles down the chain")
    inheritance_path: List[str] = Field(default_factory=list, description="Role names in inheritance order")


class RoleValidationResponse(BaseModel):
    """Response schema for role validation."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    circular_dependency: bool = Field(False, description="Whether role would create circular dependency")


# Update forward references
RoleDetailResponse.model_rebuild()