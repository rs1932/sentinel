"""
Permission management API endpoints for Module 6
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.permission_service import PermissionService
from src.schemas.permission import (
    PermissionCreateRequest, PermissionCreate, PermissionUpdate, PermissionResponse, PermissionListResponse
)
from src.core.security_utils import require_scopes, CurrentUser
from src.core.exceptions import NotFoundError, ConflictError, ValidationError


router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.post("/", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_request: PermissionCreateRequest,
    current_user: CurrentUser = Depends(require_scopes("permission:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new permission definition.
    
    Requires:
    - JWT authentication
    - permission:admin scope
    """
    try:
        # Create internal permission data with tenant_id from current user
        permission_data = PermissionCreate(
            tenant_id=current_user.tenant_id,
            **permission_request.model_dump()
        )
        
        service = PermissionService(db)
        return await service.create_permission(permission_data)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create permission")


@router.get("/", response_model=PermissionListResponse)
async def list_permissions(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by permission name"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    current_user: CurrentUser = Depends(require_scopes("permission:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    List permissions with filtering and pagination.
    
    Requires:
    - JWT authentication  
    - permission:read scope
    """
    try:
        service = PermissionService(db)
        
        # Check if user has global permission access
        has_global_access = hasattr(current_user, 'scopes') and 'permission:global' in current_user.scopes
        tenant_id = None if has_global_access else current_user.tenant_id
        
        return await service.list_permissions(
            tenant_id=tenant_id,
            resource_type=resource_type,
            is_active=is_active,
            search=search,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list permissions")


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: UUID,
    current_user: CurrentUser = Depends(require_scopes("permission:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific permission by ID.
    
    Requires:
    - JWT authentication
    - permission:read scope
    """
    try:
        service = PermissionService(db)
        return await service.get_permission(permission_id, current_user.tenant_id)
        
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get permission")


@router.patch("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: UUID,
    permission_data: PermissionUpdate,
    current_user: CurrentUser = Depends(require_scopes("permission:write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a specific permission.
    
    Requires:
    - JWT authentication
    - permission:write scope
    """
    try:
        service = PermissionService(db)
        return await service.update_permission(permission_id, current_user.tenant_id, permission_data)
        
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update permission")


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: UUID,
    current_user: CurrentUser = Depends(require_scopes("permission:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific permission.
    
    Requires:
    - JWT authentication  
    - permission:admin scope
    """
    try:
        service = PermissionService(db)
        success = await service.delete_permission(permission_id, current_user.tenant_id)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
            
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete permission")


