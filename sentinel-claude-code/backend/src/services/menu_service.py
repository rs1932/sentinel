"""
MenuService for Module 9: Menu/Navigation management
"""
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID as UUID_T
from sqlalchemy import select, and_, or_, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import MenuItem, UserMenuCustomization, Tenant, User
from src.schemas.menu import (
    MenuItemCreate, MenuItemUpdate, MenuItemResponse,
    MenuItemWithChildren, UserMenuCustomizationCreate, UserMenuCustomizationUpdate,
    UserMenuCustomizationResponse, MenuQuery, MenuItemListResponse,
    UserMenuResponse, MenuStatistics, MenuCustomizationBatch
)
from src.core.exceptions import NotFoundError, ConflictError, ValidationError


class MenuService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_menu_item(self, item_data: MenuItemCreate) -> MenuItemResponse:
        """Create a new menu item with validation."""
        
        # Check if menu item already exists (same name within same parent and tenant)
        query = select(MenuItem).where(
            and_(
                MenuItem.name == item_data.name,
                MenuItem.parent_id == item_data.parent_id,
                MenuItem.tenant_id == item_data.tenant_id
            )
        )
        existing_item = await self.db.execute(query)
        if existing_item.scalar_one_or_none():
            raise ConflictError(
                f"Menu item '{item_data.name}' already exists in the specified parent"
            )

        # Validate parent exists if parent_id is provided
        if item_data.parent_id:
            parent_result = await self.db.execute(
                select(MenuItem).where(MenuItem.id == item_data.parent_id)
            )
            if not parent_result.scalar_one_or_none():
                raise NotFoundError(f"Parent menu item with ID {item_data.parent_id} not found")

        # Validate tenant exists if tenant_id is provided
        if item_data.tenant_id:
            tenant_result = await self.db.execute(
                select(Tenant).where(Tenant.id == item_data.tenant_id)
            )
            if not tenant_result.scalar_one_or_none():
                raise NotFoundError(f"Tenant with ID {item_data.tenant_id} not found")

        # Create menu item
        menu_item = MenuItem(
            tenant_id=item_data.tenant_id,
            parent_id=item_data.parent_id,
            name=item_data.name,
            display_name=item_data.display_name,
            icon=item_data.icon,
            url=item_data.url,
            resource_id=item_data.resource_id,
            required_permission=item_data.required_permission,
            display_order=item_data.display_order,
            is_visible=item_data.is_visible,
            menu_metadata=item_data.menu_metadata
        )

        self.db.add(menu_item)
        await self.db.commit()
        await self.db.refresh(menu_item)

        return MenuItemResponse.model_validate(menu_item)

    async def get_menu_item(self, item_id: UUID_T) -> MenuItemResponse:
        """Get menu item by ID."""
        
        query = select(MenuItem).where(MenuItem.id == item_id)
        result = await self.db.execute(query)
        menu_item = result.scalar_one_or_none()
        
        if not menu_item:
            raise NotFoundError(f"Menu item with ID {item_id} not found")

        return MenuItemResponse.model_validate(menu_item)

    async def list_menu_items(
        self,
        page: int = 1,
        limit: int = 50,
        parent_id: Optional[UUID_T] = None,
        tenant_id: Optional[UUID_T] = None,
        include_system_wide: bool = True
    ) -> MenuItemListResponse:
        """List menu items with filtering and pagination."""
        
        # Build base query
        query = select(MenuItem)
        where_conditions = []

        # Apply filters
        if parent_id is not None:
            where_conditions.append(MenuItem.parent_id == parent_id)
        
        if tenant_id is not None or not include_system_wide:
            if tenant_id and include_system_wide:
                # Include both tenant-specific and system-wide items
                where_conditions.append(
                    or_(
                        MenuItem.tenant_id == tenant_id,
                        MenuItem.tenant_id.is_(None)
                    )
                )
            elif tenant_id:
                # Only tenant-specific items
                where_conditions.append(MenuItem.tenant_id == tenant_id)
            else:
                # Only system-wide items
                where_conditions.append(MenuItem.tenant_id.is_(None))

        if where_conditions:
            query = query.where(and_(*where_conditions))

        # Count total items
        count_query = select(func.count()).select_from(query.alias())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting and pagination
        query = query.order_by(MenuItem.display_order, MenuItem.name)
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        menu_items = result.scalars().all()

        # Convert to response schemas
        items = [MenuItemResponse.model_validate(item) for item in menu_items]

        return MenuItemListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_next=offset + len(items) < total,
            has_prev=page > 1
        )

    async def update_menu_item(
        self,
        item_id: UUID_T,
        item_data: MenuItemUpdate
    ) -> MenuItemResponse:
        """Update menu item."""
        
        # Get existing menu item
        query = select(MenuItem).where(MenuItem.id == item_id)
        result = await self.db.execute(query)
        menu_item = result.scalar_one_or_none()
        
        if not menu_item:
            raise NotFoundError(f"Menu item with ID {item_id} not found")

        # Update fields
        update_data = item_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(menu_item, field, value)

        await self.db.commit()
        await self.db.refresh(menu_item)

        return MenuItemResponse.model_validate(menu_item)

    async def delete_menu_item(self, item_id: UUID_T) -> bool:
        """Delete menu item and its children."""
        
        query = select(MenuItem).where(MenuItem.id == item_id)
        result = await self.db.execute(query)
        menu_item = result.scalar_one_or_none()
        
        if not menu_item:
            raise NotFoundError(f"Menu item with ID {item_id} not found")

        # Delete the item (cascade will handle children and customizations)
        await self.db.delete(menu_item)
        await self.db.commit()

        return True

    async def get_user_menu(
        self,
        user_id: UUID_T,
        include_hidden: bool = False,
        tenant_id: Optional[UUID_T] = None
    ) -> UserMenuResponse:
        """Get hierarchical menu structure for a user with customizations applied."""
        
        # Verify user exists
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        # Use user's tenant if not specified
        if tenant_id is None:
            tenant_id = user.tenant_id

        # Get all menu items (system-wide and tenant-specific)
        menu_query = select(MenuItem).where(
            or_(
                MenuItem.tenant_id.is_(None),
                MenuItem.tenant_id == tenant_id
            )
        ).order_by(MenuItem.display_order, MenuItem.name)
        
        menu_result = await self.db.execute(menu_query)
        menu_items = menu_result.scalars().all()

        # Get user customizations
        customizations_query = select(UserMenuCustomization).where(
            UserMenuCustomization.user_id == user_id
        )
        customizations_result = await self.db.execute(customizations_query)
        customizations = customizations_result.scalars().all()
        
        # Build customization lookup
        customization_map = {c.menu_item_id: c for c in customizations}

        # Build hierarchical structure
        menu_hierarchy = self._build_menu_hierarchy(
            menu_items, 
            customization_map, 
            include_hidden
        )

        return UserMenuResponse(
            menu_items=menu_hierarchy,
            user_id=user_id,
            customizations_applied=len(customizations)
        )

    async def customize_user_menu(
        self,
        user_id: UUID_T,
        customizations: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Apply batch customizations to user menu."""
        
        # Verify user exists
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        if not user_result.scalar_one_or_none():
            raise NotFoundError(f"User with ID {user_id} not found")

        applied = 0
        failed = 0

        for customization in customizations:
            try:
                menu_item_id = customization['menu_item_id']
                
                # Check if menu item exists
                menu_item_result = await self.db.execute(
                    select(MenuItem).where(MenuItem.id == menu_item_id)
                )
                if not menu_item_result.scalar_one_or_none():
                    failed += 1
                    continue

                # Check if customization already exists
                existing_result = await self.db.execute(
                    select(UserMenuCustomization).where(
                        and_(
                            UserMenuCustomization.user_id == user_id,
                            UserMenuCustomization.menu_item_id == menu_item_id
                        )
                    )
                )
                existing = existing_result.scalar_one_or_none()

                if existing:
                    # Update existing customization
                    if 'is_hidden' in customization:
                        existing.is_hidden = customization['is_hidden']
                    if 'custom_order' in customization:
                        existing.custom_order = customization['custom_order']
                else:
                    # Create new customization
                    new_customization = UserMenuCustomization(
                        user_id=user_id,
                        menu_item_id=menu_item_id,
                        is_hidden=customization.get('is_hidden', False),
                        custom_order=customization.get('custom_order')
                    )
                    self.db.add(new_customization)

                applied += 1

            except Exception:
                failed += 1

        await self.db.commit()
        
        return {
            "applied": applied,
            "failed": failed
        }

    async def get_user_customization(
        self,
        user_id: UUID_T,
        menu_item_id: UUID_T
    ) -> Optional[UserMenuCustomizationResponse]:
        """Get user's customization for a specific menu item."""
        
        query = select(UserMenuCustomization).where(
            and_(
                UserMenuCustomization.user_id == user_id,
                UserMenuCustomization.menu_item_id == menu_item_id
            )
        )
        result = await self.db.execute(query)
        customization = result.scalar_one_or_none()
        
        if not customization:
            return None

        return UserMenuCustomizationResponse.model_validate(customization)

    async def delete_user_customization(
        self,
        user_id: UUID_T,
        menu_item_id: UUID_T
    ) -> bool:
        """Delete user's customization for a specific menu item."""
        
        query = select(UserMenuCustomization).where(
            and_(
                UserMenuCustomization.user_id == user_id,
                UserMenuCustomization.menu_item_id == menu_item_id
            )
        )
        result = await self.db.execute(query)
        customization = result.scalar_one_or_none()
        
        if not customization:
            raise NotFoundError(f"Customization not found for user {user_id} and menu item {menu_item_id}")

        await self.db.delete(customization)
        await self.db.commit()

        return True

    async def get_menu_statistics(self, tenant_id: Optional[UUID_T] = None) -> MenuStatistics:
        """Get menu statistics."""
        
        where_conditions = []
        if tenant_id:
            where_conditions.append(
                or_(
                    MenuItem.tenant_id.is_(None),
                    MenuItem.tenant_id == tenant_id
                )
            )

        base_query = select(MenuItem)
        if where_conditions:
            base_query = base_query.where(and_(*where_conditions))

        # Total items
        total_result = await self.db.execute(
            select(func.count()).select_from(base_query.alias())
        )
        total_items = total_result.scalar()

        # System-wide vs tenant-specific
        system_wide_query = select(func.count()).select_from(MenuItem)
        if where_conditions:
            system_wide_query = system_wide_query.where(and_(*where_conditions, MenuItem.tenant_id.is_(None)))
        else:
            system_wide_query = system_wide_query.where(MenuItem.tenant_id.is_(None))
            
        system_wide_result = await self.db.execute(system_wide_query)
        system_wide_items = system_wide_result.scalar()
        tenant_specific_items = total_items - system_wide_items

        # Visible vs hidden
        visible_query = select(func.count()).select_from(MenuItem)
        if where_conditions:
            visible_query = visible_query.where(and_(*where_conditions, MenuItem.is_visible.is_(True)))
        else:
            visible_query = visible_query.where(MenuItem.is_visible.is_(True))
        
        visible_result = await self.db.execute(visible_query)
        visible_items = visible_result.scalar()
        hidden_items = total_items - visible_items

        # Items with permissions
        permissions_query = select(func.count()).select_from(MenuItem)
        if where_conditions:
            permissions_query = permissions_query.where(and_(*where_conditions, MenuItem.required_permission.is_not(None)))
        else:
            permissions_query = permissions_query.where(MenuItem.required_permission.is_not(None))
            
        permissions_result = await self.db.execute(permissions_query)
        items_with_permissions = permissions_result.scalar()

        # Top-level items (no parent)
        top_level_query = select(func.count()).select_from(MenuItem)
        if where_conditions:
            top_level_query = top_level_query.where(and_(*where_conditions, MenuItem.parent_id.is_(None)))
        else:
            top_level_query = top_level_query.where(MenuItem.parent_id.is_(None))
            
        top_level_result = await self.db.execute(top_level_query)
        top_level_items = top_level_result.scalar()

        # Calculate hierarchy depth (simplified - could be optimized with recursive query)
        hierarchy_depth = 1  # At least 1 level if there are items
        if total_items > 0:
            # For now, assume max depth of 3 - could be calculated more precisely
            hierarchy_depth = 3

        return MenuStatistics(
            total_items=total_items,
            system_wide_items=system_wide_items,
            tenant_specific_items=tenant_specific_items,
            visible_items=visible_items,
            hidden_items=hidden_items,
            items_with_permissions=items_with_permissions,
            hierarchy_depth=hierarchy_depth,
            top_level_items=top_level_items
        )

    def _build_menu_hierarchy(
        self,
        menu_items: List[MenuItem],
        customization_map: Dict[UUID_T, UserMenuCustomization],
        include_hidden: bool = False
    ) -> List[MenuItemWithChildren]:
        """Build hierarchical menu structure with user customizations."""
        
        # Create lookup for menu items by ID
        item_map = {item.id: item for item in menu_items}
        
        # Build hierarchy
        hierarchy = []
        processed_items = set()

        def build_item_with_children(item: MenuItem) -> Optional[MenuItemWithChildren]:
            if item.id in processed_items:
                return None
            
            processed_items.add(item.id)
            
            # Check user customization
            customization = customization_map.get(item.id)
            is_hidden_by_user = customization.is_hidden if customization else False
            
            # Skip hidden items unless explicitly requested
            if is_hidden_by_user and not include_hidden:
                return None
            
            # Convert to response format
            item_data = MenuItemResponse.model_validate(item)
            
            # Build children
            children = []
            for child_item in menu_items:
                if child_item.parent_id == item.id:
                    child_with_children = build_item_with_children(child_item)
                    if child_with_children:
                        children.append(child_with_children)
            
            # Sort children by custom order or default order
            children.sort(key=lambda x: (
                customization_map[x.id].custom_order
                if x.id in customization_map and customization_map[x.id].custom_order is not None
                else x.display_order
            ))
            
            return MenuItemWithChildren(
                **item_data.model_dump(),
                children=children,
                visible=not is_hidden_by_user
            )

        # Build top-level items (items with no parent)
        for item in menu_items:
            if item.parent_id is None:
                item_with_children = build_item_with_children(item)
                if item_with_children:
                    hierarchy.append(item_with_children)

        # Sort top-level items
        hierarchy.sort(key=lambda x: (
            customization_map[x.id].custom_order
            if x.id in customization_map and customization_map[x.id].custom_order is not None
            else x.display_order
        ))

        return hierarchy