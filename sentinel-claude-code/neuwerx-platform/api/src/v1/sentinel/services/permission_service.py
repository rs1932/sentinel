"""
PermissionService for Module 6: Manage permissions and support role assignments
"""
from typing import List, Optional, Tuple
from uuid import UUID as UUID_T
from sqlalchemy import select, and_, update, delete, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models import Permission, RolePermission, Role
from ..schemas.permission import (
    PermissionCreate, PermissionUpdate, PermissionResponse, PermissionListResponse
)
from ..core.exceptions import NotFoundError, ConflictError, ValidationError


class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_permission(self, data: PermissionCreate) -> PermissionResponse:
        # Validate resource_id xor resource_path
        if (data.resource_id is None and data.resource_path is None) or (
            data.resource_id is not None and data.resource_path is not None
        ):
            raise ValidationError("Exactly one of resource_id or resource_path must be provided")

        permission = Permission(
            tenant_id=data.tenant_id,
            name=data.name,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            resource_path=data.resource_path,
            actions=data.actions,
            conditions=data.conditions,
            field_permissions=data.field_permissions,
            is_active=data.is_active,
        )
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return PermissionResponse.model_validate(permission)

    async def get_permission(self, permission_id: UUID_T, tenant_id: UUID_T) -> PermissionResponse:
        stmt = select(Permission).where(and_(Permission.id == permission_id, Permission.tenant_id == tenant_id))
        res = await self.db.execute(stmt)
        perm = res.scalar_one_or_none()
        if not perm:
            raise NotFoundError("Permission not found")
        return PermissionResponse.model_validate(perm)

    async def update_permission(self, permission_id: UUID_T, tenant_id: UUID_T, data: PermissionUpdate) -> PermissionResponse:
        stmt = select(Permission).where(and_(Permission.id == permission_id, Permission.tenant_id == tenant_id))
        res = await self.db.execute(stmt)
        perm = res.scalar_one_or_none()
        if not perm:
            raise NotFoundError("Permission not found")

        update_data = data.model_dump(exclude_unset=True)
        if "resource_id" in update_data and "resource_path" in update_data and update_data["resource_id"] is not None and update_data["resource_path"] is not None:
            raise ValidationError("Only one of resource_id or resource_path can be updated at a time")

        await self.db.execute(
            update(Permission)
            .where(Permission.id == permission_id)
            .values(**update_data)
        )
        await self.db.commit()

        return await self.get_permission(permission_id, tenant_id)

    async def delete_permission(self, permission_id: UUID_T, tenant_id: UUID_T) -> bool:
        # Ensure no role assignments exist (or rely on CASCADE?)
        # Soft delete not defined; follow spec with hard delete if needed
        stmt = select(Permission).where(and_(Permission.id == permission_id, Permission.tenant_id == tenant_id))
        res = await self.db.execute(stmt)
        perm = res.scalar_one_or_none()
        if not perm:
            return False

        await self.db.execute(delete(RolePermission).where(RolePermission.permission_id == permission_id))
        await self.db.execute(delete(Permission).where(Permission.id == permission_id))
        await self.db.commit()
        return True

    async def list_permissions(
        self,
        tenant_id: Optional[UUID_T],
        resource_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> PermissionListResponse:
        # Build base query conditions
        conditions = []
        if tenant_id is not None:
            conditions.append(Permission.tenant_id == tenant_id)
        
        stmt = select(Permission)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        count_stmt = select(literal(0))  # placeholder if later need exact count

        if resource_type is not None:
            stmt = stmt.where(Permission.resource_type == resource_type)
        if is_active is not None:
            stmt = stmt.where(Permission.is_active == is_active)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(Permission.name.ilike(like))

        stmt = stmt.offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        items = [PermissionResponse.model_validate(r) for r in res.scalars().all()]
        total = len(items) if skip == 0 else skip + len(items)  # simple estimate

        return PermissionListResponse(items=items, total=total, page=1, limit=limit)

