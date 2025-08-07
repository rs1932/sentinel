"""
Service Account management API endpoints for Module 3
Handles service account CRUD operations with JWT authentication and scope-based authorization
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.core.security_utils import get_current_user, require_scopes, CurrentUser
from src.services.service_account_service import ServiceAccountService
from src.schemas.user import (
    ServiceAccountCreate, ServiceAccountUpdate, ServiceAccountResponse,
    ServiceAccountDetailResponse, ServiceAccountListResponse, CredentialResponse,
    CredentialRotation, UserQuery, SortField, SortOrder
)
from src.core.exceptions import (
    NotFoundError, ValidationError, ConflictError
)
from uuid import UUID

router = APIRouter(prefix="/service-accounts", tags=["service-accounts"])
security = HTTPBearer()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_service_account(
    account_data: ServiceAccountCreate,
    current_user: CurrentUser = Depends(require_scopes("service_account:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new service account
    
    Required scope: service_account:admin
    
    Returns both service account info and credentials (client_secret only returned once)
    """
    try:
        service_account_service = ServiceAccountService(db)
        account_response, credential_response = await service_account_service.create_service_account(
            account_data=account_data,
            tenant_id=current_user.tenant_id,
            creator_id=current_user.user_id
        )
        
        return {
            "service_account": account_response,
            "credentials": credential_response
        }
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/", response_model=ServiceAccountListResponse)
async def list_service_accounts(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    sort: SortField = Query(SortField.created_at, description="Sort field"),
    order: SortOrder = Query(SortOrder.desc, description="Sort order"),
    current_user: CurrentUser = Depends(require_scopes("service_account:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    List service accounts with filtering and pagination
    
    Required scope: service_account:read
    """
    service_account_service = ServiceAccountService(db)
    
    # Build query parameters
    query_params = UserQuery(
        tenant_id=current_user.tenant_id,
        is_active=is_active,
        search=search,
        page=page,
        limit=limit,
        sort=sort,
        order=order
    )
    
    return await service_account_service.list_service_accounts(
        query_params=query_params,
        tenant_id=current_user.tenant_id
    )


@router.get("/{account_id}", response_model=ServiceAccountDetailResponse)
async def get_service_account(
    account_id: UUID,
    current_user: CurrentUser = Depends(require_scopes("service_account:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get service account details by ID
    
    Required scope: service_account:read
    """
    try:
        service_account_service = ServiceAccountService(db)
        return await service_account_service.get_service_account(
            account_id=account_id,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{account_id}", response_model=ServiceAccountResponse)
async def update_service_account(
    account_id: UUID,
    account_data: ServiceAccountUpdate,
    current_user: CurrentUser = Depends(require_scopes("service_account:write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update service account information
    
    Required scope: service_account:write
    """
    try:
        service_account_service = ServiceAccountService(db)
        return await service_account_service.update_service_account(
            account_id=account_id,
            account_data=account_data,
            tenant_id=current_user.tenant_id,
            updater_id=current_user.user_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_account(
    account_id: UUID,
    hard_delete: bool = Query(False, description="Perform hard delete instead of soft delete"),
    current_user: CurrentUser = Depends(require_scopes("service_account:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete service account (soft delete by default)
    
    Required scope: service_account:admin
    """
    try:
        service_account_service = ServiceAccountService(db)
        await service_account_service.delete_service_account(
            account_id=account_id,
            tenant_id=current_user.tenant_id,
            soft_delete=not hard_delete
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{account_id}/rotate-credentials", response_model=CredentialResponse)
async def rotate_service_account_credentials(
    account_id: UUID,
    rotation_data: Optional[CredentialRotation] = None,
    current_user: CurrentUser = Depends(require_scopes("service_account:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Rotate service account credentials
    
    Required scope: service_account:admin
    
    Returns new credentials (client_secret only returned once)
    """
    try:
        service_account_service = ServiceAccountService(db)
        
        # Use default rotation settings if not provided
        if rotation_data is None:
            rotation_data = CredentialRotation()
        
        return await service_account_service.rotate_credentials(
            account_id=account_id,
            rotation_data=rotation_data,
            tenant_id=current_user.tenant_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{account_id}/validate", status_code=status.HTTP_200_OK)
async def validate_service_account(
    account_id: UUID,
    client_secret: str = Query(..., description="Client secret to validate"),
    current_user: CurrentUser = Depends(require_scopes("service_account:admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate service account credentials (for administrative purposes)
    
    Required scope: service_account:admin
    """
    try:
        service_account_service = ServiceAccountService(db)
        account = await service_account_service.get_service_account(
            account_id=account_id,
            tenant_id=current_user.tenant_id
        )
        
        # Validate the credentials
        validated_account = await service_account_service.validate_api_key(
            client_id=account.client_id,
            client_secret=client_secret,
            tenant_id=current_user.tenant_id
        )
        
        return {
            "valid": validated_account is not None,
            "account_id": account_id,
            "client_id": account.client_id,
            "is_active": account.is_active
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))