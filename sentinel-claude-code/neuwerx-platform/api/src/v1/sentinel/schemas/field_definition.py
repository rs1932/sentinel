"""
Pydantic schemas for Module 8: Field Definition Management
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from datetime import datetime

from ..models.field_definition_types import FieldType, FieldDataType, FieldPermission


class FieldDefinitionBase(BaseModel):
    """Base schema for field definition operations."""
    entity_type: str = Field(..., min_length=1, max_length=100, description="Entity type (e.g., vessel, container)")
    field_name: str = Field(..., min_length=1, max_length=100, description="Field name")
    field_type: str = Field(..., description="Field type: core, platform_dynamic, or tenant_specific")
    data_type: str = Field(..., description="Data type of the field")
    storage_column: Optional[str] = Field(None, max_length=100, description="Database column name for core fields")
    storage_path: Optional[str] = Field(None, max_length=255, description="JSON path for dynamic fields")
    display_name: Optional[str] = Field(None, max_length=255, description="Human-readable field name")
    description: Optional[str] = Field(None, description="Field description")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules as JSON")
    default_visibility: str = Field(default="read", description="Default field visibility: read, write, or hidden")
    is_indexed: bool = Field(default=False, description="Whether field should be indexed")
    is_required: bool = Field(default=False, description="Whether field is required")
    is_active: bool = Field(default=True, description="Whether field definition is active")

    @validator('field_type')
    def validate_field_type(cls, v):
        """Validate field type."""
        valid_types = [e.value for e in FieldType]
        if v not in valid_types:
            raise ValueError(f"Invalid field type. Must be one of: {', '.join(valid_types)}")
        return v

    @validator('data_type')
    def validate_data_type(cls, v):
        """Validate data type."""
        valid_types = [e.value for e in FieldDataType]
        if v not in valid_types:
            raise ValueError(f"Invalid data type. Must be one of: {', '.join(valid_types)}")
        return v

    @validator('default_visibility')
    def validate_default_visibility(cls, v):
        """Validate default visibility."""
        valid_permissions = [e.value for e in FieldPermission]
        if v not in valid_permissions:
            raise ValueError(f"Invalid visibility. Must be one of: {', '.join(valid_permissions)}")
        return v

    @validator('field_name')
    def validate_field_name(cls, v):
        """Validate field name format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Field name must contain only alphanumeric characters, hyphens, and underscores")
        # Ensure field name doesn't conflict with reserved words
        reserved_words = ['metadata', 'meta_data', 'id', 'created_at', 'updated_at']
        if v.lower() in reserved_words:
            raise ValueError(f"Field name '{v}' is reserved and cannot be used")
        return v

    @validator('entity_type')
    def validate_entity_type(cls, v):
        """Validate entity type format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Entity type must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()


class FieldDefinitionCreateRequest(FieldDefinitionBase):
    """Schema for field definition creation request (tenant_id auto-populated from JWT)."""

    @validator('storage_column', 'storage_path')
    def validate_storage_config(cls, v, values):
        """Validate storage configuration based on field type."""
        field_type = values.get('field_type')
        if not field_type:
            return v

        if field_type == FieldType.CORE.value:
            if 'storage_column' in values and not values.get('storage_column'):
                raise ValueError("storage_column is required for core fields")
            if 'storage_path' in values and values.get('storage_path'):
                raise ValueError("storage_path should not be set for core fields")
        else:  # platform_dynamic or tenant_specific
            if 'storage_path' in values and not values.get('storage_path'):
                raise ValueError("storage_path is required for dynamic fields")
            if 'storage_column' in values and values.get('storage_column'):
                raise ValueError("storage_column should not be set for dynamic fields")
        return v


class FieldDefinitionCreate(FieldDefinitionBase):
    """Internal schema for field definition creation (includes tenant_id)."""
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID (None for platform-wide fields)")


class FieldDefinitionUpdate(BaseModel):
    """Schema for field definition updates."""
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    default_visibility: Optional[str] = None
    is_indexed: Optional[bool] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None

    @validator('default_visibility')
    def validate_default_visibility(cls, v):
        """Validate default visibility if provided."""
        if v is not None:
            valid_permissions = [e.value for e in FieldPermission]
            if v not in valid_permissions:
                raise ValueError(f"Invalid visibility. Must be one of: {', '.join(valid_permissions)}")
        return v

    @validator('display_name')
    def validate_display_name(cls, v):
        """Validate display name if provided."""
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError("Display name cannot be empty")
        return v


class FieldDefinitionResponse(BaseModel):
    """Schema for field definition API responses."""
    id: UUID
    tenant_id: Optional[UUID]
    entity_type: str
    field_name: str
    field_type: str
    data_type: str
    storage_column: Optional[str]
    storage_path: Optional[str]
    display_name: Optional[str]
    description: Optional[str]
    validation_rules: Dict[str, Any]
    default_visibility: str
    is_indexed: bool
    is_required: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FieldDefinitionDetailResponse(FieldDefinitionResponse):
    """Detailed field definition response with additional computed fields."""
    is_platform_wide: bool = Field(..., description="Whether this is a platform-wide field definition")
    full_field_path: str = Field(..., description="Full field path for JSON storage")
    storage_info: Dict[str, Any] = Field(..., description="Storage configuration information")


class FieldDefinitionListResponse(BaseModel):
    """Schema for paginated field definition lists."""
    items: List[FieldDefinitionResponse]
    total: int
    page: int = 1
    limit: int = 50
    has_next: bool = False
    has_prev: bool = False


class FieldDefinitionQuery(BaseModel):
    """Schema for field definition query parameters."""
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    field_type: Optional[str] = Field(None, description="Filter by field type")
    tenant_id: Optional[UUID] = Field(None, description="Filter by tenant (for tenant-specific fields)")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, max_length=255, description="Search in field name and display name")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: str = Field(default="field_name", description="Sort field")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")

    @validator('field_type')
    def validate_field_type(cls, v):
        """Validate field type if provided."""
        if v is not None:
            valid_types = [e.value for e in FieldType]
            if v not in valid_types:
                raise ValueError(f"Invalid field type. Must be one of: {', '.join(valid_types)}")
        return v

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


class FieldPermissionCheck(BaseModel):
    """Schema for field permission checking."""
    user_id: UUID = Field(..., description="User ID to check permissions for")
    entity_type: str = Field(..., description="Entity type")
    entity_id: Optional[str] = Field(None, description="Specific entity instance ID")
    fields: List[str] = Field(..., min_items=1, description="List of field names to check")


class FieldPermissionResponse(BaseModel):
    """Schema for field permission check results."""
    field_permissions: Dict[str, List[str]] = Field(..., description="Field permissions mapping")
    user_id: UUID
    entity_type: str
    entity_id: Optional[str]
    checked_fields: List[str]


class FieldValidationError(BaseModel):
    """Schema for field validation errors."""
    field: str
    message: str
    code: str


class FieldDefinitionBulkOperation(BaseModel):
    """Schema for bulk operations on field definitions."""
    field_definition_ids: List[UUID] = Field(
        ..., min_items=1, max_items=100, description="List of field definition IDs"
    )
    operation: str = Field(..., pattern="^(activate|deactivate|delete)$", description="Bulk operation type")


class FieldDefinitionBulkResponse(BaseModel):
    """Schema for bulk operation responses."""
    operation: str
    processed: int
    failed: int
    errors: List[Dict[str, str]] = Field(
        default_factory=list, description="Errors during bulk operation"
    )


class FieldDefinitionStatistics(BaseModel):
    """Schema for field definition statistics."""
    total_definitions: int
    by_entity_type: Dict[str, int] = Field(default_factory=dict)
    by_field_type: Dict[str, int] = Field(default_factory=dict)
    by_data_type: Dict[str, int] = Field(default_factory=dict)
    active_definitions: int
    inactive_definitions: int
    platform_wide_definitions: int
    tenant_specific_definitions: int


class FieldDefinitionExport(BaseModel):
    """Schema for field definition export."""
    format: str = Field(default="json", pattern="^(json|csv|yaml)$", description="Export format")
    entity_types: Optional[List[str]] = Field(None, description="Filter by entity types")
    field_types: Optional[List[str]] = Field(None, description="Filter by field types")
    include_inactive: bool = Field(default=False, description="Include inactive field definitions")


class FieldDefinitionImport(BaseModel):
    """Schema for field definition import."""
    definitions: List[FieldDefinitionCreateRequest] = Field(..., min_items=1, description="Field definitions to import")
    overwrite_existing: bool = Field(default=False, description="Overwrite existing definitions")
    validate_only: bool = Field(default=False, description="Only validate, don't import")


class FieldDefinitionImportResult(BaseModel):
    """Schema for field definition import results."""
    imported: int
    skipped: int
    errors: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[Dict[str, str]] = Field(default_factory=list)
