"""
Role Management API endpoints for Module 4

Provides RESTful API for role management including:
- Role CRUD operations
- Role hierarchy management
- User-role assignments
- Role validation
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.core.security_utils import get_current_user, require_scopes
from src.services.role_service import RoleService

# Helper function for single scope requirement
def require_scope(scope: str):
    return require_scopes(scope)
from src.schemas.role import (
    RoleCreate, RoleUpdate, RoleQuery, RoleResponse, RoleDetailResponse,
    RoleListResponse, UserRoleAssignmentCreate, UserRoleAssignmentResponse,
    BulkRoleAssignmentRequest, BulkRoleAssignmentResponse, RoleHierarchyResponse,
    RoleValidationResponse
)
from src.core.exceptions import ValidationError, NotFoundError, ConflictError


router = APIRouter(prefix="/roles", tags=["Role Management"])


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("role:admin"))],
    summary="Create a new role",
    description="Create a new role with hierarchy support and validation"
)
async def create_role(
    role_data: RoleCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RoleResponse:
    """Create a new role."""
    try:
        service = RoleService(db)
        return await service.create_role(
            role_data=role_data,
            tenant_id=current_user.tenant_id,
            created_by=current_user.user_id
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "/",
    response_model=RoleListResponse,
    dependencies=[Depends(require_scope("role:read"))],
    summary="List roles",
    description="List roles with filtering, search, and pagination"
)
async def list_roles(
    type: Optional[str] = Query(None, description="Filter by role type (system/custom)"),
    is_assignable: Optional[bool] = Query(None, description="Filter by assignable status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_role_id: Optional[UUID] = Query(None, description="Filter by parent role ID"),
    search: Optional[str] = Query(None, description="Search in name and display_name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    sort_by: str = Query("name", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RoleListResponse:
    """List roles with filtering and pagination."""
    query = RoleQuery(
        type=type,
        is_assignable=is_assignable,
        is_active=is_active,
        parent_role_id=parent_role_id,
        search=search,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    service = RoleService(db)
    return await service.list_roles(
        query=query,
        tenant_id=current_user.tenant_id
    )


@router.get(
    "/{role_id}",
    response_model=RoleDetailResponse,
    dependencies=[Depends(require_scope("role:read"))],
    summary="Get role details",
    description="Get detailed role information including hierarchy and assignments"
)
async def get_role(
    role_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RoleDetailResponse:
    """Get role details by ID."""
    try:
        service = RoleService(db)
        return await service.get_role(
            role_id=role_id,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_scope("role:write"))],
    summary="Update role",
    description="Update role information with hierarchy validation"
)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RoleResponse:
    """Update an existing role."""
    try:
        service = RoleService(db)
        return await service.update_role(
            role_id=role_id,
            role_data=role_data,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("role:admin"))],
    summary="Delete role",
    description="Soft delete a role with dependency validation"
)
async def delete_role(
    role_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a role (soft delete)."""
    try:
        service = RoleService(db)
        await service.delete_role(
            role_id=role_id,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{role_id}/hierarchy",
    response_model=RoleHierarchyResponse,
    dependencies=[Depends(require_scope("role:read"))],
    summary="Get role hierarchy",
    description="Get complete role hierarchy including ancestors and descendants"
)
async def get_role_hierarchy(
    role_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RoleHierarchyResponse:
    """Get role hierarchy information."""
    try:
        service = RoleService(db)
        return await service.get_role_hierarchy(
            role_id=role_id,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{role_id}/users",
    response_model=UserRoleAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("role:admin"))],
    summary="Assign role to user",
    description="Assign a role to a user with optional expiration"
)
async def assign_role_to_user(
    role_id: UUID,
    assignment: UserRoleAssignmentCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserRoleAssignmentResponse:
    """Assign a role to a user."""
    # Ensure the role_id matches the URL parameter
    assignment.role_id = role_id
    
    try:
        service = RoleService(db)
        return await service.assign_role_to_user(
            assignment=assignment,
            tenant_id=current_user.tenant_id,
            granted_by=current_user.user_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{role_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("role:admin"))],
    summary="Remove role from user",
    description="Remove a role assignment from a user"
)
async def remove_role_from_user(
    role_id: UUID,
    user_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove role assignment from user."""
    # This would be implemented when we add user role removal methods
    # For now, return a 501 Not Implemented
    raise HTTPException(
        status_code=501,
        detail="Role removal functionality will be implemented in next iteration"
    )


@router.get(
    "/{role_id}/users",
    response_model=List[UserRoleAssignmentResponse],
    dependencies=[Depends(require_scope("role:read"))],
    summary="Get role assignments",
    description="Get all user assignments for a specific role"
)
async def get_role_assignments(
    role_id: UUID,
    is_active: Optional[bool] = Query(True, description="Filter by assignment status"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[UserRoleAssignmentResponse]:
    """Get all user assignments for a role."""
    # This would be implemented when we add role assignment listing methods
    # For now, return a 501 Not Implemented
    raise HTTPException(
        status_code=501,
        detail="Role assignment listing will be implemented in next iteration"
    )


@router.post(
    "/bulk-assign",
    response_model=BulkRoleAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("role:admin"))],
    summary="Bulk role assignment",
    description="Assign multiple roles to multiple users in a single operation"
)
async def bulk_assign_roles(
    assignment: BulkRoleAssignmentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BulkRoleAssignmentResponse:
    """Bulk assign roles to users."""
    # This would be implemented when we add bulk assignment methods
    # For now, return a 501 Not Implemented
    raise HTTPException(
        status_code=501,
        detail="Bulk role assignment will be implemented in next iteration"
    )


@router.post(
    "/validate",
    response_model=RoleValidationResponse,
    dependencies=[Depends(require_scope("role:write"))],
    summary="Validate role hierarchy",
    description="Validate a role hierarchy change for circular dependencies"
)
async def validate_role_hierarchy(
    role_id: Optional[UUID] = Query(None, description="Existing role ID (null for new roles)"),
    parent_role_id: Optional[UUID] = Query(None, description="Proposed parent role ID"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RoleValidationResponse:
    """Validate role hierarchy for circular dependencies."""
    service = RoleService(db)
    return await service.validate_role_hierarchy(
        role_id=role_id,
        parent_role_id=parent_role_id,
        tenant_id=current_user.tenant_id
    )