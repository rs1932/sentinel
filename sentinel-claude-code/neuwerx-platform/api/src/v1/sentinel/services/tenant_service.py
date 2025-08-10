from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, func, select
import logging

from ..models.tenant import Tenant, TenantType, IsolationMode
from ..schemas.tenant import (
    TenantCreate, TenantUpdate, TenantQuery,
    TenantResponse, TenantDetailResponse, TenantListResponse,
    SubTenantCreate
)
from ..utils.exceptions import (
    NotFoundError, ConflictError, ValidationError,
    TenantError
)
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

class TenantService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        result = await self.db.execute(select(Tenant).where(Tenant.code == tenant_data.code))
        existing = result.scalar_one_or_none()
        if existing:
            raise ConflictError(f"Tenant with code '{tenant_data.code}' already exists")
        
        if tenant_data.parent_tenant_id:
            result = await self.db.execute(select(Tenant).where(
                Tenant.id == tenant_data.parent_tenant_id
            ))
            parent = result.scalar_one_or_none()
            if not parent:
                raise NotFoundError(f"Parent tenant with ID {tenant_data.parent_tenant_id} not found")
            if not parent.is_active:
                raise ValidationError("Cannot create sub-tenant under inactive parent")
        
        # Convert the Pydantic model to dict, which will have 'metadata' field
        # The Tenant.__init__ will handle mapping metadata → tenant_metadata
        tenant_dict = tenant_data.dict()
        # Since we use use_enum_values=True, dict() returns strings
        # The Tenant.__init__ will convert them back to enums
        tenant = Tenant(**tenant_dict)
        
        try:
            self.db.add(tenant)
            await self.db.commit()
            await self.db.refresh(tenant)
            
            await cache_service.delete(f"tenant:{tenant.code}")
            await cache_service.delete(f"tenant:{tenant.id}")
            
            logger.info(f"Created tenant: {tenant.code} (ID: {tenant.id})")
            return tenant
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to create tenant: {str(e)}")
            raise ConflictError(f"Failed to create tenant: {str(e)}")
    
    async def get_tenant(self, tenant_id: UUID) -> Tenant:
        cache_key = f"tenant:{tenant_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            return Tenant(**cached)
        
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError(f"Tenant with ID {tenant_id} not found")
        
        await cache_service.set(cache_key, tenant.to_dict(), ttl=300)
        return tenant
    
    async def get_tenant_by_code(self, code: str) -> Tenant:
        cache_key = f"tenant:{code}"
        cached = await cache_service.get(cache_key)
        if cached:
            return Tenant(**cached)
        
        result = await self.db.execute(select(Tenant).where(Tenant.code == code))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError(f"Tenant with code '{code}' not found")
        
        await cache_service.set(cache_key, tenant.to_dict(), ttl=300)
        return tenant
    
    async def list_tenants(self, query: TenantQuery, current_user_tenant_id: Optional[UUID] = None) -> TenantListResponse:
        stmt = select(Tenant)
        
        # TENANT ISOLATION: Only show tenants the user has access to
        if current_user_tenant_id:
            # For tenant admins: show only their own tenant and any sub-tenants
            stmt = stmt.where(
                or_(
                    Tenant.id == current_user_tenant_id,  # Their own tenant
                    Tenant.parent_tenant_id == current_user_tenant_id  # Sub-tenants they manage
                )
            )
        # Note: Super admins (platform users) get current_user_tenant_id=None and see all tenants
        
        if query.name:
            stmt = stmt.where(Tenant.name.ilike(f"%{query.name}%"))
        if query.code:
            stmt = stmt.where(Tenant.code.ilike(f"%{query.code}%"))
        if query.type:
            stmt = stmt.where(Tenant.type == query.type)
        if query.parent_tenant_id:
            stmt = stmt.where(Tenant.parent_tenant_id == query.parent_tenant_id)
        if query.is_active is not None:
            stmt = stmt.where(Tenant.is_active == query.is_active)
        
        count_result = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count_result.scalar()
        
        result = await self.db.execute(stmt.offset(query.offset).limit(query.limit))
        tenants = result.scalars().all()
        
        return TenantListResponse(
            items=[TenantResponse(**t.to_dict()) for t in tenants],
            total=total,
            limit=query.limit,
            offset=query.offset
        )
    
    async def update_tenant(self, tenant_id: UUID, update_data: TenantUpdate) -> Tenant:
        # Query the tenant directly to ensure it's in the current session
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError(f"Tenant with ID {tenant_id} not found")
        
        if tenant.code == "PLATFORM":
            raise ValidationError("Platform tenant cannot be modified")
        
        update_dict = update_data.dict(exclude_unset=True)
        
        # Handle metadata mapping for update
        if "metadata" in update_dict:
            update_dict["tenant_metadata"] = update_dict.pop("metadata")
        
        for key, value in update_dict.items():
            setattr(tenant, key, value)
        
        try:
            await self.db.commit()
            await self.db.refresh(tenant)
            
            await cache_service.delete(f"tenant:{tenant.code}")
            await cache_service.delete(f"tenant:{tenant.id}")
            
            logger.info(f"Updated tenant: {tenant.code} (ID: {tenant.id})")
            return tenant
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to update tenant: {str(e)}")
            raise ConflictError(f"Failed to update tenant: {str(e)}")
    
    async def delete_tenant(self, tenant_id: UUID) -> bool:
        # Query the tenant directly without using get_tenant to avoid session issues
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError(f"Tenant with ID {tenant_id} not found")
        
        if tenant.code == "PLATFORM":
            raise ValidationError("Platform tenant cannot be deleted")
        
        count_result = await self.db.execute(select(func.count(Tenant.id)).where(
            Tenant.parent_tenant_id == tenant_id
        ))
        sub_tenants_count = count_result.scalar()
        
        if sub_tenants_count > 0:
            raise ValidationError(f"Cannot delete tenant with {sub_tenants_count} sub-tenants")
        
        # Store values for cache deletion before deleting the object
        tenant_code = tenant.code
        
        try:
            await self.db.delete(tenant)
            await self.db.commit()
            
            await cache_service.delete(f"tenant:{tenant_code}")
            await cache_service.delete(f"tenant:{tenant_id}")
            
            logger.info(f"Deleted tenant: {tenant_code} (ID: {tenant_id})")
            return True
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to delete tenant: {str(e)}")
            raise ConflictError(f"Failed to delete tenant due to existing dependencies")
    
    async def create_sub_tenant(
        self, 
        parent_tenant_id: UUID, 
        sub_tenant_data: SubTenantCreate
    ) -> Tenant:
        parent = await self.get_tenant(parent_tenant_id)
        
        if not parent.is_active:
            raise ValidationError("Cannot create sub-tenant under inactive parent")
        
        tenant_create = TenantCreate(
            **sub_tenant_data.dict(),
            type=TenantType.SUB_TENANT,
            parent_tenant_id=parent_tenant_id
        )
        
        return await self.create_tenant(tenant_create)
    
    async def get_tenant_hierarchy(self, tenant_id: UUID) -> List[Tenant]:
        tenant = await self.get_tenant(tenant_id)
        return tenant.get_hierarchy()
    
    async def get_tenant_detail(self, tenant_id: UUID) -> TenantDetailResponse:
        tenant = await self.get_tenant(tenant_id)
        
        count_result = await self.db.execute(select(func.count(Tenant.id)).where(
            Tenant.parent_tenant_id == tenant_id
        ))
        sub_tenants_count = count_result.scalar()
        
        # For now, skip user count since User model doesn't exist yet
        users_count = 0
        try:
            from ..models.user import User
            count_result = await self.db.execute(select(func.count(User.id)).where(
                User.tenant_id == tenant_id
            ))
            users_count = count_result.scalar() or 0
        except ImportError:
            # User model not implemented yet
            pass
        
        hierarchy = tenant.get_hierarchy()
        
        response = TenantDetailResponse(**tenant.to_dict())
        response.sub_tenants_count = sub_tenants_count or 0
        response.users_count = users_count
        response.hierarchy = [TenantResponse(**t.to_dict()) for t in hierarchy]
        
        return response
    
    async def activate_tenant(self, tenant_id: UUID) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        
        if tenant.is_active:
            raise ValidationError("Tenant is already active")
        
        if tenant.parent_tenant_id:
            parent = await self.get_tenant(tenant.parent_tenant_id)
            if not parent.is_active:
                raise ValidationError("Cannot activate sub-tenant when parent is inactive")
        
        tenant.is_active = True
        await self.db.commit()
        await self.db.refresh(tenant)
        
        await cache_service.delete(f"tenant:{tenant.code}")
        await cache_service.delete(f"tenant:{tenant.id}")
        
        logger.info(f"Activated tenant: {tenant.code} (ID: {tenant.id})")
        return tenant
    
    async def deactivate_tenant(self, tenant_id: UUID) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        
        if tenant.code == "PLATFORM":
            raise ValidationError("Platform tenant cannot be deactivated")
        
        if not tenant.is_active:
            raise ValidationError("Tenant is already inactive")
        
        count_result = await self.db.execute(select(func.count(Tenant.id)).where(
            and_(
                Tenant.parent_tenant_id == tenant_id,
                Tenant.is_active == True
            )
        ))
        active_sub_tenants = count_result.scalar()
        
        if active_sub_tenants > 0:
            raise ValidationError(f"Cannot deactivate tenant with {active_sub_tenants} active sub-tenants")
        
        tenant.is_active = False
        await self.db.commit()
        await self.db.refresh(tenant)
        
        await cache_service.delete(f"tenant:{tenant.code}")
        await cache_service.delete(f"tenant:{tenant.id}")
        
        logger.info(f"Deactivated tenant: {tenant.code} (ID: {tenant.id})")
        return tenant
    
    async def validate_tenant_access(self, tenant_id: UUID, target_tenant_id: UUID) -> bool:
        if tenant_id == target_tenant_id:
            return True
        
        target_tenant = await self.get_tenant(target_tenant_id)
        return target_tenant.is_sub_tenant_of(tenant_id)