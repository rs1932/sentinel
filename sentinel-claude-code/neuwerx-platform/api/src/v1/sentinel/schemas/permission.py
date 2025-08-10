"""
Pydantic schemas for Module 6: Permissions
"""
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, root_validator, validator

# Enums represented as Literal for validation
PermissionAction = Literal["create","read","update","delete","execute","approve","reject"]
ResourceType = Literal["product_family","app","capability","service","entity","page","api"]
FieldPermissionType = Literal["read","write","hidden"]


class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    resource_type: ResourceType
    resource_id: Optional[UUID] = None
    resource_path: Optional[str] = Field(None, description="Wildcard path for resources, e.g., 'fleet/*'")
    actions: List[PermissionAction] = Field(..., min_items=1)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    field_permissions: Dict[str, List[FieldPermissionType]] = Field(default_factory=dict)
    is_active: bool = True

    @root_validator(skip_on_failure=True)
    def validate_resource_specification(cls, values):
        rid, rpath = values.get("resource_id"), values.get("resource_path")
        if (rid is None and rpath is None) or (rid is not None and rpath is not None):
            raise ValueError("Exactly one of resource_id or resource_path must be provided")
        return values


class PermissionCreateRequest(PermissionBase):
    """Permission creation request schema (tenant_id auto-populated from JWT)"""
    pass


class PermissionCreate(PermissionBase):
    """Internal permission creation schema (includes tenant_id)"""
    tenant_id: UUID


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    resource_id: Optional[UUID] = None
    resource_path: Optional[str] = None
    actions: Optional[List[PermissionAction]] = None
    conditions: Optional[Dict[str, Any]] = None
    field_permissions: Optional[Dict[str, List[FieldPermissionType]]] = None
    is_active: Optional[bool] = None

    @root_validator(skip_on_failure=True)
    def validate_resource_specification(cls, values):
        rid, rpath = values.get("resource_id"), values.get("resource_path")
        if rid is not None and rpath is not None:
            raise ValueError("Only one of resource_id or resource_path can be updated at a time")
        return values


class PermissionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    resource_type: str
    resource_id: Optional[UUID]
    resource_path: Optional[str]
    actions: List[str]
    conditions: Dict[str, Any]
    field_permissions: Dict[str, List[str]]
    is_active: bool

    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    items: List[PermissionResponse]
    total: int
    page: int = 1
    limit: int = 50


# Role-Permission operations
class RolePermissionAssignment(BaseModel):
    # Either reference an existing permission by ID or provide a definition to create
    permission_id: Optional[UUID] = None
    permission: Optional[PermissionCreate] = None

    @root_validator(skip_on_failure=True)
    def validate_choice(cls, values):
        pid, pdef = values.get("permission_id"), values.get("permission")
        if (pid is None and pdef is None) or (pid is not None and pdef is not None):
            raise ValueError("Provide exactly one of permission_id or permission definition")
        return values


class RolePermissionAssignmentRequest(BaseModel):
    permissions: List[RolePermissionAssignment] = Field(..., min_items=1)


class RolePermissionResponse(BaseModel):
    role_id: UUID
    permission: PermissionResponse
    granted_by: Optional[UUID] = None


class RolePermissionsListResponse(BaseModel):
    direct_permissions: List[PermissionResponse] = Field(default_factory=list)
    inherited_permissions: List[PermissionResponse] = Field(default_factory=list)
    effective_permissions: List[PermissionResponse] = Field(default_factory=list)

