"""
Pydantic schemas for Module 7: Resource Management
"""
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator, model_validator
from datetime import datetime

from src.models.resource import ResourceType


class ResourceBase(BaseModel):
    """Base schema for resource operations."""
    name: str = Field(..., min_length=1, max_length=255, description="Resource name")
    code: str = Field(..., min_length=1, max_length=100, description="Unique identifier code")
    type: ResourceType = Field(..., description="Resource type")
    parent_id: Optional[UUID] = Field(None, description="Parent resource ID for hierarchy")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Resource-specific attributes")
    workflow_enabled: bool = Field(default=False, description="Enable workflow for this resource")
    workflow_config: Dict[str, Any] = Field(default_factory=dict, description="Workflow configuration")
    is_active: bool = Field(default=True, description="Resource active status")

    @validator('code')
    def validate_code(cls, v):
        """Validate resource code format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Code must contain only alphanumeric characters, hyphens, and underscores")
        return v

    @validator('type')
    def validate_type(cls, v):
        """Validate resource type."""
        if isinstance(v, str):
            try:
                return ResourceType(v)
            except ValueError:
                raise ValueError(f"Invalid resource type: {v}")
        return v


class ResourceCreateRequest(ResourceBase):
    """Schema for resource creation request (tenant_id auto-populated from JWT)."""
    pass


class ResourceCreate(ResourceBase):
    """Internal schema for resource creation (includes tenant_id)."""
    tenant_id: UUID = Field(..., description="Tenant ID")


class ResourceUpdate(BaseModel):
    """Schema for resource updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[UUID] = None
    attributes: Optional[Dict[str, Any]] = None
    workflow_enabled: Optional[bool] = None
    workflow_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @validator('name', pre=True, always=True)
    def validate_name(cls, v):
        """Validate name if provided."""
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError("Name cannot be empty")
        return v


class ResourceResponse(BaseModel):
    """Schema for resource API responses."""
    id: UUID
    tenant_id: UUID
    type: str
    name: str
    code: str
    parent_id: Optional[UUID]
    path: Optional[str]
    attributes: Dict[str, Any]
    workflow_enabled: bool
    workflow_config: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResourceDetailResponse(ResourceResponse):
    """Detailed resource response with additional computed fields."""
    depth: int = Field(..., description="Hierarchy depth (0 = root)")
    hierarchy_level_name: str = Field(..., description="Human-readable hierarchy level")
    ancestor_ids: List[str] = Field(default_factory=list, description="List of ancestor resource IDs")
    child_count: int = Field(default=0, description="Number of direct children")


class ResourceListResponse(BaseModel):
    """Schema for paginated resource lists."""
    items: List[ResourceResponse]
    total: int
    page: int = 1
    limit: int = 50
    has_next: bool = False
    has_prev: bool = False


class ResourceTreeNode(BaseModel):
    """Schema for hierarchical resource tree representation."""
    id: UUID
    type: str
    name: str
    code: str
    attributes: Dict[str, Any]
    is_active: bool
    children: List['ResourceTreeNode'] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Enable forward reference for recursive model
ResourceTreeNode.model_rebuild()


class ResourceTreeResponse(BaseModel):
    """Schema for resource tree/hierarchy responses."""
    tree: Union[ResourceTreeNode, List[ResourceTreeNode]]
    total_nodes: int = Field(..., description="Total number of nodes in the tree")
    max_depth: int = Field(..., description="Maximum depth of the tree")


class ResourceQuery(BaseModel):
    """Schema for resource query parameters."""
    type: Optional[ResourceType] = None
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    search: Optional[str] = Field(None, max_length=255, description="Search in name and code")
    include_children: bool = Field(default=False, description="Include child resources")
    max_depth: Optional[int] = Field(None, ge=1, le=10, description="Maximum depth for hierarchy queries")
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: str = Field(default="name", description="Sort field")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")

    @validator('search')
    def validate_search(cls, v):
        """Validate search term."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            if len(v) < 2:
                raise ValueError("Search term must be at least 2 characters")
        return v


class ResourcePermissionResponse(BaseModel):
    """Schema for resource permissions."""
    resource_id: UUID
    resource_name: str
    resource_type: str
    permissions: List[Dict[str, Any]] = Field(default_factory=list, description="Associated permissions")


class ResourceSearchResponse(BaseModel):
    """Schema for resource search results."""
    items: List[ResourceDetailResponse]
    total: int
    query: str
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")


class ResourceMoveRequest(BaseModel):
    """Schema for moving resources in the hierarchy."""
    new_parent_id: Optional[UUID] = Field(None, description="New parent ID (None for root level)")
    
    @model_validator(mode='before')
    def validate_move(cls, values):
        """Validate move operation."""
        # Additional validation can be added here
        return values


class ResourceBulkOperation(BaseModel):
    """Schema for bulk operations on resources."""
    resource_ids: List[UUID] = Field(..., min_items=1, max_items=100, description="List of resource IDs")
    operation: str = Field(..., pattern="^(activate|deactivate|delete)$", description="Bulk operation type")
    cascade: bool = Field(default=False, description="Apply operation to child resources")


class ResourceBulkResponse(BaseModel):
    """Schema for bulk operation responses."""
    operation: str
    processed: int
    failed: int
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Errors during bulk operation")


class ResourceStatistics(BaseModel):
    """Schema for resource statistics."""
    total_resources: int
    by_type: Dict[str, int] = Field(default_factory=dict)
    active_resources: int
    inactive_resources: int
    max_hierarchy_depth: int
    total_root_resources: int


class ResourceValidationError(BaseModel):
    """Schema for resource validation errors."""
    field: str
    message: str
    code: str