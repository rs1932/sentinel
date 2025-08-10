"""
Service Account management service for Module 3
Handles service account CRUD operations and credential management
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
import uuid
import secrets
import logging

from ..models.user import User
from ..models.tenant import Tenant
from ..schemas.user import (
    ServiceAccountCreate, ServiceAccountUpdate, ServiceAccountResponse,
    ServiceAccountDetailResponse, ServiceAccountListResponse, CredentialResponse,
    CredentialRotation, UserQuery
)
from ..core.exceptions import (
    NotFoundError, ValidationError, ConflictError
)
from ..utils.tenant_context import get_current_tenant_id

logger = logging.getLogger(__name__)


class ServiceAccountService:
    """Service for service account management operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_service_account(
        self, 
        account_data: ServiceAccountCreate, 
        tenant_id: Optional[UUID] = None,
        creator_id: Optional[UUID] = None
    ) -> Tuple[ServiceAccountResponse, CredentialResponse]:
        """
        Create a new service account
        
        Args:
            account_data: Service account creation data
            tenant_id: Tenant ID (from context if not provided)
            creator_id: ID of user creating this service account (for audit)
            
        Returns:
            Tuple[ServiceAccountResponse, CredentialResponse]: Created service account and credentials
        """
        # Use tenant from context if not provided
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        # Validate tenant exists and is active
        tenant = await self._get_active_tenant(tenant_id)
        
        # Check if service account name already exists in tenant
        existing_account = await self._get_service_account_by_name(account_data.name, tenant_id)
        if existing_account:
            raise ConflictError(f"Service account with name {account_data.name} already exists in this tenant")
        
        # Generate unique client_id and client_secret
        client_id = f"svc_{account_data.name.lower().replace(' ', '_').replace('-', '_')}_{secrets.token_hex(4)}"
        client_secret = secrets.token_urlsafe(32)
        
        # Create service account as a user with is_service_account=True
        service_account = User(
            tenant_id=tenant_id,
            email=f"{client_id}@{tenant.code.lower()}.service",  # Generate unique email
            username=account_data.name,
            password_hash=None,  # Service accounts don't use passwords
            is_service_account=True,
            service_account_key=client_secret,  # Store the secret
            attributes=account_data.attributes or {},
            preferences={},  # Service accounts don't need preferences
            is_active=account_data.is_active
        )
        
        self.db.add(service_account)
        await self.db.commit()
        await self.db.refresh(service_account)
        
        logger.info(f"Service account created: {service_account.id} ({client_id}) in tenant {tenant_id}")
        
        # Prepare response objects
        account_response = ServiceAccountResponse(
            id=service_account.id,
            tenant_id=service_account.tenant_id,
            name=service_account.username,
            description=account_data.description,
            attributes=service_account.attributes,
            client_id=client_id,
            is_active=service_account.is_active,
            last_login=service_account.last_login,
            login_count=service_account.login_count or 0,
            created_at=service_account.created_at,
            updated_at=service_account.updated_at
        )
        
        credential_response = CredentialResponse(
            client_id=client_id,
            client_secret=client_secret,
            created_at=service_account.created_at
        )
        
        return account_response, credential_response
    
    async def get_service_account(
        self, 
        account_id: UUID, 
        tenant_id: Optional[UUID] = None
    ) -> ServiceAccountDetailResponse:
        """
        Get service account by ID with detailed information
        
        Args:
            account_id: Service account ID
            tenant_id: Tenant ID (from context if not provided)
            
        Returns:
            ServiceAccountDetailResponse: Service account details
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        account = await self._get_service_account_by_id(account_id, tenant_id)
        if not account:
            raise NotFoundError(f"Service account {account_id} not found")
        
        return ServiceAccountDetailResponse(
            id=account.id,
            tenant_id=account.tenant_id,
            name=account.username,
            description=None,  # Could be stored in attributes
            attributes=account.attributes,
            client_id=self._generate_client_id_from_account(account),
            is_active=account.is_active,
            last_login=account.last_login,
            login_count=account.login_count or 0,
            failed_login_count=account.failed_login_count or 0,
            locked_until=account.locked_until,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    
    async def list_service_accounts(
        self, 
        query_params: UserQuery, 
        tenant_id: Optional[UUID] = None
    ) -> ServiceAccountListResponse:
        """
        List service accounts with filtering and pagination
        
        Args:
            query_params: Query parameters for filtering and pagination
            tenant_id: Tenant ID (from context if not provided)
            
        Returns:
            ServiceAccountListResponse: Paginated list of service accounts
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        # Base query for service accounts
        query = select(User).where(
            and_(
                User.tenant_id == tenant_id,
                User.is_service_account == True
            )
        )
        
        # Apply filters
        if query_params.is_active is not None:
            query = query.where(User.is_active == query_params.is_active)
        
        if query_params.search:
            search_term = f"%{query_params.search.lower()}%"
            query = query.where(
                or_(
                    func.lower(User.username).like(search_term),
                    func.lower(User.email).like(search_term)
                )
            )
        
        # Count total results
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        sort_column = getattr(User, query_params.sort.value)
        if query_params.order.value == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (query_params.page - 1) * query_params.limit
        query = query.offset(offset).limit(query_params.limit)
        
        # Execute query
        result = await self.db.execute(query)
        accounts = result.scalars().all()
        
        # Convert to response models
        account_responses = []
        for account in accounts:
            account_responses.append(ServiceAccountResponse(
                id=account.id,
                tenant_id=account.tenant_id,
                name=account.username,
                description=None,
                attributes=account.attributes,
                client_id=self._generate_client_id_from_account(account),
                is_active=account.is_active,
                last_login=account.last_login,
                login_count=account.login_count or 0,
                created_at=account.created_at,
                updated_at=account.updated_at
            ))
        
        return ServiceAccountListResponse(
            items=account_responses,
            total=total,
            page=query_params.page,
            limit=query_params.limit,
            pages=(total + query_params.limit - 1) // query_params.limit
        )
    
    async def update_service_account(
        self, 
        account_id: UUID, 
        account_data: ServiceAccountUpdate, 
        tenant_id: Optional[UUID] = None,
        updater_id: Optional[UUID] = None
    ) -> ServiceAccountResponse:
        """
        Update service account information
        
        Args:
            account_id: Service account ID to update
            account_data: Updated service account data
            tenant_id: Tenant ID (from context if not provided)
            updater_id: ID of user making the update (for audit)
            
        Returns:
            ServiceAccountResponse: Updated service account data
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        account = await self._get_service_account_by_id(account_id, tenant_id)
        if not account:
            raise NotFoundError(f"Service account {account_id} not found")
        
        # Check name uniqueness if being changed
        if account_data.name and account_data.name != account.username:
            existing_account = await self._get_service_account_by_name(account_data.name, tenant_id)
            if existing_account and existing_account.id != account_id:
                raise ConflictError(f"Service account with name {account_data.name} already exists")
        
        # Update fields
        update_data = {}
        if account_data.name:
            update_data['username'] = account_data.name
        if account_data.attributes is not None:
            update_data['attributes'] = account_data.attributes
        if account_data.is_active is not None:
            update_data['is_active'] = account_data.is_active
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            
            await self.db.execute(
                update(User)
                .where(User.id == account_id)
                .values(**update_data)
            )
            await self.db.commit()
        
        # Refresh account data
        await self.db.refresh(account)
        
        logger.info(f"Service account updated: {account_id} by {updater_id}")
        
        return ServiceAccountResponse(
            id=account.id,
            tenant_id=account.tenant_id,
            name=account.username,
            description=account_data.description,
            attributes=account.attributes,
            client_id=self._generate_client_id_from_account(account),
            is_active=account.is_active,
            last_login=account.last_login,
            login_count=account.login_count or 0,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    
    async def delete_service_account(
        self, 
        account_id: UUID, 
        tenant_id: Optional[UUID] = None,
        soft_delete: bool = True
    ) -> None:
        """
        Delete service account (soft delete by default)
        
        Args:
            account_id: Service account ID to delete
            tenant_id: Tenant ID (from context if not provided)
            soft_delete: Whether to soft delete (deactivate) or hard delete
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        account = await self._get_service_account_by_id(account_id, tenant_id)
        if not account:
            raise NotFoundError(f"Service account {account_id} not found")
        
        if soft_delete:
            # Soft delete by deactivating
            await self.db.execute(
                update(User)
                .where(User.id == account_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            logger.info(f"Service account soft deleted: {account_id}")
        else:
            # Hard delete
            await self.db.execute(delete(User).where(User.id == account_id))
            logger.info(f"Service account hard deleted: {account_id}")
        
        await self.db.commit()
    
    async def rotate_credentials(
        self,
        account_id: UUID,
        rotation_data: CredentialRotation,
        tenant_id: Optional[UUID] = None
    ) -> CredentialResponse:
        """
        Rotate service account credentials
        
        Args:
            account_id: Service account ID
            rotation_data: Credential rotation options
            tenant_id: Tenant ID (from context if not provided)
            
        Returns:
            CredentialResponse: New credentials
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        account = await self._get_service_account_by_id(account_id, tenant_id)
        if not account:
            raise NotFoundError(f"Service account {account_id} not found")
        
        # Generate new secret
        new_client_secret = secrets.token_urlsafe(32)
        
        # Update the service account key
        await self.db.execute(
            update(User)
            .where(User.id == account_id)
            .values(
                service_account_key=new_client_secret,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        logger.info(f"Service account credentials rotated: {account_id}")
        
        # Generate client_id for response
        client_id = self._generate_client_id_from_account(account)
        
        return CredentialResponse(
            client_id=client_id,
            client_secret=new_client_secret,
            created_at=datetime.utcnow()
        )
    
    async def validate_api_key(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: Optional[UUID] = None
    ) -> Optional[User]:
        """
        Validate service account API key
        
        Args:
            client_id: Client ID
            client_secret: Client secret to validate
            tenant_id: Tenant ID (from context if not provided)
            
        Returns:
            Optional[User]: Service account user if valid
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        # Find service account by client_secret (stored in service_account_key)
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.tenant_id == tenant_id,
                    User.is_service_account == True,
                    User.service_account_key == client_secret,
                    User.is_active == True
                )
            )
        )
        account = result.scalar_one_or_none()
        
        if account:
            # Verify client_id matches expected pattern
            expected_client_id = self._generate_client_id_from_account(account)
            if client_id == expected_client_id:
                return account
        
        return None
    
    # Private helper methods
    
    async def _get_active_tenant(self, tenant_id: UUID) -> Tenant:
        """Get active tenant by ID"""
        result = await self.db.execute(
            select(Tenant).where(
                and_(Tenant.id == tenant_id, Tenant.is_active == True)
            )
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError(f"Tenant {tenant_id} not found or inactive")
        return tenant
    
    async def _get_service_account_by_id(self, account_id: UUID, tenant_id: UUID) -> Optional[User]:
        """Get service account by ID and tenant"""
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.id == account_id,
                    User.tenant_id == tenant_id,
                    User.is_service_account == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_service_account_by_name(self, name: str, tenant_id: UUID) -> Optional[User]:
        """Get service account by name and tenant"""
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.username == name,
                    User.tenant_id == tenant_id,
                    User.is_service_account == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    def _generate_client_id_from_account(self, account: User) -> str:
        """Generate client_id from service account"""
        if not account.username:
            return f"svc_{account.id.hex[:8]}"
        
        name_part = account.username.lower().replace(' ', '_').replace('-', '_')
        # Extract the unique suffix from email or use account id
        if '@' in account.email:
            email_local = account.email.split('@')[0]
            if '_' in email_local:
                suffix = email_local.split('_')[-1]
                return f"svc_{name_part}_{suffix}"
        
        return f"svc_{name_part}_{account.id.hex[:8]}"