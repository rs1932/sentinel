"""
User management API endpoints for Module 3
Handles user CRUD operations with JWT authentication and scope-based authorization
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..core.security_utils import get_current_user, require_scopes, CurrentUser
from ..services.user_service import UserService
from ..schemas.user import (
    UserCreate, UserUpdate, UserQuery, UserResponse, UserDetailResponse,
    UserListResponse, UserPermissionsResponse, UserBulkOperation, 
    BulkOperationResponse, PasswordChange, AdminPasswordReset, SortField, SortOrder
)
from ..core.exceptions import (
    NotFoundError, ValidationError, ConflictError, AuthenticationError
)
from uuid import UUID

router = APIRouter(tags=["users"])
security = HTTPBearer()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile information
    
    Returns the authenticated user's profile data
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user(current_user.user_id, current_user.tenant_id)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information
    
    Users can update their own profile data
    """
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(
            user_id=current_user.user_id,
            user_data=user_data,
            updated_by=current_user.user_id
        )
        return updated_user
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update user profile")


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: CurrentUser = Depends(require_scopes("user:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user
    
    Required scope: user:admin
    """
    try:
        user_service = UserService(db)
        return await user_service.create_user(
            user_data=user_data,
            tenant_id=current_user.tenant_id,
            creator_id=current_user.user_id
        )
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=UserListResponse)
async def list_users(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant ID"),
    role: Optional[str] = Query(None, description="Filter by role name"),
    group: Optional[str] = Query(None, description="Filter by group name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by email/username"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    sort: SortField = Query(SortField.created_at, description="Sort field"),
    order: SortOrder = Query(SortOrder.desc, description="Sort order"),
    current_user: CurrentUser = Depends(require_scopes("user:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    List users with filtering and pagination
    
    Required scope: user:read
    """
    user_service = UserService(db)
    
    # Build query parameters
    query_params = UserQuery(
        tenant_id=tenant_id,
        role=role,
        group=group,
        is_active=is_active,
        search=search,
        page=page,
        limit=limit,
        sort=sort,
        order=order
    )
    
    return await user_service.list_users(
        query_params=query_params,
        tenant_id=current_user.tenant_id
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    current_user: CurrentUser = Depends(require_scopes("user:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user details by ID
    
    Required scope: user:read
    """
    try:
        user_service = UserService(db)
        return await user_service.get_user(
            user_id=user_id,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: CurrentUser = Depends(require_scopes("user:write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user information
    
    Required scope: user:write
    """
    try:
        user_service = UserService(db)
        return await user_service.update_user(
            user_id=user_id,
            user_data=user_data,
            tenant_id=current_user.tenant_id,
            updater_id=current_user.user_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    hard_delete: bool = Query(False, description="Perform hard delete instead of soft delete"),
    current_user: CurrentUser = Depends(require_scopes("user:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (soft delete by default)
    
    Required scope: user:admin
    """
    try:
        user_service = UserService(db)
        await user_service.delete_user(
            user_id=user_id,
            tenant_id=current_user.tenant_id,
            soft_delete=not hard_delete
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_user_operations(
    bulk_data: UserBulkOperation,
    current_user: CurrentUser = Depends(require_scopes("user:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform bulk operations on users
    
    Required scope: user:admin
    """
    try:
        user_service = UserService(db)
        return await user_service.bulk_operation(
            bulk_data=bulk_data,
            tenant_id=current_user.tenant_id,
            operator_id=current_user.user_id
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{user_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: UUID,
    current_user: CurrentUser = Depends(require_scopes("user:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user permissions (placeholder for future role integration)
    
    Required scope: user:read
    """
    try:
        user_service = UserService(db)
        return await user_service.get_user_permissions(
            user_id=user_id,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{user_id}/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_password(
    user_id: UUID,
    password_data: PasswordChange,
    current_user: CurrentUser = Depends(require_scopes("user:write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password
    
    Required scope: user:write
    Note: Users can only change their own password unless they have user:admin scope
    """
    # Check if user is changing their own password or has admin rights
    if user_id != current_user.user_id:
        # Require admin scope to change other users' passwords
        current_user_admin = Depends(require_scopes("user:admin"))
        await current_user_admin(current_user)
    
    try:
        user_service = UserService(db)
        await user_service.change_password(
            user_id=user_id,
            password_data=password_data,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{user_id}/admin-reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def admin_reset_user_password(
    user_id: UUID,
    password_data: AdminPasswordReset,
    current_user: CurrentUser = Depends(require_scopes("user:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin password reset - doesn't require current password
    
    Required scope: user:admin
    Allows administrators to directly set a new password for any user
    """
    try:
        user_service = UserService(db)
        await user_service.admin_reset_password(
            user_id=user_id,
            new_password=password_data.new_password,
            tenant_id=current_user.tenant_id,
            admin_user_id=current_user.user_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{user_id}/lock", status_code=status.HTTP_204_NO_CONTENT)
async def lock_user(
    user_id: UUID,
    duration_minutes: int = Query(30, ge=1, le=1440, description="Lock duration in minutes (max 24 hours)"),
    current_user: CurrentUser = Depends(require_scopes("user:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Lock user account for specified duration
    
    Required scope: user:admin
    """
    try:
        user_service = UserService(db)
        await user_service.lock_user(
            user_id=user_id,
            duration_minutes=duration_minutes,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{user_id}/unlock", status_code=status.HTTP_204_NO_CONTENT)
async def unlock_user(
    user_id: UUID,
    current_user: CurrentUser = Depends(require_scopes("user:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Unlock user account
    
    Required scope: user:admin
    """
    try:
        user_service = UserService(db)
        await user_service.unlock_user(
            user_id=user_id,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))