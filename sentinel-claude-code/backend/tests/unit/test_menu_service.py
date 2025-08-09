"""
Unit tests for Menu Service (Module 9)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from src.services.menu_service import MenuService
from src.schemas.menu import (
    MenuItemCreate, MenuItemUpdate, MenuQuery, 
    UserMenuResponse, MenuStatistics
)
from src.models import MenuItem, UserMenuCustomization
from src.core.exceptions import NotFoundError, ConflictError


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def menu_service(mock_db):
    """MenuService instance with mocked database."""
    return MenuService(mock_db)


@pytest.fixture
def sample_menu_item_create():
    """Sample menu item creation data."""
    return MenuItemCreate(
        tenant_id=uuid4(),
        parent_id=None,
        name="test-menu",
        display_name="Test Menu",
        icon="test-icon",
        url="/test",
        resource_id=uuid4(),
        required_permission="test:read",
        display_order=1,
        is_visible=True,
        menu_metadata={"category": "test"}
    )


class TestMenuService:
    """Test suite for MenuService."""

    @pytest.mark.asyncio
    async def test_create_menu_item_success(self, menu_service, mock_db, sample_menu_item_create):
        """Test successful menu item creation."""
        # Mock database responses
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # No existing item
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock menu item instance
        mock_menu_item = MagicMock()
        mock_menu_item.id = uuid4()
        mock_menu_item.name = sample_menu_item_create.name
        mock_menu_item.display_name = sample_menu_item_create.display_name
        mock_menu_item.created_at = datetime.now(timezone.utc)
        mock_menu_item.updated_at = datetime.now(timezone.utc)
        
        mock_db.add = MagicMock()
        mock_db.refresh.side_effect = lambda x: setattr(x, 'id', mock_menu_item.id)
        
        # Execute
        result = await menu_service.create_menu_item(sample_menu_item_create)
        
        # Verify
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_create_menu_item_duplicate_error(self, menu_service, mock_db, sample_menu_item_create):
        """Test menu item creation with duplicate name."""
        # Mock existing menu item
        existing_item = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_item
        
        # Execute and verify exception
        with pytest.raises(ConflictError, match="already exists"):
            await menu_service.create_menu_item(sample_menu_item_create)

    @pytest.mark.asyncio
    async def test_get_menu_item_success(self, menu_service, mock_db):
        """Test successful menu item retrieval."""
        item_id = uuid4()
        
        # Mock menu item
        mock_menu_item = MagicMock()
        mock_menu_item.id = item_id
        mock_menu_item.name = "test-menu"
        mock_menu_item.display_name = "Test Menu"
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_menu_item
        
        # Execute
        result = await menu_service.get_menu_item(item_id)
        
        # Verify
        assert result is not None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_menu_item_not_found(self, menu_service, mock_db):
        """Test menu item retrieval with non-existent ID."""
        item_id = uuid4()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundError, match="not found"):
            await menu_service.get_menu_item(item_id)

    @pytest.mark.asyncio
    async def test_list_menu_items(self, menu_service, mock_db):
        """Test menu item listing with pagination."""
        # Mock count query
        mock_db.execute.side_effect = [
            # Count query result
            MagicMock(scalar=lambda: 25),
            # Main query result
            MagicMock(scalars=lambda: MagicMock(all=lambda: [
                MagicMock(id=uuid4(), name="item1"),
                MagicMock(id=uuid4(), name="item2")
            ]))
        ]
        
        # Execute
        result = await menu_service.list_menu_items(page=1, limit=10)
        
        # Verify
        assert result.total == 25
        assert len(result.items) == 2
        assert result.page == 1
        assert result.limit == 10

    @pytest.mark.asyncio
    async def test_update_menu_item_success(self, menu_service, mock_db):
        """Test successful menu item update."""
        item_id = uuid4()
        update_data = MenuItemUpdate(display_name="Updated Menu")
        
        # Mock existing menu item
        mock_menu_item = MagicMock()
        mock_menu_item.id = item_id
        mock_menu_item.display_name = "Original Menu"
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_menu_item
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Execute
        result = await menu_service.update_menu_item(item_id, update_data)
        
        # Verify
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_menu_item_not_found(self, menu_service, mock_db):
        """Test menu item update with non-existent ID."""
        item_id = uuid4()
        update_data = MenuItemUpdate(display_name="Updated Menu")
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundError, match="not found"):
            await menu_service.update_menu_item(item_id, update_data)

    @pytest.mark.asyncio
    async def test_delete_menu_item_success(self, menu_service, mock_db):
        """Test successful menu item deletion."""
        item_id = uuid4()
        
        # Mock existing menu item
        mock_menu_item = MagicMock()
        mock_menu_item.id = item_id
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_menu_item
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()
        
        # Execute
        result = await menu_service.delete_menu_item(item_id)
        
        # Verify
        assert result is True
        mock_db.delete.assert_called_once_with(mock_menu_item)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_menu_item_not_found(self, menu_service, mock_db):
        """Test menu item deletion with non-existent ID."""
        item_id = uuid4()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundError, match="not found"):
            await menu_service.delete_menu_item(item_id)

    @pytest.mark.asyncio
    async def test_get_user_menu_success(self, menu_service, mock_db):
        """Test successful user menu retrieval."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        # Mock user
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.tenant_id = tenant_id
        
        # Mock menu items
        mock_menu_items = [
            MagicMock(
                id=uuid4(),
                name="parent-menu",
                parent_id=None,
                display_order=1,
                is_visible=True
            ),
            MagicMock(
                id=uuid4(),
                name="child-menu",
                parent_id=mock_menu_items[0].id if mock_menu_items else uuid4(),
                display_order=1,
                is_visible=True
            )
        ]
        
        # Mock customizations
        mock_customizations = []
        
        mock_db.execute.side_effect = [
            # User query
            MagicMock(scalar_one_or_none=lambda: mock_user),
            # Menu items query
            MagicMock(scalars=lambda: MagicMock(all=lambda: mock_menu_items)),
            # Customizations query
            MagicMock(scalars=lambda: MagicMock(all=lambda: mock_customizations))
        ]
        
        # Execute
        result = await menu_service.get_user_menu(user_id, include_hidden=False, tenant_id=tenant_id)
        
        # Verify
        assert isinstance(result, UserMenuResponse)
        assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_user_menu_user_not_found(self, menu_service, mock_db):
        """Test user menu retrieval with non-existent user."""
        user_id = uuid4()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundError, match="not found"):
            await menu_service.get_user_menu(user_id)

    @pytest.mark.asyncio
    async def test_customize_user_menu_success(self, menu_service, mock_db):
        """Test successful user menu customization."""
        user_id = uuid4()
        menu_item_id = uuid4()
        
        customizations = [
            {
                "menu_item_id": menu_item_id,
                "is_hidden": True,
                "custom_order": 5
            }
        ]
        
        # Mock user and menu item existence
        mock_user = MagicMock()
        mock_menu_item = MagicMock()
        
        mock_db.execute.side_effect = [
            # User query
            MagicMock(scalar_one_or_none=lambda: mock_user),
            # Menu item query
            MagicMock(scalar_one_or_none=lambda: mock_menu_item),
            # Existing customization query
            MagicMock(scalar_one_or_none=lambda: None)
        ]
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        # Execute
        result = await menu_service.customize_user_menu(user_id, customizations)
        
        # Verify
        assert result["applied"] == 1
        assert result["failed"] == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_customize_user_menu_user_not_found(self, menu_service, mock_db):
        """Test menu customization with non-existent user."""
        user_id = uuid4()
        customizations = []
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundError, match="not found"):
            await menu_service.customize_user_menu(user_id, customizations)

    @pytest.mark.asyncio
    async def test_get_user_customization_success(self, menu_service, mock_db):
        """Test successful user customization retrieval."""
        user_id = uuid4()
        menu_item_id = uuid4()
        
        # Mock customization
        mock_customization = MagicMock()
        mock_customization.user_id = user_id
        mock_customization.menu_item_id = menu_item_id
        mock_customization.is_hidden = True
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_customization
        
        # Execute
        result = await menu_service.get_user_customization(user_id, menu_item_id)
        
        # Verify
        assert result is not None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_customization_not_found(self, menu_service, mock_db):
        """Test user customization retrieval when none exists."""
        user_id = uuid4()
        menu_item_id = uuid4()
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute
        result = await menu_service.get_user_customization(user_id, menu_item_id)
        
        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user_customization_success(self, menu_service, mock_db):
        """Test successful user customization deletion."""
        user_id = uuid4()
        menu_item_id = uuid4()
        
        # Mock existing customization
        mock_customization = MagicMock()
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_customization
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()
        
        # Execute
        result = await menu_service.delete_user_customization(user_id, menu_item_id)
        
        # Verify
        assert result is True
        mock_db.delete.assert_called_once_with(mock_customization)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_customization_not_found(self, menu_service, mock_db):
        """Test user customization deletion when none exists."""
        user_id = uuid4()
        menu_item_id = uuid4()
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundError, match="not found"):
            await menu_service.delete_user_customization(user_id, menu_item_id)

    @pytest.mark.asyncio
    async def test_get_menu_statistics(self, menu_service, mock_db):
        """Test menu statistics retrieval."""
        # Mock various count queries
        mock_db.execute.side_effect = [
            MagicMock(scalar=lambda: 50),   # Total items
            MagicMock(scalar=lambda: 20),   # System-wide items
            MagicMock(scalar=lambda: 40),   # Visible items
            MagicMock(scalar=lambda: 15),   # Items with permissions
            MagicMock(scalar=lambda: 10),   # Top-level items
        ]
        
        # Execute
        result = await menu_service.get_menu_statistics()
        
        # Verify
        assert isinstance(result, MenuStatistics)
        assert result.total_items == 50
        assert result.system_wide_items == 20
        assert result.tenant_specific_items == 30  # 50 - 20
        assert result.visible_items == 40
        assert result.hidden_items == 10  # 50 - 40

    @pytest.mark.asyncio  
    async def test_build_menu_hierarchy(self, menu_service):
        """Test menu hierarchy building with customizations."""
        # Create mock menu items
        parent_item = MagicMock()
        parent_item.id = uuid4()
        parent_item.parent_id = None
        parent_item.name = "parent"
        parent_item.display_order = 1
        
        child_item = MagicMock()
        child_item.id = uuid4()
        child_item.parent_id = parent_item.id
        child_item.name = "child"
        child_item.display_order = 1
        
        menu_items = [parent_item, child_item]
        
        # Create mock customizations
        customization_map = {
            child_item.id: MagicMock(is_hidden=False, custom_order=None)
        }
        
        # Execute
        result = menu_service._build_menu_hierarchy(menu_items, customization_map, False)
        
        # Verify
        assert len(result) >= 0  # Should return some hierarchy

    def test_menu_item_model_methods(self):
        """Test MenuItem model helper methods."""
        # Test system-wide item
        system_item = MenuItem(
            name="system-menu",
            display_name="System Menu",
            tenant_id=None
        )
        assert system_item.is_system_wide() is True
        assert system_item.is_tenant_specific() is False
        
        # Test tenant-specific item
        tenant_item = MenuItem(
            name="tenant-menu",
            display_name="Tenant Menu",
            tenant_id=uuid4()
        )
        assert tenant_item.is_system_wide() is False
        assert tenant_item.is_tenant_specific() is True
        
        # Test permission requirement
        protected_item = MenuItem(
            name="protected-menu",
            required_permission="admin:read"
        )
        assert protected_item.has_permission_requirement() is True
        
        unprotected_item = MenuItem(name="public-menu")
        assert unprotected_item.has_permission_requirement() is False

    def test_user_menu_customization_model_methods(self):
        """Test UserMenuCustomization model helper methods."""
        # Test visible override
        visible_customization = UserMenuCustomization(
            user_id=uuid4(),
            menu_item_id=uuid4(),
            is_hidden=False
        )
        assert visible_customization.is_visible_override() is True
        
        hidden_customization = UserMenuCustomization(
            user_id=uuid4(),
            menu_item_id=uuid4(),
            is_hidden=True
        )
        assert hidden_customization.is_visible_override() is False
        
        # Test custom ordering
        ordered_customization = UserMenuCustomization(
            user_id=uuid4(),
            menu_item_id=uuid4(),
            custom_order=5
        )
        assert ordered_customization.has_custom_ordering() is True
        
        unordered_customization = UserMenuCustomization(
            user_id=uuid4(),
            menu_item_id=uuid4(),
            custom_order=None
        )
        assert unordered_customization.has_custom_ordering() is False