"""
Pydantic schemas for Group Management (Module 5)
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID


class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None)
    parent_group_id: Optional[UUID] = Field(None, description="Parent group ID for hierarchy")
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="group_metadata")
    is_active: bool = Field(True)

    @validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Group name cannot be empty")
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError("Group name can only contain letters, numbers, hyphens, underscores, and periods")
        return v.strip().lower()


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    parent_group_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="group_metadata")
    is_active: Optional[bool] = None


class GroupQuery(BaseModel):
    tenant_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    parent_group_id: Optional[UUID] = None
    search: Optional[str] = Field(None, description="Search in name and display_name")

    # Pagination
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)

    # Sorting
    sort_by: str = Field("name")
    sort_order: str = Field("asc", pattern="^(asc|desc)$")


class GroupResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    parent_group_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="group_metadata")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class GroupDetailResponse(GroupResponse):
    # Optional richer data for later increment (counts, hierarchy)
    child_groups: List["GroupResponse"] = Field(default_factory=list)


class GroupListResponse(BaseModel):
    items: List[GroupResponse]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True
        populate_by_name = True


class GroupUserAddRequest(BaseModel):
    user_ids: List[UUID] = Field(..., min_items=1, max_items=100)


class GroupRoleAssignRequest(BaseModel):
    role_ids: List[UUID] = Field(..., min_items=1, max_items=50)


# Resolve forward refs
GroupDetailResponse.model_rebuild()

