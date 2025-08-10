"""
Role Service for Module 4: Role Management

Provides comprehensive role management functionality including:
- Role CRUD operations
- Role hierarchy management 
- Role assignment to users
- Role validation and circular dependency detection
- Bulk operations
"""
import asyncio
from typing import List, Optional, Dict, Any, Tuple, Set
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from ..models import Role, UserRole, User, Tenant, RoleType
from ..schemas.role import (
    RoleCreate, RoleUpdate, RoleQuery, RoleResponse, RoleDetailResponse, 
    RoleListResponse, UserRoleAssignmentCreate, UserRoleAssignmentResponse,
    BulkRoleAssignmentRequest, BulkRoleAssignmentResponse, RoleHierarchyResponse,
    RoleValidationResponse
)
from ..core.exceptions import ValidationError, ConflictError, NotFoundError


class RoleService:
    """Service class for role management operations."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_role(
        self, 
        role_data: RoleCreate, 
        tenant_id: UUID, 
        created_by: Optional[UUID] = None
    ) -> RoleResponse:
        """
        Create a new role.
        
        Args:
            role_data: Role creation data
            tenant_id: Tenant ID for the role
            created_by: ID of user creating the role
            
        Returns:
            Created role response
            
        Raises:
            ValidationError: If role data is invalid
            ConflictError: If role name already exists in tenant
        """
        # Validate parent role if specified
        if role_data.parent_role_id:
            await self._validate_parent_role(role_data.parent_role_id, tenant_id)
            
            # Check for circular dependency
            if await self._would_create_circular_dependency(
                parent_id=role_data.parent_role_id,
                tenant_id=tenant_id
            ):
                raise ValidationError("Cannot create role: would create circular dependency")

        # Check if role name already exists in tenant
        existing = await self.db.execute(
            select(Role).where(
                and_(
                    Role.tenant_id == tenant_id,
                    Role.name == role_data.name
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Role '{role_data.name}' already exists in this tenant")

        # Create role
        role = Role(
            tenant_id=tenant_id,
            name=role_data.name,
            display_name=role_data.display_name,
            description=role_data.description,
            type=role_data.type,
            parent_role_id=role_data.parent_role_id,
            is_assignable=role_data.is_assignable,
            priority=role_data.priority,
            role_metadata=role_data.role_metadata,
            is_active=role_data.is_active,
            created_by=created_by
        )

        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)

        return RoleResponse.model_validate(role)

    async def get_role(self, role_id: UUID, tenant_id: UUID) -> RoleDetailResponse:
        """
        Get role by ID with detailed information.
        
        Args:
            role_id: Role ID
            tenant_id: Tenant ID for access control
            
        Returns:
            Detailed role response
            
        Raises:
            NotFoundError: If role not found
        """
        # Get role first
        role_stmt = select(Role).where(
            and_(
                Role.id == role_id,
                Role.tenant_id == tenant_id
            )
        )
        
        role_result = await self.db.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        
        if not role:
            raise NotFoundError(f"Role with ID {role_id} not found")

        # Get parent role if exists
        parent_role = None
        if role.parent_role_id:
            parent_stmt = select(Role).where(Role.id == role.parent_role_id)
            parent_result = await self.db.execute(parent_stmt)
            parent_role = parent_result.scalar_one_or_none()
        
        # Get child roles
        child_stmt = select(Role).where(
            and_(
                Role.parent_role_id == role_id,
                Role.is_active == True
            )
        )
        child_result = await self.db.execute(child_stmt)
        child_roles = child_result.scalars().all()
        
        # Get user assignment count
        user_count_stmt = select(func.count(UserRole.id)).where(
            and_(
                UserRole.role_id == role_id,
                UserRole.is_active == True
            )
        )
        user_count_result = await self.db.execute(user_count_stmt)
        user_count = user_count_result.scalar() or 0

        # Build detailed response
        response_data = {
            "id": role.id,
            "tenant_id": role.tenant_id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "type": role.type,
            "parent_role_id": role.parent_role_id,
            "is_assignable": role.is_assignable,
            "priority": role.priority,
            "role_metadata": role.role_metadata,
            "is_active": role.is_active,
            "created_by": role.created_by,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "parent_role": RoleResponse.model_validate(parent_role) if parent_role else None,
            "child_roles": [RoleResponse.model_validate(child) for child in child_roles],
            "user_count": user_count
        }

        return RoleDetailResponse.model_validate(response_data)

    async def list_roles(
        self, 
        query: RoleQuery, 
        tenant_id: UUID
    ) -> RoleListResponse:
        """
        List roles with filtering and pagination.
        
        Args:
            query: Query parameters
            tenant_id: Tenant ID for access control
            
        Returns:
            Paginated role list
        """
        # Build base query
        stmt = select(Role).where(Role.tenant_id == tenant_id)
        count_stmt = select(func.count(Role.id)).where(Role.tenant_id == tenant_id)

        # Apply filters
        if query.type is not None:
            stmt = stmt.where(Role.type == query.type)
            count_stmt = count_stmt.where(Role.type == query.type)

        if query.is_assignable is not None:
            stmt = stmt.where(Role.is_assignable == query.is_assignable)
            count_stmt = count_stmt.where(Role.is_assignable == query.is_assignable)

        if query.is_active is not None:
            stmt = stmt.where(Role.is_active == query.is_active)
            count_stmt = count_stmt.where(Role.is_active == query.is_active)

        if query.parent_role_id is not None:
            stmt = stmt.where(Role.parent_role_id == query.parent_role_id)
            count_stmt = count_stmt.where(Role.parent_role_id == query.parent_role_id)

        if query.search:
            search_term = f"%{query.search}%"
            search_filter = or_(
                Role.name.ilike(search_term),
                Role.display_name.ilike(search_term),
                Role.description.ilike(search_term)
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        # Apply sorting
        if query.sort_by == "name":
            order_column = Role.name
        elif query.sort_by == "display_name":
            order_column = Role.display_name
        elif query.sort_by == "type":
            order_column = Role.type
        elif query.sort_by == "priority":
            order_column = Role.priority
        elif query.sort_by == "created_at":
            order_column = Role.created_at
        else:
            order_column = Role.name

        if query.sort_order == "desc":
            stmt = stmt.order_by(order_column.desc())
        else:
            stmt = stmt.order_by(order_column.asc())

        # Apply pagination
        stmt = stmt.offset(query.skip).limit(query.limit)

        # Execute queries
        roles_result = await self.db.execute(stmt)
        roles = roles_result.scalars().all()
        
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()

        return RoleListResponse(
            items=[RoleResponse.model_validate(role) for role in roles],
            total=total,
            skip=query.skip,
            limit=query.limit
        )

    async def update_role(
        self, 
        role_id: UUID, 
        role_data: RoleUpdate, 
        tenant_id: UUID
    ) -> RoleResponse:
        """
        Update an existing role.
        
        Args:
            role_id: Role ID to update
            role_data: Updated role data
            tenant_id: Tenant ID for access control
            
        Returns:
            Updated role response
            
        Raises:
            NotFoundError: If role not found
            ValidationError: If update would create circular dependency
        """
        # Get existing role
        role = await self._get_role_by_id(role_id, tenant_id)

        # Validate parent role change
        if role_data.parent_role_id is not None:
            if role_data.parent_role_id != role.parent_role_id:
                await self._validate_parent_role(role_data.parent_role_id, tenant_id)
                
                # Check for circular dependency
                if await self._would_create_circular_dependency(
                    role_id=role_id,
                    parent_id=role_data.parent_role_id,
                    tenant_id=tenant_id
                ):
                    raise ValidationError("Cannot update role: would create circular dependency")

        # Update fields
        update_data = {}
        for field, value in role_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        if update_data:
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            await self.db.execute(
                update(Role)
                .where(
                    and_(
                        Role.id == role_id,
                        Role.tenant_id == tenant_id
                    )
                )
                .values(**update_data)
            )
            await self.db.commit()

            # Refresh role
            await self.db.refresh(role)

        return RoleResponse.model_validate(role)

    async def delete_role(self, role_id: UUID, tenant_id: UUID) -> bool:
        """
        Delete a role (soft delete by setting is_active=False).
        
        Args:
            role_id: Role ID to delete
            tenant_id: Tenant ID for access control
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If role not found
            ValidationError: If role has dependencies
        """
        role = await self._get_role_by_id(role_id, tenant_id)

        # Check if role has child roles
        child_roles = await self.db.execute(
            select(func.count(Role.id))
            .where(
                and_(
                    Role.parent_role_id == role_id,
                    Role.is_active == True
                )
            )
        )
        if child_roles.scalar() > 0:
            raise ValidationError("Cannot delete role: has active child roles")

        # Check if role has active user assignments
        active_assignments = await self.db.execute(
            select(func.count(UserRole.id))
            .where(
                and_(
                    UserRole.role_id == role_id,
                    UserRole.is_active == True
                )
            )
        )
        if active_assignments.scalar() > 0:
            raise ValidationError("Cannot delete role: has active user assignments")

        # Soft delete
        await self.db.execute(
            update(Role)
            .where(
                and_(
                    Role.id == role_id,
                    Role.tenant_id == tenant_id
                )
            )
            .values(
                is_active=False,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()

        return True

    async def assign_role_to_user(
        self, 
        assignment: UserRoleAssignmentCreate,
        tenant_id: UUID,
        granted_by: Optional[UUID] = None
    ) -> UserRoleAssignmentResponse:
        """
        Assign a role to a user.
        
        Args:
            assignment: Assignment data
            tenant_id: Tenant ID for access control
            granted_by: ID of user granting the role
            
        Returns:
            Role assignment response
            
        Raises:
            NotFoundError: If role or user not found
            ConflictError: If assignment already exists
            ValidationError: If role is not assignable
        """
        # Validate role exists and is assignable
        role = await self._get_role_by_id(assignment.role_id, tenant_id)
        if not role.is_assignable:
            raise ValidationError("Role is not assignable")

        # Validate user exists in tenant
        user = await self.db.execute(
            select(User).where(
                and_(
                    User.id == assignment.user_id,
                    User.tenant_id == tenant_id
                )
            )
        )
        if not user.scalar_one_or_none():
            raise NotFoundError(f"User with ID {assignment.user_id} not found")

        # Check if assignment already exists
        existing = await self.db.execute(
            select(UserRole).where(
                and_(
                    UserRole.user_id == assignment.user_id,
                    UserRole.role_id == assignment.role_id,
                    UserRole.is_active == True
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("User already has this role assigned")

        # Create assignment
        user_role = UserRole(
            user_id=assignment.user_id,
            role_id=assignment.role_id,
            granted_by=granted_by,
            expires_at=assignment.expires_at,
            is_active=assignment.is_active
        )

        self.db.add(user_role)
        await self.db.commit()
        await self.db.refresh(user_role)

        # Build response data manually to avoid relationship issues
        response_data = {
            "id": user_role.id,
            "user_id": user_role.user_id,
            "role_id": user_role.role_id,
            "granted_by": user_role.granted_by,
            "granted_at": user_role.granted_at,
            "expires_at": user_role.expires_at,
            "is_active": user_role.is_active,
            "created_at": user_role.created_at,
            "updated_at": user_role.updated_at,
            "role": RoleResponse.model_validate(role)
        }

        return UserRoleAssignmentResponse.model_validate(response_data)

    async def get_role_hierarchy(self, role_id: UUID, tenant_id: UUID) -> RoleHierarchyResponse:
        """
        Get complete role hierarchy for a role.
        
        Args:
            role_id: Role ID
            tenant_id: Tenant ID for access control
            
        Returns:
            Role hierarchy response
        """
        role = await self._get_role_by_id(role_id, tenant_id)

        # Get ancestors (parents up the chain)
        ancestors = await self._get_role_ancestors(role_id, tenant_id)
        
        # Get descendants (children down the chain) 
        descendants = await self._get_role_descendants(role_id, tenant_id)
        
        # Build inheritance path
        inheritance_path = [ancestor.name for ancestor in ancestors] + [role.name]

        return RoleHierarchyResponse(
            role=RoleResponse.model_validate(role),
            ancestors=[RoleResponse.model_validate(r) for r in ancestors],
            descendants=[RoleResponse.model_validate(r) for r in descendants],
            inheritance_path=inheritance_path
        )

    async def validate_role_hierarchy(
        self, 
        role_id: Optional[UUID], 
        parent_role_id: Optional[UUID],
        tenant_id: UUID
    ) -> RoleValidationResponse:
        """
        Validate role hierarchy for circular dependencies.
        
        Args:
            role_id: Role ID (None for new roles)
            parent_role_id: Proposed parent role ID
            tenant_id: Tenant ID
            
        Returns:
            Validation response
        """
        errors = []
        warnings = []
        circular_dependency = False

        if parent_role_id:
            # Check if parent exists
            try:
                await self._get_role_by_id(parent_role_id, tenant_id)
            except NotFoundError:
                errors.append(f"Parent role {parent_role_id} not found")

            # Check for circular dependency
            if role_id:
                circular_dependency = await self._would_create_circular_dependency(
                    role_id=role_id,
                    parent_id=parent_role_id,
                    tenant_id=tenant_id
                )
                if circular_dependency:
                    errors.append("Would create circular dependency in role hierarchy")

        return RoleValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            circular_dependency=circular_dependency
        )

    # Private helper methods
    
    async def _get_role_by_id(self, role_id: UUID, tenant_id: UUID) -> Role:
        """Get role by ID or raise NotFoundError."""
        result = await self.db.execute(
            select(Role).where(
                and_(
                    Role.id == role_id,
                    Role.tenant_id == tenant_id
                )
            )
        )
        role = result.scalar_one_or_none()
        if not role:
            raise NotFoundError(f"Role with ID {role_id} not found")
        return role

    async def _validate_parent_role(self, parent_role_id: UUID, tenant_id: UUID) -> None:
        """Validate parent role exists."""
        await self._get_role_by_id(parent_role_id, tenant_id)

    async def _would_create_circular_dependency(
        self, 
        role_id: Optional[UUID] = None,
        parent_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None
    ) -> bool:
        """Check if setting parent_id as parent would create circular dependency."""
        if not parent_id or not role_id:
            return False

        # Get all ancestors of the proposed parent
        ancestors = await self._get_role_ancestor_ids(parent_id, tenant_id)
        
        # If role_id is in the ancestors, it would create a cycle
        return role_id in ancestors

    async def _get_role_ancestor_ids(self, role_id: UUID, tenant_id: UUID) -> Set[UUID]:
        """Get all ancestor role IDs."""
        ancestors = set()
        current_id = role_id

        while current_id:
            result = await self.db.execute(
                select(Role.parent_role_id).where(
                    and_(
                        Role.id == current_id,
                        Role.tenant_id == tenant_id,
                        Role.is_active == True
                    )
                )
            )
            parent_id = result.scalar_one_or_none()
            
            if parent_id:
                if parent_id in ancestors:
                    # Circular reference detected
                    break
                ancestors.add(parent_id)
                current_id = parent_id
            else:
                break

        return ancestors

    async def _get_role_ancestors(self, role_id: UUID, tenant_id: UUID) -> List[Role]:
        """Get all ancestor roles."""
        ancestors = []
        current_id = role_id

        while current_id:
            result = await self.db.execute(
                select(Role).where(
                    and_(
                        Role.id == current_id,
                        Role.tenant_id == tenant_id,
                        Role.is_active == True
                    )
                )
            )
            role = result.scalar_one_or_none()
            
            if role and role.parent_role_id:
                parent_result = await self.db.execute(
                    select(Role).where(Role.id == role.parent_role_id)
                )
                parent = parent_result.scalar_one_or_none()
                if parent:
                    ancestors.append(parent)
                    current_id = parent.id
                else:
                    break
            else:
                break

        return list(reversed(ancestors))  # Return from root to immediate parent

    async def _get_role_descendants(self, role_id: UUID, tenant_id: UUID) -> List[Role]:
        """Get all descendant roles."""
        descendants = []
        
        # Get direct children
        children_result = await self.db.execute(
            select(Role).where(
                and_(
                    Role.parent_role_id == role_id,
                    Role.tenant_id == tenant_id,
                    Role.is_active == True
                )
            )
        )
        children = children_result.scalars().all()
        
        # Recursively get grandchildren
        for child in children:
            descendants.append(child)
            grandchildren = await self._get_role_descendants(child.id, tenant_id)
            descendants.extend(grandchildren)
        
        return descendants