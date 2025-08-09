"""
Dynamic RBAC Service

Replaces hardcoded scope resolution with database-driven permission queries.
Supports role inheritance, group-based assignments, and caching for performance.
"""

import asyncio
import json
import time
from typing import Dict, List, Set, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from src.models import User, Role, Group, Permission, UserRole, UserGroup, GroupRole, RolePermission
from src.core.cache import CacheManager
from src.core.exceptions import NotFoundError, ValidationError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RBACService:
    """
    Dynamic Role-Based Access Control Service
    
    Provides database-driven permission resolution with caching,
    role inheritance, and group-based access control.
    """
    
    # Cache configuration
    CACHE_TTL = 300  # 5 minutes
    CACHE_PREFIX = "rbac"
    
    def __init__(self, db: AsyncSession, cache_manager: Optional[CacheManager] = None):
        self.db = db
        self.cache = cache_manager
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_queries": 0,
            "permission_resolutions": 0
        }
    
    async def get_user_scopes(self, user: User) -> List[str]:
        """
        Get all scopes/permissions for a user.
        
        This is the main method that replaces the hardcoded _get_user_scopes()
        in the authentication service.
        
        Args:
            user: User object
            
        Returns:
            List of permission scope strings (e.g., ['user:read', 'tenant:write'])
        """
        start_time = time.time()
        self._stats["permission_resolutions"] += 1
        
        try:
            # Check cache first
            cache_key = f"{self.CACHE_PREFIX}:user_scopes:{user.id}"
            if self.cache:
                cached_scopes = await self.cache.get(cache_key)
                if cached_scopes:
                    self._stats["cache_hits"] += 1
                    logger.debug(f"Cache hit for user scopes: {user.id}")
                    return json.loads(cached_scopes)
            
            self._stats["cache_misses"] += 1
            logger.debug(f"Cache miss for user scopes: {user.id}, resolving from database")
            
            # Resolve permissions from database
            scopes = await self._resolve_user_permissions(user)
            
            # Cache results
            if self.cache:
                await self.cache.set(cache_key, json.dumps(scopes), ttl=self.CACHE_TTL)
            
            resolution_time = time.time() - start_time
            logger.info(f"Resolved {len(scopes)} scopes for user {user.id} in {resolution_time:.3f}s")
            
            return scopes
            
        except Exception as e:
            logger.error(f"Error resolving user scopes for {user.id}: {e}")
            # SECURITY: Fail secure - deny all access if RBAC resolution fails
            logger.warning(f"RBAC resolution failed for user {user.id}. Denying all access for security.")
            return []  # Return empty scopes - no permissions
    
    async def _resolve_user_permissions(self, user: User) -> List[str]:
        """Resolve user permissions from roles and groups."""
        all_scopes = set()
        
        # 0. Check for superadmin attribute (legacy compatibility)
        if user.attributes and user.attributes.get('role') == 'superadmin':
            logger.info(f"User {user.id} has superadmin attribute, granting full access")
            return self._get_superadmin_scopes()
        
        # 1. Get direct role assignments
        direct_roles = await self.get_user_direct_roles(user.id)
        logger.debug(f"User {user.id} has {len(direct_roles)} direct roles")
        
        # 2. Get group-based role assignments
        group_roles = await self.get_user_group_roles(user.id)
        logger.debug(f"User {user.id} has {len(group_roles)} group-based roles")
        
        # 3. Combine all roles
        all_roles = direct_roles + group_roles
        
        # 4. Resolve role inheritance
        resolved_roles = await self.resolve_role_inheritance(all_roles)
        logger.debug(f"User {user.id} has {len(resolved_roles)} roles after inheritance resolution")
        
        # 5. Get permissions for all roles
        for role in resolved_roles:
            role_permissions = await self.get_role_permissions(role.id)
            role_scopes = self._permissions_to_scopes(role_permissions)
            all_scopes.update(role_scopes)
        
        # 6. Apply permission conflict resolution
        final_scopes = await self._resolve_permission_conflicts(list(all_scopes), resolved_roles)
        
        return final_scopes
    
    def _get_superadmin_scopes(self) -> List[str]:
        """Return full superadmin scopes (copied from hardcoded logic)."""
        return [
            "user:profile",
            "platform:admin",  # Global platform administration
            "tenant:read", "tenant:write", "tenant:admin", "tenant:global",
            "user:read", "user:write", "user:admin", "user:global",
            "service_account:read", "service_account:write", "service_account:admin", "service_account:global",
            "role:read", "role:write", "role:admin", "role:global",
            "group:read", "group:write", "group:admin", "group:global",
            "permission:read", "permission:write", "permission:admin", "permission:global",
            "resource:read", "resource:write", "resource:admin", "resource:global",
            "system:admin",  # System-level administration
            "audit:read", "audit:write"  # Audit log access
        ]
    
    async def get_user_direct_roles(self, user_id: UUID) -> List[Role]:
        """Get roles directly assigned to user."""
        self._stats["db_queries"] += 1
        
        query = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.is_active == True,
                    Role.is_active == True,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > text("NOW()")
                    )
                )
            )
            .options(selectinload(Role.parent_role))
        )
        
        result = await self.db.execute(query)
        roles = result.scalars().all()
        
        logger.debug(f"Found {len(roles)} direct roles for user {user_id}")
        return list(roles)
    
    async def get_user_group_roles(self, user_id: UUID) -> List[Role]:
        """Get roles assigned through group membership."""
        self._stats["db_queries"] += 1
        
        query = (
            select(Role)
            .join(GroupRole, GroupRole.role_id == Role.id)
            .join(Group, Group.id == GroupRole.group_id)
            .join(UserGroup, UserGroup.group_id == Group.id)
            .where(
                and_(
                    UserGroup.user_id == user_id,
                    Group.is_active == True,
                    Role.is_active == True
                )
            )
            .options(selectinload(Role.parent_role))
        )
        
        result = await self.db.execute(query)
        roles = result.scalars().all()
        
        logger.debug(f"Found {len(roles)} group-based roles for user {user_id}")
        return list(roles)
    
    async def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions assigned to a role."""
        self._stats["db_queries"] += 1
        
        query = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                and_(
                    RolePermission.role_id == role_id,
                    Permission.is_active == True
                )
            )
        )
        
        result = await self.db.execute(query)
        permissions = result.scalars().all()
        
        logger.debug(f"Found {len(permissions)} permissions for role {role_id}")
        return list(permissions)
    
    async def resolve_role_inheritance(self, roles: List[Role]) -> List[Role]:
        """
        Resolve role inheritance hierarchy.
        
        Child roles inherit permissions from parent roles.
        """
        resolved_roles = set(roles)
        
        # Build inheritance chain for each role
        for role in roles:
            parent_chain = await self._get_role_parent_chain(role)
            resolved_roles.update(parent_chain)
        
        logger.debug(f"Role inheritance resolved: {len(roles)} -> {len(resolved_roles)} roles")
        return list(resolved_roles)
    
    async def _get_role_parent_chain(self, role: Role) -> List[Role]:
        """Get the full parent chain for a role."""
        parent_chain = []
        current_role = role
        visited_roles = set()  # Prevent circular inheritance
        
        while current_role.parent_role_id and current_role.id not in visited_roles:
            visited_roles.add(current_role.id)
            
            # Get parent role
            parent_result = await self.db.execute(
                select(Role)
                .where(
                    and_(
                        Role.id == current_role.parent_role_id,
                        Role.is_active == True
                    )
                )
                .options(selectinload(Role.parent_role))
            )
            
            parent_role = parent_result.scalar_one_or_none()
            if parent_role:
                parent_chain.append(parent_role)
                current_role = parent_role
            else:
                break
        
        return parent_chain
    
    def _permissions_to_scopes(self, permissions: List[Permission]) -> List[str]:
        """Convert Permission objects to scope strings."""
        scopes = []
        
        for permission in permissions:
            # Build scope strings from permission attributes
            # resource_type is already a string from the database, not an enum object
            resource_type = permission.resource_type if permission.resource_type else "general"
            
            for action in permission.actions:
                # action is also already a string from the database
                scope = f"{resource_type}:{action}"
                scopes.append(scope)
            
            # Add resource-specific scopes if resource_id is set
            if permission.resource_id:
                for action in permission.actions:
                    resource_scope = f"{resource_type}:{action}:{permission.resource_id}"
                    scopes.append(resource_scope)
        
        return scopes
    
    async def _resolve_permission_conflicts(self, scopes: List[str], roles: List[Role]) -> List[str]:
        """
        Resolve permission conflicts using role priority.
        
        Higher priority roles can override lower priority permissions.
        """
        # Sort roles by priority (higher priority first)
        sorted_roles = sorted(roles, key=lambda r: r.priority, reverse=True)
        
        # For now, just return unique scopes
        # In the future, could implement more complex conflict resolution
        unique_scopes = list(set(scopes))
        
        logger.debug(f"Resolved {len(scopes)} scopes to {len(unique_scopes)} unique scopes")
        return unique_scopes
    
    async def _get_fallback_scopes(self, user: User) -> List[str]:
        """
        DEPRECATED: This method is a security vulnerability and should not be used.
        
        Previously provided fallback scopes when dynamic resolution failed,
        but this violates the principle of "fail secure". If RBAC resolution
        fails, the system should deny access, not grant fallback permissions.
        
        SECURITY WARNING: Always return empty list (no permissions) on failure.
        """
        logger.error(f"SECURITY WARNING: _get_fallback_scopes called for user {user.id}. This method should not be used!")
        return []  # Always deny access - fail secure
    
    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate cached permissions for a user."""
        if self.cache:
            cache_key = f"{self.CACHE_PREFIX}:user_scopes:{user_id}"
            await self.cache.delete(cache_key)
            logger.info(f"Invalidated cache for user {user_id}")
    
    async def invalidate_role_cache(self, role_id: UUID) -> None:
        """Invalidate cached permissions for all users with a role."""
        if not self.cache:
            return
        
        # Get all users with this role (direct or through groups)
        direct_users_query = (
            select(UserRole.user_id)
            .where(UserRole.role_id == role_id)
        )
        
        group_users_query = (
            select(UserGroup.user_id)
            .join(GroupRole, GroupRole.group_id == UserGroup.group_id)
            .where(GroupRole.role_id == role_id)
        )
        
        direct_result = await self.db.execute(direct_users_query)
        group_result = await self.db.execute(group_users_query)
        
        affected_users = set()
        affected_users.update([row[0] for row in direct_result.fetchall()])
        affected_users.update([row[0] for row in group_result.fetchall()])
        
        # Invalidate cache for all affected users
        for user_id in affected_users:
            await self.invalidate_user_cache(user_id)
        
        logger.info(f"Invalidated cache for {len(affected_users)} users affected by role {role_id}")
    
    async def get_effective_permissions(self, user_id: UUID) -> Dict[str, any]:
        """
        Get detailed effective permissions for a user.
        
        Returns comprehensive permission information for debugging and auditing.
        """
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Get role and permission details
        direct_roles = await self.get_user_direct_roles(user_id)
        group_roles = await self.get_user_group_roles(user_id)
        all_roles = direct_roles + group_roles
        resolved_roles = await self.resolve_role_inheritance(all_roles)
        
        # Get permissions for each role
        role_permissions = {}
        for role in resolved_roles:
            permissions = await self.get_role_permissions(role.id)
            role_permissions[role.name] = [
                {
                    "name": p.name,
                    "resource_type": p.resource_type.value if p.resource_type else None,
                    "actions": [a.value for a in p.actions],
                    "resource_id": str(p.resource_id) if p.resource_id else None
                }
                for p in permissions
            ]
        
        # Get final scopes
        scopes = await self.get_user_scopes(user)
        
        return {
            "user_id": str(user_id),
            "direct_roles": [{"id": str(r.id), "name": r.name, "priority": r.priority} for r in direct_roles],
            "group_roles": [{"id": str(r.id), "name": r.name, "priority": r.priority} for r in group_roles],
            "resolved_roles": [{"id": str(r.id), "name": r.name, "priority": r.priority} for r in resolved_roles],
            "role_permissions": role_permissions,
            "final_scopes": scopes,
            "resolution_stats": self._stats.copy()
        }
    
    def get_stats(self) -> Dict[str, int]:
        """Get performance statistics for monitoring."""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_queries": 0,
            "permission_resolutions": 0
        }


class RBACServiceFactory:
    """Factory for creating RBACService instances with proper dependencies."""
    
    @staticmethod
    async def create(db: AsyncSession, use_cache: bool = True) -> RBACService:
        """Create RBACService with optional caching."""
        cache_manager = None
        
        if use_cache:
            try:
                from src.core.cache import get_cache_manager
                cache_manager = await get_cache_manager()
            except ImportError:
                logger.warning("Cache manager not available, running without cache")
        
        return RBACService(db, cache_manager)


# Convenience functions for common operations
async def get_user_permissions(db: AsyncSession, user: User) -> List[str]:
    """Convenience function to get user permissions."""
    rbac_service = await RBACServiceFactory.create(db)
    return await rbac_service.get_user_scopes(user)


async def invalidate_user_permissions(db: AsyncSession, user_id: UUID) -> None:
    """Convenience function to invalidate user permissions cache."""
    rbac_service = await RBACServiceFactory.create(db)
    await rbac_service.invalidate_user_cache(user_id)


async def get_permission_details(db: AsyncSession, user_id: UUID) -> Dict[str, any]:
    """Convenience function to get detailed permission information."""
    rbac_service = await RBACServiceFactory.create(db)
    return await rbac_service.get_effective_permissions(user_id)