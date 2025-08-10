"""
RolePermissionService for Module 6: Manage role-permission assignments
"""
from typing import List, Optional
from uuid import UUID as UUID_T
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Permission, RolePermission, Role
from ..schemas.permission import (
    PermissionCreate, PermissionResponse, RolePermissionAssignment,
    RolePermissionResponse, RolePermissionsListResponse
)
from ..services.permission_service import PermissionService
from ..core.exceptions import NotFoundError, ConflictError, ValidationError


class RolePermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.permission_service = PermissionService(db)

    async def assign_permissions_to_role(
        self,
        role_id: UUID_T,
        tenant_id: UUID_T,
        assignments: List[RolePermissionAssignment],
        granted_by: UUID_T
    ) -> List[RolePermissionResponse]:
        """
        Assign permissions to a role. Can either reference existing permissions
        or create new ones as part of the assignment.
        """
        # Verify role exists and belongs to tenant
        role_stmt = select(Role).where(and_(Role.id == role_id, Role.tenant_id == tenant_id))
        role_result = await self.db.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundError("Role not found")

        results = []
        for assignment in assignments:
            if assignment.permission_id:
                # Use existing permission
                permission = await self.permission_service.get_permission(assignment.permission_id, tenant_id)
                permission_id = assignment.permission_id
            else:
                # Create new permission
                permission = await self.permission_service.create_permission(assignment.permission)
                permission_id = permission.id

            # Check if assignment already exists
            existing_stmt = select(RolePermission).where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                )
            )
            existing_result = await self.db.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                continue  # Skip if already assigned

            # Create role-permission assignment
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                granted_by=granted_by
            )
            self.db.add(role_permission)
            await self.db.commit()

            results.append(RolePermissionResponse(
                role_id=role_id,
                permission=permission,
                granted_by=granted_by
            ))

        return results

    async def get_role_permissions(
        self,
        role_id: UUID_T,
        tenant_id: UUID_T,
        include_inherited: bool = True
    ) -> RolePermissionsListResponse:
        """
        Get all permissions for a role, optionally including inherited permissions.
        """
        # Verify role exists
        role_stmt = select(Role).where(and_(Role.id == role_id, Role.tenant_id == tenant_id))
        role_result = await self.db.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundError("Role not found")

        # Get direct permissions
        direct_stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        direct_result = await self.db.execute(direct_stmt)
        direct_permissions = [PermissionResponse.model_validate(p) for p in direct_result.scalars().all()]

        inherited_permissions = []
        if include_inherited and role.parent_id:
            # Recursively get parent role permissions
            parent_perms = await self.get_role_permissions(role.parent_id, tenant_id, include_inherited)
            inherited_permissions = parent_perms.effective_permissions

        # Combine and deduplicate effective permissions
        effective_permissions = direct_permissions[:]
        direct_perm_ids = {p.id for p in direct_permissions}
        
        for inherited_perm in inherited_permissions:
            if inherited_perm.id not in direct_perm_ids:
                effective_permissions.append(inherited_perm)

        return RolePermissionsListResponse(
            direct_permissions=direct_permissions,
            inherited_permissions=inherited_permissions,
            effective_permissions=effective_permissions
        )

    async def remove_permission_from_role(
        self,
        role_id: UUID_T,
        permission_id: UUID_T,
        tenant_id: UUID_T
    ) -> bool:
        """
        Remove a specific permission from a role.
        """
        # Verify role exists and belongs to tenant
        role_stmt = select(Role).where(and_(Role.id == role_id, Role.tenant_id == tenant_id))
        role_result = await self.db.execute(role_stmt)
        if not role_result.scalar_one_or_none():
            raise NotFoundError("Role not found")

        # Remove the assignment
        delete_stmt = delete(RolePermission).where(
            and_(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            )
        )
        result = await self.db.execute(delete_stmt)
        await self.db.commit()
        
        return result.rowcount > 0

    async def remove_all_permissions_from_role(
        self,
        role_id: UUID_T,
        tenant_id: UUID_T
    ) -> bool:
        """
        Remove all permissions from a role.
        """
        # Verify role exists and belongs to tenant
        role_stmt = select(Role).where(and_(Role.id == role_id, Role.tenant_id == tenant_id))
        role_result = await self.db.execute(role_stmt)
        if not role_result.scalar_one_or_none():
            raise NotFoundError("Role not found")

        # Remove all assignments for this role
        delete_stmt = delete(RolePermission).where(RolePermission.role_id == role_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        return True

    async def get_user_effective_permissions(
        self,
        user_id: UUID_T,
        tenant_id: UUID_T,
        resource_type: Optional[str] = None
    ) -> List[PermissionResponse]:
        """
        Get all effective permissions for a user based on their role assignments.
        This includes both direct role permissions and inherited permissions.
        """
        # Get all roles assigned to the user (both direct and via groups)
        from sqlalchemy import or_, union_all
        from ..models import UserRole, UserGroup, GroupRole
        
        # Direct role assignments
        direct_roles_stmt = (
            select(Role.id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(and_(UserRole.user_id == user_id, Role.tenant_id == tenant_id))
        )
        
        # Roles via group membership
        group_roles_stmt = (
            select(Role.id)
            .join(GroupRole, GroupRole.role_id == Role.id)
            .join(UserGroup, UserGroup.group_id == GroupRole.group_id)
            .where(and_(UserGroup.user_id == user_id, Role.tenant_id == tenant_id))
        )
        
        # Combine both queries
        all_roles_stmt = union_all(direct_roles_stmt, group_roles_stmt)
        all_roles_result = await self.db.execute(all_roles_stmt)
        role_ids = [row[0] for row in all_roles_result.fetchall()]
        
        if not role_ids:
            return []
        
        # Get all permissions for these roles
        permissions_stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id.in_(role_ids))
        )
        
        if resource_type:
            permissions_stmt = permissions_stmt.where(Permission.resource_type == resource_type)
        
        permissions_result = await self.db.execute(permissions_stmt)
        permissions = permissions_result.scalars().all()
        
        # Deduplicate permissions by ID
        seen_ids = set()
        unique_permissions = []
        for perm in permissions:
            if perm.id not in seen_ids:
                seen_ids.add(perm.id)
                unique_permissions.append(PermissionResponse.model_validate(perm))
        
        return unique_permissions