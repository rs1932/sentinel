"""
Resource Management API endpoints for Module 7

Provides RESTful API for resource management including:
- Resource CRUD operations
- Hierarchical resource management  
- Resource tree/hierarchy views
- Resource permissions
- Resource statistics
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.core.security_utils import get_current_user, require_scopes
from src.services.resource_service import ResourceService

# Helper function for single scope requirement
def require_scope(scope: str):
    return require_scopes(scope)

from src.schemas.resource import (
    ResourceCreateRequest, ResourceUpdate, ResourceQuery, ResourceResponse, 
    ResourceDetailResponse, ResourceListResponse, ResourceTreeResponse,
    ResourcePermissionResponse, ResourceStatistics, ResourceMoveRequest
)
from src.core.exceptions import ValidationError, NotFoundError, ConflictError


router = APIRouter(prefix="/resources", tags=["Resource Management"])


@router.post(
    "/",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("resource:write"))],
    summary="Create a new resource",
    description="Create a new resource with hierarchy validation"
)
async def create_resource(
    resource_data: ResourceCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResourceResponse:
    """Create a new resource."""
    try:
        from src.schemas.resource import ResourceCreate
        
        # Convert request to internal schema with tenant_id
        resource_create = ResourceCreate(
            **resource_data.model_dump(),
            tenant_id=current_user.tenant_id
        )
        
        service = ResourceService(db)
        return await service.create_resource(resource_create)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "/",
    response_model=ResourceListResponse,
    dependencies=[Depends(require_scope("resource:read"))],
    summary="List resources",
    description="List resources with filtering, search, and pagination"
)
async def list_resources(
    type: Optional[str] = Query(None, description="Filter by resource type"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent resource ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and code"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResourceListResponse:
    """List resources with filtering and pagination."""
    from src.models.resource import ResourceType
    
    # Convert string type to enum if provided
    resource_type = None
    if type:
        try:
            resource_type = ResourceType(type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid resource type: {type}")
    
    query = ResourceQuery(
        type=resource_type,
        parent_id=parent_id,
        is_active=is_active,
        search=search,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    service = ResourceService(db)
    
    # Check if user has global resource access
    has_global_access = hasattr(current_user, 'scopes') and 'resource:global' in current_user.scopes
    tenant_id = None if has_global_access else current_user.tenant_id
    
    return await service.list_resources(
        tenant_id=tenant_id,
        query=query
    )


@router.get(
    "/tree",
    response_model=ResourceTreeResponse,
    dependencies=[Depends(require_scope("resource:read"))],
    summary="Get resource tree/hierarchy",
    description="Get hierarchical resource tree structure"
)
async def get_resource_tree(
    root_id: Optional[UUID] = Query(None, description="Root resource ID (optional, returns all if not specified)"),
    max_depth: Optional[int] = Query(None, ge=1, le=10, description="Maximum depth to traverse"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResourceTreeResponse:
    """Get resource tree/hierarchy."""
    try:
        service = ResourceService(db)
        
        # Check if user has global resource access
        has_global_access = hasattr(current_user, 'scopes') and 'resource:global' in current_user.scopes
        tenant_id = None if has_global_access else current_user.tenant_id
        
        return await service.get_resource_tree(
            tenant_id=tenant_id,
            root_id=root_id,
            max_depth=max_depth
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/statistics",
    response_model=ResourceStatistics,
    dependencies=[Depends(require_scope("resource:read"))],
    summary="Get resource statistics",
    description="Get resource statistics for the tenant"
)
async def get_resource_statistics(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResourceStatistics:
    """Get resource statistics."""
    service = ResourceService(db)
    
    # Check if user has global resource access
    has_global_access = hasattr(current_user, 'scopes') and 'resource:global' in current_user.scopes
    tenant_id = None if has_global_access else current_user.tenant_id
    
    return await service.get_resource_statistics(tenant_id)


@router.get(
    "/{resource_id}",
    response_model=ResourceDetailResponse,
    dependencies=[Depends(require_scope("resource:read"))],
    summary="Get resource details",
    description="Get detailed resource information including hierarchy metadata"
)
async def get_resource(
    resource_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResourceDetailResponse:
    """Get resource details by ID."""
    try:
        service = ResourceService(db)
        return await service.get_resource_detail(
            resource_id=resource_id,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch(
    "/{resource_id}",
    response_model=ResourceResponse,
    dependencies=[Depends(require_scope("resource:write"))],
    summary="Update resource",
    description="Update resource information with hierarchy validation"
)
async def update_resource(
    resource_id: UUID,
    resource_data: ResourceUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResourceResponse:
    """Update an existing resource."""
    try:
        service = ResourceService(db)
        return await service.update_resource(
            resource_id=resource_id,
            tenant_id=current_user.tenant_id,
            update_data=resource_data
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("resource:admin"))],
    summary="Delete resource",
    description="Soft delete a resource with optional cascade"
)
async def delete_resource(
    resource_id: UUID,
    cascade: bool = Query(False, description="Delete child resources as well"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a resource (soft delete)."""
    try:
        service = ResourceService(db)
        await service.delete_resource(
            resource_id=resource_id,
            tenant_id=current_user.tenant_id,
            cascade=cascade
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{resource_id}/move",
    response_model=ResourceResponse,
    dependencies=[Depends(require_scope("resource:write"))],
    summary="Move resource in hierarchy",
    description="Move a resource to a different parent in the hierarchy"
)
async def move_resource(
    resource_id: UUID,
    move_data: ResourceMoveRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResourceResponse:
    """Move a resource to a different parent."""
    try:
        # Convert to update with parent_id change
        update_data = ResourceUpdate(parent_id=move_data.new_parent_id)
        
        service = ResourceService(db)
        return await service.update_resource(
            resource_id=resource_id,
            tenant_id=current_user.tenant_id,
            update_data=update_data
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{resource_id}/permissions",
    response_model=ResourcePermissionResponse,
    dependencies=[Depends(require_scope("resource:read"))],
    summary="Get resource permissions",
    description="Get all permissions associated with a resource"
)
async def get_resource_permissions(
    resource_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResourcePermissionResponse:
    """Get permissions associated with a resource."""
    try:
        service = ResourceService(db)
        return await service.get_resource_permissions(
            resource_id=resource_id,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{resource_id}/children",
    response_model=ResourceListResponse,
    dependencies=[Depends(require_scope("resource:read"))],
    summary="Get child resources",
    description="Get direct child resources of a specific resource"
)
async def get_child_resources(
    resource_id: UUID,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResourceListResponse:
    """Get child resources of a specific resource."""
    # Use the list_resources method with parent_id filter
    query = ResourceQuery(
        parent_id=resource_id,
        is_active=is_active,
        page=page,
        limit=limit
    )
    
    service = ResourceService(db)
    return await service.list_resources(
        tenant_id=current_user.tenant_id,
        query=query
    )