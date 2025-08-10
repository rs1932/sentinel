"""
Navigation/Menu Management API endpoints for Module 9

Provides RESTful API for menu navigation management including:
- Hierarchical menu structure retrieval
- User menu customization
- Menu item CRUD operations (admin only)
- Permission-based menu visibility
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..core.security_utils import get_current_user, require_scopes
from ..services.menu_service import MenuService
from ..schemas.menu import (
    MenuItemCreateRequest, MenuItemUpdate, MenuQuery,
    MenuItemResponse, MenuItemListResponse, UserMenuResponse,
    MenuCustomizationBatch, MenuCustomizationBatchResponse,
    UserMenuCustomizationResponse, MenuStatistics
)
from ..schemas import MenuItemCreate
from ..core.exceptions import ValidationError, NotFoundError, ConflictError


# Helper function for single scope requirement
def require_scope(scope: str):
    return require_scopes(scope)


router = APIRouter(tags=["Navigation Management"])


@router.get(
    "/menu",
    response_model=UserMenuResponse,
    dependencies=[Depends(require_scope("navigation:read"))],
    summary="Get user menu structure",
    description="Get hierarchical menu structure for the current user with customizations applied"
)
async def get_user_menu(
    user_id: Optional[UUID] = Query(None, description="User ID (defaults to current user)"),
    include_hidden: bool = Query(False, description="Include hidden menu items"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserMenuResponse:
    """Get hierarchical menu structure for a user."""
    try:
        # Use current user if no user_id specified
        target_user_id = user_id if user_id else current_user.id
        
        # Only allow users to access their own menu unless admin
        if target_user_id != current_user.id:
            # Check if current user has admin permissions
            try:
                await require_scope("navigation:admin")(current_user=current_user)
            except HTTPException:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot access another user's menu without admin permissions"
                )
        
        service = MenuService(db)
        return await service.get_user_menu(
            user_id=target_user_id,
            include_hidden=include_hidden,
            tenant_id=current_user.tenant_id
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/customize",
    response_model=MenuCustomizationBatchResponse,
    dependencies=[Depends(require_scope("navigation:write"))],
    summary="Customize user menu",
    description="Apply batch customizations to the current user's menu"
)
async def customize_user_menu(
    customization_data: MenuCustomizationBatch,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MenuCustomizationBatchResponse:
    """Apply batch customizations to user menu."""
    try:
        service = MenuService(db)
        result = await service.customize_user_menu(
            user_id=current_user.id,
            customizations=customization_data.customizations
        )
        
        return MenuCustomizationBatchResponse(
            applied=result["applied"],
            failed=result["failed"],
            errors=[]
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Admin endpoints for menu management
@router.post(
    "/menu-items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("navigation:admin"))],
    summary="Create menu item",
    description="Create a new menu item (admin only)"
)
async def create_menu_item(
    item_data: MenuItemCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MenuItemResponse:
    """Create a new menu item."""
    try:
        # Convert request to internal create schema with tenant_id
        menu_item_create = MenuItemCreate(
            tenant_id=current_user.tenant_id,
            **item_data.model_dump()
        )
        
        service = MenuService(db)
        return await service.create_menu_item(menu_item_create)
        
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/menu-items",
    response_model=MenuItemListResponse,
    dependencies=[Depends(require_scope("navigation:read"))],
    summary="List menu items",
    description="Get a paginated list of menu items with filtering options"
)
async def list_menu_items(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent menu item"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    include_system_wide: bool = Query(True, description="Include system-wide menu items"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MenuItemListResponse:
    """List menu items with filtering and pagination."""
    try:
        # Use current user's tenant if not specified
        filter_tenant_id = tenant_id if tenant_id else current_user.tenant_id
        
        service = MenuService(db)
        return await service.list_menu_items(
            page=page,
            limit=limit,
            parent_id=parent_id,
            tenant_id=filter_tenant_id,
            include_system_wide=include_system_wide
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/menu-items/{item_id}",
    response_model=MenuItemResponse,
    dependencies=[Depends(require_scope("navigation:read"))],
    summary="Get menu item details",
    description="Get detailed information about a specific menu item"
)
async def get_menu_item(
    item_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MenuItemResponse:
    """Get menu item by ID."""
    try:
        service = MenuService(db)
        return await service.get_menu_item(item_id)
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch(
    "/menu-items/{item_id}",
    response_model=MenuItemResponse,
    dependencies=[Depends(require_scope("navigation:admin"))],
    summary="Update menu item",
    description="Update an existing menu item (admin only)"
)
async def update_menu_item(
    item_id: UUID,
    item_data: MenuItemUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MenuItemResponse:
    """Update menu item."""
    try:
        service = MenuService(db)
        return await service.update_menu_item(item_id, item_data)
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/menu-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("navigation:admin"))],
    summary="Delete menu item",
    description="Delete a menu item and its children (admin only)"
)
async def delete_menu_item(
    item_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete menu item."""
    try:
        service = MenuService(db)
        await service.delete_menu_item(item_id)
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/statistics",
    response_model=MenuStatistics,
    dependencies=[Depends(require_scope("navigation:read"))],
    summary="Get menu statistics",
    description="Get statistics about menu items and structure"
)
async def get_menu_statistics(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MenuStatistics:
    """Get menu statistics."""
    try:
        service = MenuService(db)
        return await service.get_menu_statistics(current_user.tenant_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# User menu customization endpoints
@router.get(
    "/customizations/{menu_item_id}",
    response_model=Optional[UserMenuCustomizationResponse],
    dependencies=[Depends(require_scope("navigation:read"))],
    summary="Get user menu customization",
    description="Get the current user's customization for a specific menu item"
)
async def get_user_customization(
    menu_item_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Optional[UserMenuCustomizationResponse]:
    """Get user's customization for a menu item."""
    try:
        service = MenuService(db)
        return await service.get_user_customization(current_user.id, menu_item_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/customizations/{menu_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("navigation:write"))],
    summary="Reset menu item customization",
    description="Reset the current user's customization for a specific menu item to defaults"
)
async def reset_user_customization(
    menu_item_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset user's customization for a menu item."""
    try:
        service = MenuService(db)
        await service.delete_user_customization(current_user.id, menu_item_id)
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")