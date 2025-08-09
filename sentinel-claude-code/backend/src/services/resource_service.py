"""
ResourceService for Module 7: Hierarchical resource management
"""
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID as UUID_T
from sqlalchemy import select, and_, or_, func, text, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from src.models import Resource, ResourceType, Permission
from src.schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceResponse, ResourceDetailResponse,
    ResourceTreeNode, ResourceTreeResponse, ResourceQuery, ResourceListResponse,
    ResourceStatistics, ResourcePermissionResponse
)
from src.core.exceptions import NotFoundError, ConflictError, ValidationError


class ResourceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_resource(self, resource_data: ResourceCreate) -> ResourceResponse:
        """Create a new resource with hierarchy validation."""
        
        # Check if code is unique within tenant and type
        existing_resource = await self.db.execute(
            select(Resource).where(
                and_(
                    Resource.tenant_id == resource_data.tenant_id,
                    Resource.type == resource_data.type,
                    Resource.code == resource_data.code
                )
            )
        )
        if existing_resource.scalar_one_or_none():
            raise ConflictError(f"Resource code '{resource_data.code}' already exists for type '{resource_data.type}'")

        # Validate parent if specified
        parent_resource = None
        if resource_data.parent_id:
            parent_result = await self.db.execute(
                select(Resource).where(
                    and_(
                        Resource.id == resource_data.parent_id,
                        Resource.tenant_id == resource_data.tenant_id
                    )
                )
            )
            parent_resource = parent_result.scalar_one_or_none()
            if not parent_resource:
                raise NotFoundError(f"Parent resource with ID {resource_data.parent_id} not found")
            
            # Validate hierarchy rules (basic validation)
            await self._validate_hierarchy_rules(resource_data.type, parent_resource.type)

        # Create resource
        resource = Resource(
            tenant_id=resource_data.tenant_id,
            type=resource_data.type,
            name=resource_data.name,
            code=resource_data.code,
            parent_id=resource_data.parent_id,
            attributes=resource_data.attributes,
            workflow_enabled=resource_data.workflow_enabled,
            workflow_config=resource_data.workflow_config,
            is_active=resource_data.is_active
        )

        # Set materialized path
        if parent_resource:
            resource.path = f"{parent_resource.path}{resource.id}/"
        else:
            resource.path = f"/{resource.id}/"

        self.db.add(resource)
        await self.db.commit()
        await self.db.refresh(resource)

        return ResourceResponse.model_validate(resource)

    async def get_resource(self, resource_id: UUID_T, tenant_id: UUID_T) -> ResourceResponse:
        """Get a resource by ID."""
        result = await self.db.execute(
            select(Resource).where(
                and_(
                    Resource.id == resource_id,
                    Resource.tenant_id == tenant_id
                )
            )
        )
        resource = result.scalar_one_or_none()
        if not resource:
            raise NotFoundError(f"Resource with ID {resource_id} not found")

        return ResourceResponse.model_validate(resource)

    async def get_resource_detail(self, resource_id: UUID_T, tenant_id: UUID_T) -> ResourceDetailResponse:
        """Get detailed resource information."""
        resource = await self.get_resource(resource_id, tenant_id)
        
        # Get additional details
        resource_obj = await self.db.execute(
            select(Resource).where(Resource.id == resource_id)
        )
        resource_obj = resource_obj.scalar_one()

        # Count children
        child_count_result = await self.db.execute(
            select(func.count(Resource.id)).where(Resource.parent_id == resource_id)
        )
        child_count = child_count_result.scalar()

        return ResourceDetailResponse(
            **resource.model_dump(),
            depth=resource_obj.get_depth(),
            hierarchy_level_name=resource_obj.hierarchy_level_name,
            ancestor_ids=resource_obj.get_ancestors(),
            child_count=child_count
        )

    async def list_resources(
        self, 
        tenant_id: Optional[UUID_T],
        query: ResourceQuery
    ) -> ResourceListResponse:
        """List resources with filtering and pagination."""
        
        # Build base query
        conditions = []
        if tenant_id is not None:
            conditions.append(Resource.tenant_id == tenant_id)
        
        stmt = select(Resource)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Apply filters
        if query.type:
            stmt = stmt.where(Resource.type == query.type)
        
        if query.parent_id:
            stmt = stmt.where(Resource.parent_id == query.parent_id)
        elif query.parent_id is None and hasattr(query, '_parent_id_filter_none'):
            # Filter for root resources only
            stmt = stmt.where(Resource.parent_id.is_(None))
        
        if query.is_active is not None:
            stmt = stmt.where(Resource.is_active == query.is_active)
        
        if query.search:
            search_term = f"%{query.search}%"
            stmt = stmt.where(
                or_(
                    Resource.name.ilike(search_term),
                    Resource.code.ilike(search_term)
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()

        # Apply sorting
        if query.sort_by == "name":
            order_col = Resource.name
        elif query.sort_by == "code":
            order_col = Resource.code
        elif query.sort_by == "type":
            order_col = Resource.type
        elif query.sort_by == "created_at":
            order_col = Resource.created_at
        else:
            order_col = Resource.name

        if query.sort_order == "desc":
            order_col = order_col.desc()

        stmt = stmt.order_by(order_col)

        # Apply pagination
        offset = (query.page - 1) * query.limit
        stmt = stmt.offset(offset).limit(query.limit)

        # Execute query
        result = await self.db.execute(stmt)
        resources = result.scalars().all()

        # Build response
        items = [ResourceResponse.model_validate(resource) for resource in resources]
        
        return ResourceListResponse(
            items=items,
            total=total,
            page=query.page,
            limit=query.limit,
            has_next=(query.page * query.limit) < total,
            has_prev=query.page > 1
        )

    async def update_resource(
        self, 
        resource_id: UUID_T, 
        tenant_id: UUID_T, 
        update_data: ResourceUpdate
    ) -> ResourceResponse:
        """Update a resource."""
        
        # Get existing resource
        result = await self.db.execute(
            select(Resource).where(
                and_(
                    Resource.id == resource_id,
                    Resource.tenant_id == tenant_id
                )
            )
        )
        resource = result.scalar_one_or_none()
        if not resource:
            raise NotFoundError(f"Resource with ID {resource_id} not found")

        # Apply updates
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        # Handle parent_id change (hierarchy move)
        if 'parent_id' in update_dict:
            new_parent_id = update_dict['parent_id']
            
            # Validate new parent if specified
            if new_parent_id:
                if new_parent_id == resource_id:
                    raise ValidationError("Resource cannot be its own parent")
                
                parent_result = await self.db.execute(
                    select(Resource).where(
                        and_(
                            Resource.id == new_parent_id,
                            Resource.tenant_id == tenant_id
                        )
                    )
                )
                parent_resource = parent_result.scalar_one_or_none()
                if not parent_resource:
                    raise NotFoundError(f"Parent resource with ID {new_parent_id} not found")
                
                # Check for circular dependency
                if await self._would_create_cycle(resource_id, new_parent_id):
                    raise ValidationError("Moving resource would create circular dependency")
                
                # Update materialized path
                await self._update_resource_path(resource, parent_resource.path)
            else:
                # Moving to root level
                await self._update_resource_path(resource, None)

        # Apply other updates
        for field, value in update_dict.items():
            if field != 'parent_id':  # parent_id handled above
                setattr(resource, field, value)

        await self.db.commit()
        await self.db.refresh(resource)

        return ResourceResponse.model_validate(resource)

    async def delete_resource(self, resource_id: UUID_T, tenant_id: UUID_T, cascade: bool = False) -> bool:
        """Soft delete a resource."""
        
        # Get resource
        result = await self.db.execute(
            select(Resource).where(
                and_(
                    Resource.id == resource_id,
                    Resource.tenant_id == tenant_id
                )
            )
        )
        resource = result.scalar_one_or_none()
        if not resource:
            raise NotFoundError(f"Resource with ID {resource_id} not found")

        # Check for children if not cascading
        if not cascade:
            children_result = await self.db.execute(
                select(func.count(Resource.id)).where(
                    and_(
                        Resource.parent_id == resource_id,
                        Resource.is_active == True
                    )
                )
            )
            children_count = children_result.scalar()
            if children_count > 0:
                raise ValidationError(f"Cannot delete resource with {children_count} active children. Use cascade=True to delete children.")

        # Soft delete resource and optionally children
        if cascade:
            # Get all descendant IDs using materialized path
            descendants_result = await self.db.execute(
                select(Resource.id).where(
                    and_(
                        Resource.tenant_id == tenant_id,
                        Resource.path.like(f"{resource.path}%"),
                        Resource.id != resource_id
                    )
                )
            )
            descendant_ids = [row[0] for row in descendants_result.fetchall()]
            
            # Soft delete all descendants
            if descendant_ids:
                await self.db.execute(
                    update(Resource).where(
                        Resource.id.in_(descendant_ids)
                    ).values(is_active=False)
                )

        # Soft delete the resource
        resource.is_active = False
        await self.db.commit()

        return True

    async def get_resource_tree(
        self, 
        tenant_id: Optional[UUID_T],
        root_id: Optional[UUID_T] = None,
        max_depth: Optional[int] = None
    ) -> ResourceTreeResponse:
        """Get hierarchical resource tree."""
        
        # Build query for tree nodes
        conditions = [Resource.is_active == True]
        if tenant_id is not None:
            conditions.append(Resource.tenant_id == tenant_id)
            
        stmt = select(Resource).where(and_(*conditions))

        if root_id:
            # Get subtree from specific root
            root_conditions = [Resource.id == root_id]
            if tenant_id is not None:
                root_conditions.append(Resource.tenant_id == tenant_id)
                
            root_result = await self.db.execute(
                select(Resource).where(and_(*root_conditions))
            )
            root_resource = root_result.scalar_one_or_none()
            if not root_resource:
                raise NotFoundError(f"Root resource with ID {root_id} not found")
            
            stmt = stmt.where(Resource.path.like(f"{root_resource.path}%"))
        else:
            # Get all resources for building tree
            pass

        stmt = stmt.order_by(Resource.path)
        result = await self.db.execute(stmt)
        resources = result.scalars().all()

        # Build tree structure
        if root_id:
            tree = self._build_tree_from_resources(resources, root_id)
            total_nodes = len(resources)
        else:
            # Build multiple trees for root resources
            root_resources = [r for r in resources if r.parent_id is None]
            tree = []
            for root in root_resources:
                subtree = self._build_tree_from_resources(resources, root.id)
                tree.append(subtree)
            total_nodes = len(resources)

        # Calculate max depth
        max_depth_found = max([r.get_depth() for r in resources]) if resources else 0

        return ResourceTreeResponse(
            tree=tree[0] if root_id and tree else tree,
            total_nodes=total_nodes,
            max_depth=max_depth_found
        )

    async def get_resource_permissions(self, resource_id: UUID_T, tenant_id: UUID_T) -> ResourcePermissionResponse:
        """Get permissions associated with a resource."""
        
        # Verify resource exists
        resource = await self.get_resource(resource_id, tenant_id)
        
        # Get associated permissions
        permissions_result = await self.db.execute(
            select(Permission).where(
                and_(
                    Permission.resource_id == resource_id,
                    Permission.tenant_id == tenant_id,
                    Permission.is_active == True
                )
            )
        )
        permissions = permissions_result.scalars().all()
        
        permissions_data = []
        for perm in permissions:
            permissions_data.append({
                'id': str(perm.id),
                'name': perm.name,
                'actions': perm.actions,
                'conditions': perm.conditions,
                'field_permissions': perm.field_permissions,
                'is_active': perm.is_active
            })

        return ResourcePermissionResponse(
            resource_id=resource_id,
            resource_name=resource.name,
            resource_type=resource.type,
            permissions=permissions_data
        )

    async def get_resource_statistics(self, tenant_id: Optional[UUID_T]) -> ResourceStatistics:
        """Get resource statistics for a tenant."""
        
        # Total resources
        conditions = []
        if tenant_id is not None:
            conditions.append(Resource.tenant_id == tenant_id)
        
        if conditions:
            total_result = await self.db.execute(
                select(func.count(Resource.id)).where(and_(*conditions))
            )
        else:
            total_result = await self.db.execute(
                select(func.count(Resource.id))
            )
        total = total_result.scalar()

        # Active/inactive counts
        active_conditions = [Resource.is_active == True]
        if tenant_id is not None:
            active_conditions.append(Resource.tenant_id == tenant_id)
        
        active_result = await self.db.execute(
            select(func.count(Resource.id)).where(and_(*active_conditions))
        )
        active = active_result.scalar()

        # By type
        by_type_conditions = []
        if tenant_id is not None:
            by_type_conditions.append(Resource.tenant_id == tenant_id)
        
        if by_type_conditions:
            by_type_result = await self.db.execute(
                select(Resource.type, func.count(Resource.id))
                .where(and_(*by_type_conditions))
                .group_by(Resource.type)
            )
        else:
            by_type_result = await self.db.execute(
                select(Resource.type, func.count(Resource.id))
                .group_by(Resource.type)
            )
        by_type = {str(row[0]): row[1] for row in by_type_result.fetchall()}

        # Max depth
        depth_conditions = []
        if tenant_id is not None:
            depth_conditions.append(Resource.tenant_id == tenant_id)
        
        if depth_conditions:
            max_depth_result = await self.db.execute(
                select(func.max(func.array_length(func.string_to_array(Resource.path, '/'), 1)))
                .where(and_(*depth_conditions))
            )
        else:
            max_depth_result = await self.db.execute(
                select(func.max(func.array_length(func.string_to_array(Resource.path, '/'), 1)))
            )
        max_depth = max_depth_result.scalar() or 0
        max_depth = max(0, max_depth - 2)  # Adjust for leading/trailing slashes

        # Root resources
        root_conditions = [Resource.parent_id.is_(None)]
        if tenant_id is not None:
            root_conditions.append(Resource.tenant_id == tenant_id)
        
        root_result = await self.db.execute(
            select(func.count(Resource.id)).where(and_(*root_conditions))
        )
        root_count = root_result.scalar()

        return ResourceStatistics(
            total_resources=total,
            by_type=by_type,
            active_resources=active,
            inactive_resources=total - active,
            max_hierarchy_depth=max_depth,
            total_root_resources=root_count
        )

    # Private helper methods

    async def _validate_hierarchy_rules(self, child_type: ResourceType, parent_type: ResourceType):
        """Validate hierarchy rules between parent and child resource types."""
        # Define valid parent-child relationships
        valid_hierarchy = {
            ResourceType.PRODUCT_FAMILY: [],  # Root level
            ResourceType.APP: [ResourceType.PRODUCT_FAMILY],
            ResourceType.CAPABILITY: [ResourceType.APP],
            ResourceType.SERVICE: [ResourceType.CAPABILITY],
            ResourceType.ENTITY: [ResourceType.SERVICE, ResourceType.APP],  # Can be under service or app
            ResourceType.PAGE: [ResourceType.APP, ResourceType.CAPABILITY],
            ResourceType.API: [ResourceType.SERVICE, ResourceType.APP]
        }

        valid_parents = valid_hierarchy.get(child_type, [])
        if valid_parents and parent_type not in valid_parents:
            raise ValidationError(
                f"Invalid hierarchy: {child_type.value} cannot be a child of {parent_type.value}. "
                f"Valid parents: {[p.value for p in valid_parents]}"
            )

    async def _would_create_cycle(self, resource_id: UUID_T, new_parent_id: UUID_T) -> bool:
        """Check if moving resource would create a circular dependency."""
        
        # Get the proposed parent's path
        parent_result = await self.db.execute(
            select(Resource.path).where(Resource.id == new_parent_id)
        )
        parent_path = parent_result.scalar()
        
        # Check if the resource being moved is an ancestor of the proposed parent
        resource_path_pattern = f"/%{resource_id}/%"
        return parent_path and resource_path_pattern in parent_path

    async def _update_resource_path(self, resource: Resource, new_parent_path: Optional[str]):
        """Update materialized path for resource and its descendants."""
        old_path = resource.path
        
        # Calculate new path
        if new_parent_path:
            new_path = f"{new_parent_path}{resource.id}/"
        else:
            new_path = f"/{resource.id}/"
        
        # Update resource path
        resource.path = new_path
        
        # Update all descendant paths
        if old_path != new_path:
            await self.db.execute(
                text("""
                    UPDATE sentinel.resources 
                    SET path = REPLACE(path, :old_path, :new_path)
                    WHERE tenant_id = :tenant_id 
                    AND path LIKE :pattern
                """),
                {
                    'old_path': old_path,
                    'new_path': new_path,
                    'tenant_id': resource.tenant_id,
                    'pattern': f"{old_path}%"
                }
            )

    def _build_tree_from_resources(self, resources: List[Resource], root_id: UUID_T) -> ResourceTreeNode:
        """Build hierarchical tree structure from flat resource list."""
        resources_by_id = {r.id: r for r in resources}
        children_by_parent = {}
        
        # Group resources by parent
        for resource in resources:
            parent_id = resource.parent_id
            if parent_id not in children_by_parent:
                children_by_parent[parent_id] = []
            children_by_parent[parent_id].append(resource)
        
        def build_node(resource_id: UUID_T) -> Optional[ResourceTreeNode]:
            resource = resources_by_id.get(resource_id)
            if not resource:
                return None
            
            # Build child nodes
            children = []
            for child_resource in children_by_parent.get(resource_id, []):
                child_node = build_node(child_resource.id)
                if child_node:
                    children.append(child_node)
            
            return ResourceTreeNode(
                id=resource.id,
                type=resource.type.value if isinstance(resource.type, ResourceType) else resource.type,
                name=resource.name,
                code=resource.code,
                attributes=resource.attributes,
                is_active=resource.is_active,
                children=children
            )
        
        return build_node(root_id)