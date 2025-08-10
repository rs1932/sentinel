"""
Pydantic schemas for Module 9: Menu/Navigation Management
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class MenuItemBase(BaseModel):
    """Base schema for menu item operations."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique menu item identifier")
    display_name: Optional[str] = Field(None, max_length=255, description="User-friendly display name")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name or class")
    url: Optional[str] = Field(None, max_length=500, description="Navigation URL")
    resource_id: Optional[UUID] = Field(None, description="Associated resource ID")
    required_permission: Optional[str] = Field(None, max_length=255, description="Required permission to view")
    display_order: int = Field(default=0, description="Display order within parent")
    is_visible: bool = Field(default=True, description="Whether the item is visible by default")
    menu_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('name')
    def validate_name(cls, v):
        """Validate menu item name format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Name must contain only alphanumeric characters, hyphens, and underscores")
        return v

    @field_validator('display_name')
    def validate_display_name(cls, v):
        """Validate display name if provided."""
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError("Display name cannot be empty")
        return v

    @field_validator('url')
    def validate_url(cls, v):
        """Validate URL format if provided."""
        if v is not None and v and not (v.startswith('/') or v.startswith('http')):
            raise ValueError("URL must be a valid path (starting with /) or full URL")
        return v


class MenuItemCreateRequest(MenuItemBase):
    """Schema for menu item creation request (tenant_id auto-populated from JWT)."""
    parent_id: Optional[UUID] = Field(None, description="Parent menu item ID for hierarchy")


class MenuItemCreate(MenuItemBase):
    """Internal schema for menu item creation (includes tenant_id)."""
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID (None for system-wide items)")
    parent_id: Optional[UUID] = Field(None, description="Parent menu item ID for hierarchy")


class MenuItemUpdate(BaseModel):
    """Schema for menu item updates."""
    display_name: Optional[str] = Field(None, max_length=255)
    icon: Optional[str] = Field(None, max_length=50)
    url: Optional[str] = Field(None, max_length=500)
    resource_id: Optional[UUID] = None
    required_permission: Optional[str] = Field(None, max_length=255)
    display_order: Optional[int] = None
    is_visible: Optional[bool] = None
    menu_metadata: Optional[Dict[str, Any]] = None

    @field_validator('display_name')
    def validate_display_name(cls, v):
        """Validate display name if provided."""
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError("Display name cannot be empty")
        return v

    @field_validator('url')
    def validate_url(cls, v):
        """Validate URL format if provided."""
        if v is not None and v and not (v.startswith('/') or v.startswith('http')):
            raise ValueError("URL must be a valid path (starting with /) or full URL")
        return v


class MenuItemResponse(BaseModel):
    """Schema for menu item API responses."""
    id: UUID
    tenant_id: Optional[UUID]
    parent_id: Optional[UUID]
    name: str
    display_name: Optional[str]
    icon: Optional[str]
    url: Optional[str]
    resource_id: Optional[UUID]
    required_permission: Optional[str]
    display_order: int
    is_visible: bool
    menu_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuItemWithChildren(MenuItemResponse):
    """Menu item response with children for hierarchical display."""
    children: List['MenuItemWithChildren'] = Field(default_factory=list, description="Child menu items")
    visible: bool = Field(default=True, description="Computed visibility for current user")


class UserMenuCustomizationBase(BaseModel):
    """Base schema for user menu customization."""
    is_hidden: bool = Field(default=False, description="Whether user has hidden this menu item")
    custom_order: Optional[int] = Field(None, description="User's custom display order")


class UserMenuCustomizationCreate(UserMenuCustomizationBase):
    """Schema for creating user menu customization."""
    menu_item_id: UUID = Field(..., description="Menu item to customize")


class UserMenuCustomizationUpdate(BaseModel):
    """Schema for updating user menu customization."""
    is_hidden: Optional[bool] = None
    custom_order: Optional[int] = None


class UserMenuCustomizationResponse(BaseModel):
    """Schema for user menu customization responses."""
    id: UUID
    user_id: UUID
    menu_item_id: UUID
    is_hidden: bool
    custom_order: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuQuery(BaseModel):
    """Schema for menu query parameters."""
    user_id: Optional[UUID] = Field(None, description="User ID (defaults to current user)")
    include_hidden: bool = Field(default=False, description="Include hidden items")
    parent_id: Optional[UUID] = Field(None, description="Filter by parent menu item")
    tenant_id: Optional[UUID] = Field(None, description="Filter by tenant")
    include_system_wide: bool = Field(default=True, description="Include system-wide menu items")


class MenuItemListResponse(BaseModel):
    """Schema for paginated menu item lists."""
    items: List[MenuItemResponse]
    total: int
    page: int = 1
    limit: int = 50
    has_next: bool = False
    has_prev: bool = False


class UserMenuResponse(BaseModel):
    """Schema for user menu structure response."""
    menu_items: List[MenuItemWithChildren] = Field(..., description="Hierarchical menu structure")
    user_id: UUID = Field(..., description="User ID this menu is for")
    customizations_applied: int = Field(default=0, description="Number of user customizations applied")


class MenuCustomizationBatch(BaseModel):
    """Schema for batch menu customization operations."""
    customizations: List[Dict[str, Any]] = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="List of menu customizations"
    )

    @field_validator('customizations')
    def validate_customizations(cls, v):
        """Validate customization entries."""
        required_fields = ['menu_item_id']
        for i, customization in enumerate(v):
            # Check required fields
            for field in required_fields:
                if field not in customization:
                    raise ValueError(f"Customization {i}: missing required field '{field}'")
            
            # Validate menu_item_id format
            try:
                UUID(str(customization['menu_item_id']))
            except (ValueError, TypeError):
                raise ValueError(f"Customization {i}: invalid menu_item_id format")
        
        return v


class MenuCustomizationBatchResponse(BaseModel):
    """Schema for batch customization responses."""
    applied: int = Field(..., description="Number of customizations applied successfully")
    failed: int = Field(default=0, description="Number of customizations that failed")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Errors during batch operation")


class MenuStatistics(BaseModel):
    """Schema for menu statistics."""
    total_items: int
    system_wide_items: int
    tenant_specific_items: int
    visible_items: int
    hidden_items: int
    items_with_permissions: int
    hierarchy_depth: int
    top_level_items: int


class MenuExport(BaseModel):
    """Schema for menu export operations."""
    format: str = Field(default="json", pattern="^(json|yaml)$", description="Export format")
    include_customizations: bool = Field(default=False, description="Include user customizations")
    tenant_id: Optional[UUID] = Field(None, description="Export specific tenant's menu items")


class MenuImport(BaseModel):
    """Schema for menu import operations."""
    menu_items: List[MenuItemCreateRequest] = Field(..., min_length=1, description="Menu items to import")
    overwrite_existing: bool = Field(default=False, description="Overwrite existing items with same name")
    validate_only: bool = Field(default=False, description="Only validate, don't import")


class MenuImportResult(BaseModel):
    """Schema for menu import results."""
    imported: int
    skipped: int
    errors: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[Dict[str, str]] = Field(default_factory=list)


# Update forward references for recursive model
MenuItemWithChildren.model_rebuild()