"""
Integration tests for User Management API (Module 3)
Tests the complete user management workflow with JWT authentication
"""
import pytest
import httpx
import uuid
from typing import Dict, Any


class TestUserAPI:
    """Integration tests for User Management API"""
    
    BASE_URL = "http://localhost:8000/api/v1"
    AUTH_URL = f"{BASE_URL}/auth/login"
    USER_URL = f"{BASE_URL}/users"
    
    TEST_CREDENTIALS = {
        "email": "test@example.com",
        "password": "password123",
        "tenant_code": "TEST"
    }
    
    @pytest.fixture
    async def auth_headers(self):
        """Get authentication headers for API requests"""
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(self.AUTH_URL, json=self.TEST_CREDENTIALS)
            
            if auth_response.status_code != 200:
                pytest.skip(f"Cannot authenticate - server may not be running: {auth_response.status_code}")
            
            token_data = auth_response.json()
            access_token = token_data["access_token"]
            return {"Authorization": f"Bearer {access_token}"}
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"testuser_{uuid.uuid4().hex[:6]}",
            "password": "testpassword123",
            "attributes": {
                "department": "engineering",
                "location": "remote"
            },
            "preferences": {
                "theme": "dark",
                "notifications": True
            },
            "is_active": True,
            "send_invitation": False
        }
    
    @pytest.mark.asyncio
    async def test_user_crud_workflow(self, auth_headers, sample_user_data):
        """Test complete CRUD workflow for users"""
        async with httpx.AsyncClient() as client:
            # 1. CREATE USER
            create_response = await client.post(
                self.USER_URL + "/",
                json=sample_user_data,
                headers=auth_headers
            )
            
            assert create_response.status_code == 201
            created_user = create_response.json()
            user_id = created_user["id"]
            
            assert created_user["email"] == sample_user_data["email"]
            assert created_user["username"] == sample_user_data["username"]
            assert created_user["is_active"] == sample_user_data["is_active"]
            assert created_user["attributes"] == sample_user_data["attributes"]
            
            # 2. GET USER
            get_response = await client.get(
                f"{self.USER_URL}/{user_id}",
                headers=auth_headers
            )
            
            assert get_response.status_code == 200
            fetched_user = get_response.json()
            assert fetched_user["id"] == user_id
            assert fetched_user["email"] == sample_user_data["email"]
            
            # 3. UPDATE USER
            update_data = {
                "username": f"updated_{sample_user_data['username']}",
                "attributes": {
                    "department": "marketing",
                    "location": "office"
                },
                "is_active": False
            }
            
            update_response = await client.patch(
                f"{self.USER_URL}/{user_id}",
                json=update_data,
                headers=auth_headers
            )
            
            assert update_response.status_code == 200
            updated_user = update_response.json()
            assert updated_user["username"] == update_data["username"]
            assert updated_user["is_active"] == update_data["is_active"]
            assert updated_user["attributes"]["department"] == "marketing"
            
            # 4. LIST USERS (should include our created user)
            list_response = await client.get(
                f"{self.USER_URL}/",
                headers=auth_headers
            )
            
            assert list_response.status_code == 200
            users_list = list_response.json()
            assert "items" in users_list
            assert "total" in users_list
            assert users_list["total"] >= 1
            
            # Find our user in the list
            our_user = next((u for u in users_list["items"] if u["id"] == user_id), None)
            assert our_user is not None
            
            # 5. DELETE USER (soft delete)
            delete_response = await client.delete(
                f"{self.USER_URL}/{user_id}",
                headers=auth_headers
            )
            
            assert delete_response.status_code == 204
            
            # 6. VERIFY DELETION (should return 404 or be inactive)
            verify_response = await client.get(
                f"{self.USER_URL}/{user_id}",
                headers=auth_headers
            )
            
            # User should either be not found or inactive (soft delete)
            if verify_response.status_code == 200:
                deleted_user = verify_response.json()
                assert deleted_user["is_active"] == False
            else:
                assert verify_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_users_with_filters(self, auth_headers, sample_user_data):
        """Test listing users with various filters"""
        async with httpx.AsyncClient() as client:
            # Create a user first
            create_response = await client.post(
                self.USER_URL + "/",
                json=sample_user_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            created_user = create_response.json()
            user_id = created_user["id"]
            
            try:
                # Test search by email
                search_response = await client.get(
                    f"{self.USER_URL}/",
                    params={"search": sample_user_data["email"][:10]},
                    headers=auth_headers
                )
                assert search_response.status_code == 200
                search_results = search_response.json()
                assert len(search_results["items"]) >= 1
                
                # Test filter by active status
                active_response = await client.get(
                    f"{self.USER_URL}/",
                    params={"is_active": True},
                    headers=auth_headers
                )
                assert active_response.status_code == 200
                active_results = active_response.json()
                assert all(user["is_active"] for user in active_results["items"])
                
                # Test pagination
                paginated_response = await client.get(
                    f"{self.USER_URL}/",
                    params={"page": 1, "limit": 5},
                    headers=auth_headers
                )
                assert paginated_response.status_code == 200
                paginated_results = paginated_response.json()
                assert len(paginated_results["items"]) <= 5
                assert paginated_results["page"] == 1
                assert paginated_results["limit"] == 5
                
            finally:
                # Cleanup
                await client.delete(f"{self.USER_URL}/{user_id}", headers=auth_headers)
    
    @pytest.mark.asyncio
    async def test_user_permissions_endpoint(self, auth_headers, sample_user_data):
        """Test user permissions endpoint (placeholder implementation)"""
        async with httpx.AsyncClient() as client:
            # Create a user first
            create_response = await client.post(
                self.USER_URL + "/",
                json=sample_user_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            user_id = create_response.json()["id"]
            
            try:
                # Get user permissions
                permissions_response = await client.get(
                    f"{self.USER_URL}/{user_id}/permissions",
                    headers=auth_headers
                )
                
                assert permissions_response.status_code == 200
                permissions = permissions_response.json()
                
                # Verify placeholder structure
                assert "user_id" in permissions
                assert "tenant_id" in permissions
                assert "direct_permissions" in permissions
                assert "inherited_permissions" in permissions
                assert "effective_permissions" in permissions
                
                assert permissions["user_id"] == user_id
                # Placeholder should return empty permission lists
                assert permissions["direct_permissions"] == []
                assert permissions["inherited_permissions"] == []
                assert permissions["effective_permissions"] == []
                
            finally:
                # Cleanup
                await client.delete(f"{self.USER_URL}/{user_id}", headers=auth_headers)
    
    @pytest.mark.asyncio
    async def test_bulk_operations(self, auth_headers):
        """Test bulk user operations"""
        async with httpx.AsyncClient() as client:
            # Create multiple users for bulk operations
            user_ids = []
            for i in range(3):
                user_data = {
                    "email": f"bulkuser{i}_{uuid.uuid4().hex[:8]}@example.com",
                    "username": f"bulkuser{i}",
                    "password": "testpassword123",
                    "is_active": True
                }
                
                create_response = await client.post(
                    self.USER_URL + "/",
                    json=user_data,
                    headers=auth_headers
                )
                assert create_response.status_code == 201
                user_ids.append(create_response.json()["id"])
            
            try:
                # Test bulk deactivate
                bulk_data = {
                    "operation": "deactivate",
                    "user_ids": user_ids
                }
                
                bulk_response = await client.post(
                    f"{self.USER_URL}/bulk",
                    json=bulk_data,
                    headers=auth_headers
                )
                
                assert bulk_response.status_code == 200
                bulk_result = bulk_response.json()
                
                assert bulk_result["operation"] == "deactivate"
                assert bulk_result["total_requested"] == 3
                assert bulk_result["successful"] >= 0  # Some might fail due to constraints
                assert bulk_result["failed"] >= 0
                assert bulk_result["successful"] + bulk_result["failed"] == 3
                
            finally:
                # Cleanup - delete all created users
                for user_id in user_ids:
                    await client.delete(f"{self.USER_URL}/{user_id}", headers=auth_headers)
    
    @pytest.mark.asyncio
    async def test_user_lock_unlock(self, auth_headers, sample_user_data):
        """Test user lock and unlock functionality"""
        async with httpx.AsyncClient() as client:
            # Create a user first
            create_response = await client.post(
                self.USER_URL + "/",
                json=sample_user_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            user_id = create_response.json()["id"]
            
            try:
                # Lock user
                lock_response = await client.post(
                    f"{self.USER_URL}/{user_id}/lock",
                    params={"duration_minutes": 60},
                    headers=auth_headers
                )
                assert lock_response.status_code == 204
                
                # Unlock user
                unlock_response = await client.post(
                    f"{self.USER_URL}/{user_id}/unlock",
                    headers=auth_headers
                )
                assert unlock_response.status_code == 204
                
            finally:
                # Cleanup
                await client.delete(f"{self.USER_URL}/{user_id}", headers=auth_headers)
    
    @pytest.mark.asyncio
    async def test_authentication_required(self):
        """Test that endpoints require authentication"""
        async with httpx.AsyncClient() as client:
            # Try to access user list without authentication
            response = await client.get(f"{self.USER_URL}/")
            assert response.status_code == 401
            
            # Try to create user without authentication
            response = await client.post(
                self.USER_URL + "/",
                json={"email": "test@example.com", "username": "test"}
            )
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_validation_errors(self, auth_headers):
        """Test input validation"""
        async with httpx.AsyncClient() as client:
            # Test invalid email
            invalid_data = {
                "email": "not-an-email",
                "username": "testuser",
                "password": "password123"
            }
            
            response = await client.post(
                self.USER_URL + "/",
                json=invalid_data,
                headers=auth_headers
            )
            assert response.status_code == 422
            
            # Test short password
            short_password_data = {
                "email": "valid@example.com",
                "username": "testuser",
                "password": "123"  # Too short
            }
            
            response = await client.post(
                self.USER_URL + "/",
                json=short_password_data,
                headers=auth_headers
            )
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_duplicate_user_creation(self, auth_headers, sample_user_data):
        """Test that duplicate users cannot be created"""
        async with httpx.AsyncClient() as client:
            # Create first user
            first_response = await client.post(
                self.USER_URL + "/",
                json=sample_user_data,
                headers=auth_headers
            )
            assert first_response.status_code == 201
            user_id = first_response.json()["id"]
            
            try:
                # Try to create duplicate user (same email)
                duplicate_response = await client.post(
                    self.USER_URL + "/",
                    json=sample_user_data,
                    headers=auth_headers
                )
                assert duplicate_response.status_code == 409  # Conflict
                
            finally:
                # Cleanup
                await client.delete(f"{self.USER_URL}/{user_id}", headers=auth_headers)