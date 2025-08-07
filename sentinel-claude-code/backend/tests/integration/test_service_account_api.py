"""
Integration tests for Service Account Management API (Module 3)
Tests the complete service account management workflow with JWT authentication
"""
import pytest
import httpx
import uuid
from typing import Dict, Any


class TestServiceAccountAPI:
    """Integration tests for Service Account Management API"""
    
    BASE_URL = "http://localhost:8000/api/v1"
    AUTH_URL = f"{BASE_URL}/auth/login"
    SA_URL = f"{BASE_URL}/service-accounts"
    
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
    def sample_service_account_data(self):
        """Sample service account data for testing"""
        return {
            "name": f"Test Service Account {uuid.uuid4().hex[:8]}",
            "description": "Service account for testing integration",
            "attributes": {
                "service_type": "integration",
                "allowed_ips": ["192.168.1.0/24"],
                "environment": "test"
            },
            "is_active": True
        }
    
    @pytest.mark.asyncio
    async def test_service_account_crud_workflow(self, auth_headers, sample_service_account_data):
        """Test complete CRUD workflow for service accounts"""
        async with httpx.AsyncClient() as client:
            # 1. CREATE SERVICE ACCOUNT
            create_response = await client.post(
                self.SA_URL + "/",
                json=sample_service_account_data,
                headers=auth_headers
            )
            
            assert create_response.status_code == 201
            create_result = create_response.json()
            
            # Verify response structure
            assert "service_account" in create_result
            assert "credentials" in create_result
            
            service_account = create_result["service_account"]
            credentials = create_result["credentials"]
            account_id = service_account["id"]
            
            # Verify service account data
            assert service_account["name"] == sample_service_account_data["name"]
            assert service_account["is_active"] == sample_service_account_data["is_active"]
            assert service_account["attributes"] == sample_service_account_data["attributes"]
            assert service_account["client_id"].startswith("svc_")
            
            # Verify credentials
            assert credentials["client_id"].startswith("svc_")
            assert len(credentials["client_secret"]) > 20  # Should be a long secret
            assert "created_at" in credentials
            
            # Store credentials for later tests
            client_id = credentials["client_id"]
            client_secret = credentials["client_secret"]
            
            # 2. GET SERVICE ACCOUNT
            get_response = await client.get(
                f"{self.SA_URL}/{account_id}",
                headers=auth_headers
            )
            
            assert get_response.status_code == 200
            fetched_account = get_response.json()
            assert fetched_account["id"] == account_id
            assert fetched_account["name"] == sample_service_account_data["name"]
            assert fetched_account["client_id"] == client_id
            
            # 3. UPDATE SERVICE ACCOUNT
            update_data = {
                "name": f"Updated {sample_service_account_data['name']}",
                "description": "Updated description for testing",
                "attributes": {
                    "service_type": "api_integration",
                    "environment": "production"
                },
                "is_active": False
            }
            
            update_response = await client.patch(
                f"{self.SA_URL}/{account_id}",
                json=update_data,
                headers=auth_headers
            )
            
            assert update_response.status_code == 200
            updated_account = update_response.json()
            assert updated_account["name"] == update_data["name"]
            assert updated_account["is_active"] == update_data["is_active"]
            assert updated_account["attributes"]["service_type"] == "api_integration"
            
            # 4. LIST SERVICE ACCOUNTS
            list_response = await client.get(
                f"{self.SA_URL}/",
                headers=auth_headers
            )
            
            assert list_response.status_code == 200
            accounts_list = list_response.json()
            assert "items" in accounts_list
            assert "total" in accounts_list
            assert accounts_list["total"] >= 1
            
            # Find our service account in the list
            our_account = next((a for a in accounts_list["items"] if a["id"] == account_id), None)
            assert our_account is not None
            
            # 5. ROTATE CREDENTIALS
            rotate_response = await client.post(
                f"{self.SA_URL}/{account_id}/rotate-credentials",
                headers=auth_headers
            )
            
            assert rotate_response.status_code == 200
            new_credentials = rotate_response.json()
            assert new_credentials["client_id"] == client_id  # Should be same client_id
            assert new_credentials["client_secret"] != client_secret  # Should be different secret
            assert len(new_credentials["client_secret"]) > 20
            
            # 6. VALIDATE CREDENTIALS
            validate_response = await client.get(
                f"{self.SA_URL}/{account_id}/validate",
                params={"client_secret": new_credentials["client_secret"]},
                headers=auth_headers
            )
            
            assert validate_response.status_code == 200
            validation_result = validate_response.json()
            assert validation_result["valid"] == True
            assert validation_result["account_id"] == account_id
            assert validation_result["client_id"] == client_id
            
            # 7. DELETE SERVICE ACCOUNT
            delete_response = await client.delete(
                f"{self.SA_URL}/{account_id}",
                headers=auth_headers
            )
            
            assert delete_response.status_code == 204
            
            # 8. VERIFY DELETION
            verify_response = await client.get(
                f"{self.SA_URL}/{account_id}",
                headers=auth_headers
            )
            
            # Service account should either be not found or inactive (soft delete)
            if verify_response.status_code == 200:
                deleted_account = verify_response.json()
                assert deleted_account["is_active"] == False
            else:
                assert verify_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_service_accounts_with_filters(self, auth_headers, sample_service_account_data):
        """Test listing service accounts with various filters"""
        async with httpx.AsyncClient() as client:
            # Create a service account first
            create_response = await client.post(
                self.SA_URL + "/",
                json=sample_service_account_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            account_id = create_response.json()["service_account"]["id"]
            
            try:
                # Test search by name
                search_response = await client.get(
                    f"{self.SA_URL}/",
                    params={"search": sample_service_account_data["name"][:10]},
                    headers=auth_headers
                )
                assert search_response.status_code == 200
                search_results = search_response.json()
                assert len(search_results["items"]) >= 1
                
                # Test filter by active status
                active_response = await client.get(
                    f"{self.SA_URL}/",
                    params={"is_active": True},
                    headers=auth_headers
                )
                assert active_response.status_code == 200
                active_results = active_response.json()
                assert all(account["is_active"] for account in active_results["items"])
                
                # Test pagination
                paginated_response = await client.get(
                    f"{self.SA_URL}/",
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
                await client.delete(f"{self.SA_URL}/{account_id}", headers=auth_headers)
    
    @pytest.mark.asyncio
    async def test_credential_rotation_with_options(self, auth_headers, sample_service_account_data):
        """Test credential rotation with different options"""
        async with httpx.AsyncClient() as client:
            # Create a service account first
            create_response = await client.post(
                self.SA_URL + "/",
                json=sample_service_account_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            account_id = create_response.json()["service_account"]["id"]
            original_secret = create_response.json()["credentials"]["client_secret"]
            
            try:
                # Test rotation with explicit options
                rotation_data = {
                    "revoke_existing": True
                }
                
                rotate_response = await client.post(
                    f"{self.SA_URL}/{account_id}/rotate-credentials",
                    json=rotation_data,
                    headers=auth_headers
                )
                
                assert rotate_response.status_code == 200
                new_credentials = rotate_response.json()
                
                # Verify new secret is different
                assert new_credentials["client_secret"] != original_secret
                assert len(new_credentials["client_secret"]) > 20
                
                # Verify old secret is no longer valid (if validation supported)
                old_validate_response = await client.get(
                    f"{self.SA_URL}/{account_id}/validate",
                    params={"client_secret": original_secret},
                    headers=auth_headers
                )
                
                if old_validate_response.status_code == 200:
                    old_validation = old_validate_response.json()
                    assert old_validation["valid"] == False
                
            finally:
                # Cleanup
                await client.delete(f"{self.SA_URL}/{account_id}", headers=auth_headers)
    
    @pytest.mark.asyncio
    async def test_invalid_credential_validation(self, auth_headers, sample_service_account_data):
        """Test validation with invalid credentials"""
        async with httpx.AsyncClient() as client:
            # Create a service account first
            create_response = await client.post(
                self.SA_URL + "/",
                json=sample_service_account_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            account_id = create_response.json()["service_account"]["id"]
            
            try:
                # Test validation with invalid secret
                validate_response = await client.get(
                    f"{self.SA_URL}/{account_id}/validate",
                    params={"client_secret": "invalid_secret_12345"},
                    headers=auth_headers
                )
                
                assert validate_response.status_code == 200
                validation_result = validate_response.json()
                assert validation_result["valid"] == False
                assert validation_result["account_id"] == account_id
                
            finally:
                # Cleanup
                await client.delete(f"{self.SA_URL}/{account_id}", headers=auth_headers)
    
    @pytest.mark.asyncio
    async def test_authentication_required(self):
        """Test that endpoints require authentication"""
        async with httpx.AsyncClient() as client:
            # Try to access service account list without authentication
            response = await client.get(f"{self.SA_URL}/")
            assert response.status_code == 401
            
            # Try to create service account without authentication
            response = await client.post(
                self.SA_URL + "/",
                json={"name": "Test Service Account"}
            )
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_validation_errors(self, auth_headers):
        """Test input validation"""
        async with httpx.AsyncClient() as client:
            # Test invalid name (too short)
            invalid_data = {
                "name": "TS",  # Too short
                "description": "Test service account"
            }
            
            response = await client.post(
                self.SA_URL + "/",
                json=invalid_data,
                headers=auth_headers
            )
            assert response.status_code == 422
            
            # Test invalid name (special characters)
            invalid_chars_data = {
                "name": "Test Service Account @#$",  # Invalid characters
                "description": "Test service account"
            }
            
            response = await client.post(
                self.SA_URL + "/",
                json=invalid_chars_data,
                headers=auth_headers
            )
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_duplicate_service_account_creation(self, auth_headers, sample_service_account_data):
        """Test that duplicate service accounts cannot be created"""
        async with httpx.AsyncClient() as client:
            # Create first service account
            first_response = await client.post(
                self.SA_URL + "/",
                json=sample_service_account_data,
                headers=auth_headers
            )
            assert first_response.status_code == 201
            account_id = first_response.json()["service_account"]["id"]
            
            try:
                # Try to create duplicate service account (same name)
                duplicate_response = await client.post(
                    self.SA_URL + "/",
                    json=sample_service_account_data,
                    headers=auth_headers
                )
                assert duplicate_response.status_code == 409  # Conflict
                
            finally:
                # Cleanup
                await client.delete(f"{self.SA_URL}/{account_id}", headers=auth_headers)
    
    @pytest.mark.asyncio
    async def test_hard_delete_service_account(self, auth_headers, sample_service_account_data):
        """Test hard delete of service account"""
        async with httpx.AsyncClient() as client:
            # Create a service account first
            create_response = await client.post(
                self.SA_URL + "/",
                json=sample_service_account_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            account_id = create_response.json()["service_account"]["id"]
            
            # Hard delete
            delete_response = await client.delete(
                f"{self.SA_URL}/{account_id}",
                params={"hard_delete": True},
                headers=auth_headers
            )
            
            assert delete_response.status_code == 204
            
            # Verify hard deletion (should be 404)
            verify_response = await client.get(
                f"{self.SA_URL}/{account_id}",
                headers=auth_headers
            )
            assert verify_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_service_account_client_id_format(self, auth_headers, sample_service_account_data):
        """Test that client_id follows expected format"""
        async with httpx.AsyncClient() as client:
            create_response = await client.post(
                self.SA_URL + "/",
                json=sample_service_account_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            
            credentials = create_response.json()["credentials"]
            client_id = credentials["client_id"]
            account_id = create_response.json()["service_account"]["id"]
            
            try:
                # Verify client_id format
                assert client_id.startswith("svc_")
                assert len(client_id) > 10  # Should be reasonably long
                assert "_" in client_id[4:]  # Should have underscores for name formatting
                
            finally:
                # Cleanup
                await client.delete(f"{self.SA_URL}/{account_id}", headers=auth_headers)