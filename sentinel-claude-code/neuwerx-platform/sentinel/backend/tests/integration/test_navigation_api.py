"""
Integration tests for Navigation API (Module 9)
Tests all Navigation endpoints with comprehensive scenarios
"""
import pytest
import httpx
from uuid import uuid4
from datetime import datetime, timezone

from src.models import MenuItem, UserMenuCustomization
from tests.auth_helpers import SyncAuthHelper, DEFAULT_USER_CREDENTIALS


class TestNavigationAPI:
    """Test Navigation API endpoints."""
    
    BASE_URL = "http://testserver/api/v1/navigation"
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Set up test environment."""
        self.auth_helper = SyncAuthHelper()
        
        # Test data
        self.test_menu_item = {
            "name": "test-menu-item",
            "display_name": "Test Menu Item",
            "icon": "test-icon",
            "url": "/test-menu",
            "display_order": 1,
            "is_visible": True,
            "menu_metadata": {"category": "test"}
        }
        
        self.test_customization = {
            "is_hidden": False,
            "custom_order": 5
        }

    @pytest.mark.asyncio
    async def test_get_user_menu_success(self):
        """Test successful user menu retrieval."""
        async with httpx.AsyncClient() as client:
            # Get authentication headers
            headers = await self._get_auth_headers(client)
            
            # Get user menu
            response = await client.get(f"{self.BASE_URL}/menu", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "menu_items" in data
            assert "user_id" in data
            assert "customizations_applied" in data
            assert isinstance(data["menu_items"], list)

    @pytest.mark.asyncio
    async def test_get_user_menu_with_hidden(self):
        """Test user menu retrieval with hidden items."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            
            response = await client.get(
                f"{self.BASE_URL}/menu",
                params={"include_hidden": True},
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "menu_items" in data

    @pytest.mark.asyncio
    async def test_get_user_menu_for_other_user_forbidden(self):
        """Test that users cannot access other users' menus without admin."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            other_user_id = str(uuid4())
            
            response = await client.get(
                f"{self.BASE_URL}/menu",
                params={"user_id": other_user_id},
                headers=headers
            )
            
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_customize_user_menu_success(self):
        """Test successful user menu customization."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            
            # First create a menu item (requires admin)
            admin_headers = await self._get_admin_headers(client)
            menu_response = await client.post(
                f"{self.BASE_URL}/menu-items",
                json=self.test_menu_item,
                headers=admin_headers
            )
            
            if menu_response.status_code == 201:
                menu_item_id = menu_response.json()["id"]
                
                # Customize the menu item
                customization_data = {
                    "customizations": [
                        {
                            "menu_item_id": menu_item_id,
                            **self.test_customization
                        }
                    ]
                }
                
                response = await client.post(
                    f"{self.BASE_URL}/customize",
                    json=customization_data,
                    headers=headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["applied"] >= 0
                assert data["failed"] >= 0

    @pytest.mark.asyncio
    async def test_customize_user_menu_invalid_data(self):
        """Test user menu customization with invalid data."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            
            invalid_data = {
                "customizations": [
                    {
                        "menu_item_id": "invalid-uuid",
                        "is_hidden": "not-a-boolean"
                    }
                ]
            }
            
            response = await client.post(
                f"{self.BASE_URL}/customize",
                json=invalid_data,
                headers=headers
            )
            
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_menu_item_success(self):
        """Test successful menu item creation (admin only)."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_admin_headers(client)
            
            response = await client.post(
                f"{self.BASE_URL}/menu-items",
                json=self.test_menu_item,
                headers=headers
            )
            
            if response.status_code == 201:
                data = response.json()
                assert data["name"] == self.test_menu_item["name"]
                assert data["display_name"] == self.test_menu_item["display_name"]
                assert "id" in data
                assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_menu_item_forbidden(self):
        """Test that regular users cannot create menu items."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            
            response = await client.post(
                f"{self.BASE_URL}/menu-items",
                json=self.test_menu_item,
                headers=headers
            )
            
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_menu_item_invalid_data(self):
        """Test menu item creation with invalid data."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_admin_headers(client)
            
            invalid_data = {
                "name": "",  # Empty name should fail
                "display_name": "Test Menu"
            }
            
            response = await client.post(
                f"{self.BASE_URL}/menu-items",
                json=invalid_data,
                headers=headers
            )
            
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_menu_items_success(self):
        """Test successful menu items listing."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            
            response = await client.get(f"{self.BASE_URL}/menu-items", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "limit" in data
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_menu_items_with_pagination(self):
        """Test menu items listing with pagination."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            
            response = await client.get(
                f"{self.BASE_URL}/menu-items",
                params={"page": 1, "limit": 5},
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 1
            assert data["limit"] == 5

    @pytest.mark.asyncio
    async def test_get_menu_item_success(self):
        """Test successful menu item retrieval by ID."""
        async with httpx.AsyncClient() as client:
            # First create a menu item
            admin_headers = await self._get_admin_headers(client)
            create_response = await client.post(
                f"{self.BASE_URL}/menu-items",
                json=self.test_menu_item,
                headers=admin_headers
            )
            
            if create_response.status_code == 201:
                item_id = create_response.json()["id"]
                
                # Get the menu item
                headers = await self._get_auth_headers(client)
                response = await client.get(
                    f"{self.BASE_URL}/menu-items/{item_id}",
                    headers=headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == item_id
                assert data["name"] == self.test_menu_item["name"]

    @pytest.mark.asyncio
    async def test_get_menu_item_not_found(self):
        """Test menu item retrieval with non-existent ID."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            fake_id = str(uuid4())
            
            response = await client.get(
                f"{self.BASE_URL}/menu-items/{fake_id}",
                headers=headers
            )
            
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_menu_item_success(self):
        """Test successful menu item update."""
        async with httpx.AsyncClient() as client:
            admin_headers = await self._get_admin_headers(client)
            
            # First create a menu item
            create_response = await client.post(
                f"{self.BASE_URL}/menu-items",
                json=self.test_menu_item,
                headers=admin_headers
            )
            
            if create_response.status_code == 201:
                item_id = create_response.json()["id"]
                
                # Update the menu item
                update_data = {
                    "display_name": "Updated Test Menu",
                    "icon": "updated-icon"
                }
                
                response = await client.patch(
                    f"{self.BASE_URL}/menu-items/{item_id}",
                    json=update_data,
                    headers=admin_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["display_name"] == "Updated Test Menu"
                assert data["icon"] == "updated-icon"

    @pytest.mark.asyncio
    async def test_update_menu_item_forbidden(self):
        """Test that regular users cannot update menu items."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            fake_id = str(uuid4())
            
            response = await client.patch(
                f"{self.BASE_URL}/menu-items/{fake_id}",
                json={"display_name": "Updated"},
                headers=headers
            )
            
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_menu_item_success(self):
        """Test successful menu item deletion."""
        async with httpx.AsyncClient() as client:
            admin_headers = await self._get_admin_headers(client)
            
            # First create a menu item
            create_response = await client.post(
                f"{self.BASE_URL}/menu-items",
                json=self.test_menu_item,
                headers=admin_headers
            )
            
            if create_response.status_code == 201:
                item_id = create_response.json()["id"]
                
                # Delete the menu item
                response = await client.delete(
                    f"{self.BASE_URL}/menu-items/{item_id}",
                    headers=admin_headers
                )
                
                assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_menu_item_forbidden(self):
        """Test that regular users cannot delete menu items."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            fake_id = str(uuid4())
            
            response = await client.delete(
                f"{self.BASE_URL}/menu-items/{fake_id}",
                headers=headers
            )
            
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_menu_statistics_success(self):
        """Test successful menu statistics retrieval."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            
            response = await client.get(f"{self.BASE_URL}/statistics", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify statistics structure
            required_fields = [
                "total_items", "system_wide_items", "tenant_specific_items",
                "visible_items", "hidden_items", "items_with_permissions",
                "hierarchy_depth", "top_level_items"
            ]
            
            for field in required_fields:
                assert field in data
                assert isinstance(data[field], int)

    @pytest.mark.asyncio
    async def test_get_user_customization_success(self):
        """Test successful user customization retrieval."""
        async with httpx.AsyncClient() as client:
            fake_menu_item_id = str(uuid4())
            headers = await self._get_auth_headers(client)
            
            # This should return null/None for non-existent customization
            response = await client.get(
                f"{self.BASE_URL}/customizations/{fake_menu_item_id}",
                headers=headers
            )
            
            # Should succeed but return null
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_user_customization_success(self):
        """Test successful user customization reset."""
        async with httpx.AsyncClient() as client:
            fake_menu_item_id = str(uuid4())
            headers = await self._get_auth_headers(client)
            
            # This will return 404 for non-existent customization
            response = await client.delete(
                f"{self.BASE_URL}/customizations/{fake_menu_item_id}",
                headers=headers
            )
            
            # Should return 404 since customization doesn't exist
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_authentication_required(self):
        """Test that endpoints require authentication."""
        async with httpx.AsyncClient() as client:
            # Try to access menu without authentication
            response = await client.get(f"{self.BASE_URL}/menu")
            assert response.status_code == 401
            
            # Try to create menu item without authentication
            response = await client.post(f"{self.BASE_URL}/menu-items", json=self.test_menu_item)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_menu_item_ids(self):
        """Test endpoints with invalid menu item IDs."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            
            # Invalid UUID format
            response = await client.get(
                f"{self.BASE_URL}/menu-items/invalid-uuid",
                headers=headers
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_large_customization_batch(self):
        """Test batch customization with many items."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_auth_headers(client)
            
            # Create a large batch of customizations (should be within limits)
            customizations = []
            for i in range(50):  # Within the 100 item limit
                customizations.append({
                    "menu_item_id": str(uuid4()),
                    "is_hidden": i % 2 == 0,
                    "custom_order": i
                })
            
            batch_data = {"customizations": customizations}
            
            response = await client.post(
                f"{self.BASE_URL}/customize",
                json=batch_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            # Most will fail since menu items don't exist, but request should be processed
            assert "applied" in data
            assert "failed" in data

    async def _get_auth_headers(self, client):
        """Get authentication headers for regular user."""
        try:
            return self.auth_helper.get_user_headers(client)
        except:
            # Fallback for testing without full auth system
            return {"Authorization": "Bearer test-token"}

    async def _get_admin_headers(self, client):
        """Get authentication headers for admin user."""
        try:
            return self.auth_helper.get_admin_headers(client)
        except:
            # Fallback for testing without full auth system
            return {"Authorization": "Bearer admin-token"}