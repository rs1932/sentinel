"""
Integration tests for Field Definition API (Module 8)
Tests all Field Definition endpoints with comprehensive scenarios
"""
import pytest
import httpx
from uuid import uuid4
from datetime import datetime, timezone

from src.models import FieldDefinition, FieldType, FieldDataType, FieldPermission
from tests.auth_helpers import SyncAuthHelper, DEFAULT_USER_CREDENTIALS


class TestFieldDefinitionAPI:
    """Test Field Definition API endpoints."""
    
    BASE_URL = "http://testserver/api/v1/field-definitions"
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Set up test data before each test."""
        # Create test user with necessary permissions
        self.user_data = await create_test_user(
            email="field_test@example.com",
            scopes=["field_definition:read", "field_definition:write", "field_definition:admin"]
        )
        self.auth_headers = await get_auth_headers(self.user_data["email"])
        
        # Sample field definition data
        self.sample_field_data = {
            "entity_type": "vessel",
            "field_name": "test_field",
            "field_type": "platform_dynamic",
            "data_type": "string",
            "storage_path": "custom_attributes.test_field",
            "display_name": "Test Field",
            "description": "A test field for validation",
            "validation_rules": {"max_length": 100},
            "default_visibility": "read",
            "is_indexed": False,
            "is_required": False
        }

    @pytest.mark.asyncio
    async def test_create_field_definition_success(self):
        """Test successful field definition creation."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL + "/",
                json=self.sample_field_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            
            # Verify response structure
            assert "id" in data
            assert data["entity_type"] == self.sample_field_data["entity_type"]
            assert data["field_name"] == self.sample_field_data["field_name"]
            assert data["field_type"] == self.sample_field_data["field_type"]
            assert data["data_type"] == self.sample_field_data["data_type"]
            assert data["storage_path"] == self.sample_field_data["storage_path"]
            assert data["display_name"] == self.sample_field_data["display_name"]
            assert "created_at" in data
            assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_field_definition_core_type(self):
        """Test creating core field definition."""
        core_field_data = {
            "entity_type": "user",
            "field_name": "core_test_field",
            "field_type": "core",
            "data_type": "string",
            "storage_column": "core_test_field",
            "display_name": "Core Test Field",
            "description": "A core test field",
            "default_visibility": "write"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL + "/",
                json=core_field_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["field_type"] == "core"
            assert data["storage_column"] == "core_test_field"
            assert data["storage_path"] is None

    @pytest.mark.asyncio
    async def test_create_field_definition_validation_errors(self):
        """Test field definition creation validation errors."""
        # Test invalid field type
        invalid_field_data = self.sample_field_data.copy()
        invalid_field_data["field_type"] = "invalid_type"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL + "/",
                json=invalid_field_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 400
            
        # Test invalid data type
        invalid_field_data = self.sample_field_data.copy()
        invalid_field_data["data_type"] = "invalid_data_type"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL + "/",
                json=invalid_field_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_field_definition_duplicate_error(self):
        """Test duplicate field definition creation error."""
        # Create first field definition
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL + "/",
                json=self.sample_field_data,
                headers=self.auth_headers
            )
            assert response.status_code == 201
            
            # Try to create duplicate
            response = await client.post(
                self.BASE_URL + "/",
                json=self.sample_field_data,
                headers=self.auth_headers
            )
            assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_list_field_definitions(self):
        """Test listing field definitions."""
        # Create some test field definitions
        field_data_1 = self.sample_field_data.copy()
        field_data_1["field_name"] = "test_field_1"
        field_data_1["storage_path"] = "custom_attributes.test_field_1"
        
        field_data_2 = self.sample_field_data.copy()
        field_data_2["field_name"] = "test_field_2"
        field_data_2["entity_type"] = "container"
        field_data_2["storage_path"] = "custom_attributes.test_field_2"
        
        async with httpx.AsyncClient() as client:
            # Create test data
            await client.post(self.BASE_URL + "/", json=field_data_1, headers=self.auth_headers)
            await client.post(self.BASE_URL + "/", json=field_data_2, headers=self.auth_headers)
            
            # Test list all
            response = await client.get(self.BASE_URL + "/", headers=self.auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert len(data["items"]) >= 2
            
            # Test filter by entity type
            response = await client.get(
                self.BASE_URL + "/?entity_type=vessel",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            vessel_fields = [item for item in data["items"] if item["entity_type"] == "vessel"]
            assert len(vessel_fields) >= 1
            
            # Test search
            response = await client.get(
                self.BASE_URL + "/?search=test_field_1",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_field_definition_by_id(self):
        """Test getting field definition by ID."""
        # Create a field definition
        async with httpx.AsyncClient() as client:
            create_response = await client.post(
                self.BASE_URL + "/",
                json=self.sample_field_data,
                headers=self.auth_headers
            )
            assert create_response.status_code == 201
            field_id = create_response.json()["id"]
            
            # Get by ID
            response = await client.get(
                f"{self.BASE_URL}/{field_id}",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == field_id
            assert "is_platform_wide" in data
            assert "full_field_path" in data
            assert "storage_info" in data

    @pytest.mark.asyncio
    async def test_get_field_definition_not_found(self):
        """Test getting non-existent field definition."""
        fake_id = str(uuid4())
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{fake_id}",
                headers=self.auth_headers
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_field_definition(self):
        """Test updating field definition."""
        # Create a field definition
        async with httpx.AsyncClient() as client:
            create_response = await client.post(
                self.BASE_URL + "/",
                json=self.sample_field_data,
                headers=self.auth_headers
            )
            assert create_response.status_code == 201
            field_id = create_response.json()["id"]
            
            # Update field definition
            update_data = {
                "display_name": "Updated Test Field",
                "description": "Updated description",
                "default_visibility": "write"
            }
            
            response = await client.patch(
                f"{self.BASE_URL}/{field_id}",
                json=update_data,
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["display_name"] == update_data["display_name"]
            assert data["description"] == update_data["description"]
            assert data["default_visibility"] == update_data["default_visibility"]

    @pytest.mark.asyncio
    async def test_delete_field_definition(self):
        """Test deleting field definition."""
        # Create a field definition
        async with httpx.AsyncClient() as client:
            create_response = await client.post(
                self.BASE_URL + "/",
                json=self.sample_field_data,
                headers=self.auth_headers
            )
            assert create_response.status_code == 201
            field_id = create_response.json()["id"]
            
            # Delete field definition
            response = await client.delete(
                f"{self.BASE_URL}/{field_id}",
                headers=self.auth_headers
            )
            assert response.status_code == 204
            
            # Verify it's marked as inactive
            response = await client.get(
                f"{self.BASE_URL}/{field_id}",
                headers=self.auth_headers
            )
            # Should still exist but be inactive
            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] == False

    @pytest.mark.asyncio
    async def test_get_field_definitions_by_entity(self):
        """Test getting field definitions by entity type."""
        # Create field definitions for different entities
        vessel_field = self.sample_field_data.copy()
        vessel_field["field_name"] = "vessel_specific"
        vessel_field["storage_path"] = "custom_attributes.vessel_specific"
        
        container_field = self.sample_field_data.copy()
        container_field["entity_type"] = "container"
        container_field["field_name"] = "container_specific"
        container_field["storage_path"] = "custom_attributes.container_specific"
        
        async with httpx.AsyncClient() as client:
            await client.post(self.BASE_URL + "/", json=vessel_field, headers=self.auth_headers)
            await client.post(self.BASE_URL + "/", json=container_field, headers=self.auth_headers)
            
            # Get vessel fields
            response = await client.get(
                f"{self.BASE_URL}/entity/vessel",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            vessel_fields = [field for field in data if field["entity_type"] == "vessel"]
            assert len(vessel_fields) >= 1

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test getting field definition statistics."""
        # Create some test data
        async with httpx.AsyncClient() as client:
            await client.post(self.BASE_URL + "/", json=self.sample_field_data, headers=self.auth_headers)
            
            response = await client.get(
                f"{self.BASE_URL}/statistics",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "total_definitions" in data
            assert "by_entity_type" in data
            assert "by_field_type" in data
            assert "by_data_type" in data
            assert "active_definitions" in data
            assert "inactive_definitions" in data

    @pytest.mark.asyncio
    async def test_bulk_operations(self):
        """Test bulk operations on field definitions."""
        # Create multiple field definitions
        field_ids = []
        
        async with httpx.AsyncClient() as client:
            for i in range(3):
                field_data = self.sample_field_data.copy()
                field_data["field_name"] = f"bulk_test_field_{i}"
                field_data["storage_path"] = f"custom_attributes.bulk_test_field_{i}"
                
                response = await client.post(
                    self.BASE_URL + "/",
                    json=field_data,
                    headers=self.auth_headers
                )
                assert response.status_code == 201
                field_ids.append(response.json()["id"])
            
            # Test bulk deactivate
            bulk_data = {
                "field_definition_ids": field_ids,
                "operation": "deactivate"
            }
            
            response = await client.post(
                f"{self.BASE_URL}/bulk",
                json=bulk_data,
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["operation"] == "deactivate"
            assert data["processed"] == 3
            assert data["failed"] == 0

    @pytest.mark.asyncio
    async def test_field_permission_check(self):
        """Test field permission checking."""
        permission_check = {
            "user_id": str(self.user_data["id"]),
            "entity_type": "vessel",
            "fields": ["test_field", "another_field"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/field-permissions/check",
                json=permission_check,
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "field_permissions" in data
            assert "user_id" in data
            assert "entity_type" in data
            assert "checked_fields" in data

    @pytest.mark.asyncio
    async def test_get_field_permissions_via_query(self):
        """Test getting field permissions via query parameters."""
        user_id = str(self.user_data["id"])
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/field-permissions?user_id={user_id}&entity_type=vessel&fields=field1,field2",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "field_permissions" in data
            assert data["user_id"] == user_id
            assert data["entity_type"] == "vessel"

    @pytest.mark.asyncio
    async def test_get_field_types(self):
        """Test getting available field types."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/types/field-types",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert "core" in data
            assert "platform_dynamic" in data
            assert "tenant_specific" in data

    @pytest.mark.asyncio
    async def test_get_data_types(self):
        """Test getting available data types."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/types/data-types",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert "string" in data
            assert "number" in data
            assert "boolean" in data

    @pytest.mark.asyncio
    async def test_get_field_permission_types(self):
        """Test getting available field permission types."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/types/permissions",
                headers=self.auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert "read" in data
            assert "write" in data
            assert "hidden" in data

    @pytest.mark.asyncio
    async def test_authentication_required(self):
        """Test that endpoints require authentication."""
        async with httpx.AsyncClient() as client:
            # Try to access field definitions without authentication
            response = await client.get(f"{self.BASE_URL}/")
            assert response.status_code == 401
            
            # Try to create field definition without authentication
            response = await client.post(f"{self.BASE_URL}/", json=self.sample_field_data)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_storage_configuration_validation(self):
        """Test storage configuration validation for different field types."""
        # Test core field without storage_column
        core_field_invalid = {
            "entity_type": "vessel",
            "field_name": "invalid_core",
            "field_type": "core",
            "data_type": "string",
            "storage_path": "should_not_be_set"  # Invalid for core
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL + "/",
                json=core_field_invalid,
                headers=self.auth_headers
            )
            assert response.status_code == 400
            
        # Test dynamic field without storage_path
        dynamic_field_invalid = {
            "entity_type": "vessel",
            "field_name": "invalid_dynamic",
            "field_type": "platform_dynamic",
            "data_type": "string",
            "storage_column": "should_not_be_set"  # Invalid for dynamic
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL + "/",
                json=dynamic_field_invalid,
                headers=self.auth_headers
            )
            assert response.status_code == 400