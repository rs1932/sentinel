"""
Field Definition Management API endpoints for Module 8

Provides RESTful API for field definition management including:
- Field Definition CRUD operations
- Three-tier field model support (core, platform_dynamic, tenant_specific)
- Field permission checking
- Field definition statistics
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.core.security_utils import get_current_user, require_scopes
from src.services.field_definition_service import FieldDefinitionService
from src.schemas.field_definition import (
    FieldDefinitionCreateRequest, FieldDefinitionUpdate, FieldDefinitionQuery,
    FieldDefinitionResponse, FieldDefinitionDetailResponse, FieldDefinitionListResponse,
    FieldPermissionCheck, FieldPermissionResponse, FieldDefinitionStatistics,
    FieldDefinitionBulkOperation, FieldDefinitionBulkResponse
)
from src.schemas import FieldDefinitionCreate
from src.core.exceptions import ValidationError, NotFoundError, ConflictError


# Helper function for single scope requirement
def require_scope(scope: str):
    return require_scopes(scope)


router = APIRouter(prefix="/field-definitions", tags=["Field Definition Management"])


@router.post(
    "/",
    response_model=FieldDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("field_definition:write"))],
    summary="Create a new field definition",
    description="Create a new field definition for the three-tier field model"
)
async def create_field_definition(
    field_data: FieldDefinitionCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FieldDefinitionResponse:
    """Create a new field definition."""
    try:
        # Convert request to internal create schema with tenant_id
        field_create = FieldDefinitionCreate(
            tenant_id=current_user.tenant_id,
            **field_data.dict()
        )

        service = FieldDefinitionService(db)
        return await service.create_field_definition(field_create)

    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/",
    response_model=FieldDefinitionListResponse,
    dependencies=[Depends(require_scope("field_definition:read"))],
    summary="List field definitions",
    description="Get a paginated list of field definitions with filtering options"
)
async def list_field_definitions(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    field_type: Optional[str] = Query(None, description="Filter by field type"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in field name and display name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("field_name", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FieldDefinitionListResponse:
    """List field definitions with filtering and pagination."""
    try:
        query_params = FieldDefinitionQuery(
            entity_type=entity_type,
            field_type=field_type,
            tenant_id=tenant_id,
            is_active=is_active,
            search=search,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )

        service = FieldDefinitionService(db)
        return await service.list_field_definitions(query_params, current_user.tenant_id)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/{field_id}",
    response_model=FieldDefinitionDetailResponse,
    dependencies=[Depends(require_scope("field_definition:read"))],
    summary="Get field definition details",
    description="Get detailed information about a specific field definition"
)
async def get_field_definition(
    field_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FieldDefinitionDetailResponse:
    """Get field definition by ID."""
    try:
        service = FieldDefinitionService(db)
        return await service.get_field_definition(field_id)

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch(
    "/{field_id}",
    response_model=FieldDefinitionResponse,
    dependencies=[Depends(require_scope("field_definition:write"))],
    summary="Update field definition",
    description="Update an existing field definition"
)
async def update_field_definition(
    field_id: UUID,
    field_data: FieldDefinitionUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FieldDefinitionResponse:
    """Update field definition."""
    try:
        service = FieldDefinitionService(db)
        return await service.update_field_definition(field_id, field_data)

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/{field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("field_definition:admin"))],
    summary="Delete field definition",
    description="Soft delete a field definition by marking it as inactive"
)
async def delete_field_definition(
    field_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete field definition (soft delete)."""
    try:
        service = FieldDefinitionService(db)
        await service.delete_field_definition(field_id)

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/entity/{entity_type}",
    response_model=List[FieldDefinitionResponse],
    dependencies=[Depends(require_scope("field_definition:read"))],
    summary="Get field definitions by entity type",
    description="Get all field definitions for a specific entity type"
)
async def get_field_definitions_by_entity(
    entity_type: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[FieldDefinitionResponse]:
    """Get field definitions for a specific entity type."""
    try:
        service = FieldDefinitionService(db)
        return await service.get_field_definitions_by_entity(entity_type, current_user.tenant_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/statistics",
    response_model=FieldDefinitionStatistics,
    dependencies=[Depends(require_scope("field_definition:read"))],
    summary="Get field definition statistics",
    description="Get statistics about field definitions"
)
async def get_field_definition_statistics(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FieldDefinitionStatistics:
    """Get field definition statistics."""
    try:
        service = FieldDefinitionService(db)
        return await service.get_statistics(current_user.tenant_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/bulk",
    response_model=FieldDefinitionBulkResponse,
    dependencies=[Depends(require_scope("field_definition:admin"))],
    summary="Bulk operations on field definitions",
    description="Perform bulk operations (activate, deactivate, delete) on multiple field definitions"
)
async def bulk_field_definition_operation(
    operation_data: FieldDefinitionBulkOperation,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FieldDefinitionBulkResponse:
    """Perform bulk operations on field definitions."""
    try:
        service = FieldDefinitionService(db)
        result = await service.bulk_operation(
            operation_data.field_definition_ids,
            operation_data.operation
        )

        return FieldDefinitionBulkResponse(
            operation=operation_data.operation,
            processed=result["processed"],
            failed=result["failed"],
            errors=[]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Field Permission Endpoints (API Section 7.4)
@router.post(
    "/field-permissions/check",
    response_model=FieldPermissionResponse,
    dependencies=[Depends(require_scope("permission:read"))],
    summary="Check field permissions for user",
    description="Check field permissions for a specific user and entity"
)
async def check_field_permissions(
    permission_check: FieldPermissionCheck,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FieldPermissionResponse:
    """Check field permissions for a user."""
    try:
        service = FieldDefinitionService(db)
        return await service.check_field_permissions(
            permission_check.user_id,
            permission_check.entity_type,
            permission_check.entity_id,
            permission_check.fields
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/field-permissions",
    response_model=FieldPermissionResponse,
    dependencies=[Depends(require_scope("permission:read"))],
    summary="Get field permissions for user",
    description="Get field permissions for a user via query parameters"
)
async def get_field_permissions(
    user_id: UUID = Query(..., description="User ID to check permissions for"),
    entity_type: str = Query(..., description="Entity type"),
    entity_id: Optional[str] = Query(None, description="Specific entity instance ID"),
    fields: Optional[str] = Query(None, description="Comma-separated field names"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FieldPermissionResponse:
    """Get field permissions for a user via query parameters."""
    try:
        field_list = fields.split(",") if fields else None

        service = FieldDefinitionService(db)
        return await service.check_field_permissions(
            user_id,
            entity_type,
            entity_id,
            field_list
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Additional utility endpoints
@router.get(
    "/types/field-types",
    response_model=List[str],
    dependencies=[Depends(require_scope("field_definition:read"))],
    summary="Get available field types",
    description="Get list of available field types for the three-tier model"
)
async def get_field_types(
    current_user=Depends(get_current_user)
) -> List[str]:
    """Get available field types."""
    from src.models.field_definition_types import FieldType
    return [e.value for e in FieldType]


@router.get(
    "/types/data-types",
    response_model=List[str],
    dependencies=[Depends(require_scope("field_definition:read"))],
    summary="Get available data types",
    description="Get list of available data types for field definitions"
)
async def get_data_types(
    current_user=Depends(get_current_user)
) -> List[str]:
    """Get available data types."""
    from src.models.field_definition_types import FieldDataType
    return [e.value for e in FieldDataType]


@router.get(
    "/types/permissions",
    response_model=List[str],
    dependencies=[Depends(require_scope("field_definition:read"))],
    summary="Get available field permissions",
    description="Get list of available field permission types"
)
async def get_field_permission_types(
    current_user=Depends(get_current_user)
) -> List[str]:
    """Get available field permission types."""
    from src.models.field_definition_types import FieldPermission
    return [e.value for e in FieldPermission]
