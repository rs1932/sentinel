"""
GroupService: business logic for Module 5 (Groups)
"""
from typing import List, Optional, Tuple
from uuid import UUID as PyUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, literal
from sqlalchemy.exc import IntegrityError

from ..core.exceptions import NotFoundError, ConflictError, ValidationError
from ..models.group import Group, UserGroup, GroupRole
from ..models.user import User
from ..models.role import Role
from ..schemas.group import (
    GroupCreate, GroupUpdate, GroupQuery,
    GroupResponse, GroupListResponse
)


class GroupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_group_by_id(self, group_id: PyUUID, tenant_id: PyUUID) -> Group:
        res = await self.db.execute(select(Group).where(and_(Group.id == group_id, Group.tenant_id == tenant_id)))
        grp = res.scalar_one_or_none()
        if not grp:
            raise NotFoundError("Group not found")
        return grp

    async def _validate_parent(self, parent_group_id: Optional[PyUUID], tenant_id: PyUUID):
        if not parent_group_id:
            return
        res = await self.db.execute(select(Group).where(and_(Group.id == parent_group_id, Group.tenant_id == tenant_id)))
        parent = res.scalar_one_or_none()
        if not parent:
            raise ValidationError("Invalid parent group")

    async def _would_create_cycle(self, group_id: Optional[PyUUID], parent_group_id: Optional[PyUUID], tenant_id: PyUUID) -> bool:
        if not parent_group_id or not group_id:
            return False
        # Walk up parents to detect cycle
        current_id = parent_group_id
        while current_id:
            res = await self.db.execute(select(Group.parent_group_id).where(and_(Group.id == current_id, Group.tenant_id == tenant_id)))
            row = res.first()
            if not row:
                break
            if row[0] == group_id:
                return True
            current_id = row[0]
        return False

    async def create_group(self, tenant_id: PyUUID, group_data: GroupCreate, created_by: Optional[PyUUID] = None) -> GroupResponse:
        await self._validate_parent(group_data.parent_group_id, tenant_id)
        # name uniqueness per tenant enforced by DB; front-run check for better error
        exists = await self.db.execute(select(Group).where(and_(Group.tenant_id == tenant_id, Group.name == group_data.name)))
        if exists.scalar_one_or_none():
            raise ConflictError(f"Group '{group_data.name}' already exists in this tenant")
        grp = Group(
            tenant_id=tenant_id,
            name=group_data.name,
            display_name=group_data.display_name,
            description=group_data.description,
            parent_group_id=group_data.parent_group_id,
            group_metadata=group_data.metadata,
            is_active=group_data.is_active,
        )
        self.db.add(grp)
        try:
            await self.db.commit()
            await self.db.refresh(grp)
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError("Failed to create group: integrity violation") from e
        return GroupResponse.model_validate(grp)

    async def get_group(self, group_id: PyUUID, tenant_id: PyUUID) -> GroupResponse:
        grp = await self._get_group_by_id(group_id, tenant_id)
        return GroupResponse.model_validate(grp)

    async def list_groups(self, tenant_id: PyUUID, query: GroupQuery) -> GroupListResponse:
        stmt = select(Group).where(Group.tenant_id == tenant_id)
        if query.is_active is not None:
            stmt = stmt.where(Group.is_active == query.is_active)
        if query.parent_group_id is not None:
            stmt = stmt.where(Group.parent_group_id == query.parent_group_id)
        if query.search:
            like = f"%{query.search.lower()}%"
            stmt = stmt.where(or_(func.lower(Group.name).like(like), func.lower(Group.display_name).like(like)))
        # Sorting
        sort_col = Group.name if query.sort_by == "name" else getattr(Group, query.sort_by, Group.name)
        if query.sort_order == "desc":
            sort_col = sort_col.desc()
        stmt = stmt.order_by(sort_col).offset(query.skip).limit(query.limit)

        res = await self.db.execute(stmt)
        items = [GroupResponse.model_validate(g) for g in res.scalars().all()]

        # Total count
        res2 = await self.db.execute(select(func.count()).select_from(Group).where(Group.tenant_id == tenant_id))
        total = int(res2.scalar() or 0)
        return GroupListResponse(items=items, total=total, skip=query.skip, limit=query.limit)

    async def update_group(self, group_id: PyUUID, tenant_id: PyUUID, data: GroupUpdate) -> GroupResponse:
        grp = await self._get_group_by_id(group_id, tenant_id)
        if data.parent_group_id:
            await self._validate_parent(data.parent_group_id, tenant_id)
            if await self._would_create_cycle(group_id, data.parent_group_id, tenant_id):
                raise ValidationError("Cannot set parent: would create circular dependency")
        # Update fields
        update_dict = data.model_dump(exclude_unset=True, by_alias=True)
        grp.update(**update_dict)
        try:
            await self.db.commit()
            await self.db.refresh(grp)
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError("Failed to update group: integrity violation") from e
        return GroupResponse.model_validate(grp)

    async def delete_group(self, group_id: PyUUID, tenant_id: PyUUID) -> None:
        grp = await self._get_group_by_id(group_id, tenant_id)
        # Soft delete (set is_active False); full delete can be considered in future
        grp.is_active = False
        await self.db.commit()

    async def add_users_to_group(self, group_id: PyUUID, user_ids: List[PyUUID], tenant_id: PyUUID, added_by: Optional[PyUUID] = None) -> int:
        grp = await self._get_group_by_id(group_id, tenant_id)
        # Fetch users and validate tenant
        res = await self.db.execute(select(User).where(and_(User.id.in_(user_ids), User.tenant_id == tenant_id)))
        users = res.scalars().all()
        if len(users) != len(set(user_ids)):
            raise ValidationError("One or more users not found or not in tenant")
        # Insert memberships (skip duplicates via unique constraint handling)
        inserted = 0
        for uid in set(user_ids):
            membership = UserGroup(user_id=uid, group_id=grp.id, added_by=added_by)
            self.db.add(membership)
            try:
                await self.db.commit()
                inserted += 1
            except IntegrityError:
                await self.db.rollback()  # already a member; ignore
        return inserted

    async def remove_user_from_group(self, group_id: PyUUID, user_id: PyUUID, tenant_id: PyUUID) -> None:
        await self._get_group_by_id(group_id, tenant_id)
        # Delete row if exists
        await self.db.execute(
            UserGroup.__table__.delete().where(and_(UserGroup.group_id == group_id, UserGroup.user_id == user_id))
        )
        await self.db.commit()

    async def list_group_members(self, group_id: PyUUID, tenant_id: PyUUID) -> List[PyUUID]:
        await self._get_group_by_id(group_id, tenant_id)
        res = await self.db.execute(select(UserGroup.user_id).where(UserGroup.group_id == group_id))
        return [row[0] for row in res.fetchall()]

    async def assign_roles_to_group(self, group_id: PyUUID, role_ids: List[PyUUID], tenant_id: PyUUID, granted_by: Optional[PyUUID] = None) -> int:
        await self._get_group_by_id(group_id, tenant_id)
        # Validate roles are in same tenant
        res = await self.db.execute(select(Role).where(and_(Role.id.in_(role_ids), Role.tenant_id == tenant_id)))
        roles = res.scalars().all()
        if len(roles) != len(set(role_ids)):
            raise ValidationError("One or more roles not found or not in tenant")
        assigned = 0
        for rid in set(role_ids):
            gr = GroupRole(group_id=group_id, role_id=rid, granted_by=granted_by)
            self.db.add(gr)
            try:
                await self.db.commit()
                assigned += 1
            except IntegrityError:
                await self.db.rollback()  # duplicate assignment; ignore
        return assigned

    async def remove_role_from_group(self, group_id: PyUUID, role_id: PyUUID, tenant_id: PyUUID) -> None:
        await self._get_group_by_id(group_id, tenant_id)
        await self.db.execute(
            GroupRole.__table__.delete().where(and_(GroupRole.group_id == group_id, GroupRole.role_id == role_id))
        )
        await self.db.commit()

    async def list_group_roles(self, group_id: PyUUID, tenant_id: PyUUID) -> List[PyUUID]:
        await self._get_group_by_id(group_id, tenant_id)
        res = await self.db.execute(select(GroupRole.role_id).where(GroupRole.group_id == group_id))
        return [row[0] for row in res.fetchall()]

