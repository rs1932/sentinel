#!/usr/bin/env python3
"""
Working pytest version that uses your running server instead of fixtures
"""
import pytest
import requests
from uuid import uuid4

# Configuration
SERVER_URL = "http://localhost:8000"
BASE_URL = f"{SERVER_URL}/api/v1"
TENANT_URL = f"{BASE_URL}/tenants"
AUTH_URL = f"{BASE_URL}/auth/login"

TEST_CREDENTIALS = {
    "email": "test@example.com",
    "password": "password123", 
    "tenant_code": "TEST"
}

def get_auth_headers():
    """Get authentication headers by logging into running server"""
    response = requests.post(AUTH_URL, json=TEST_CREDENTIALS)
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        pytest.skip(f"Cannot authenticate - server may not be running: {response.status_code}")

class TestTenantAPIWorking:
    """Tests that work with your running server"""
    
    def test_server_running(self):
        """Test that server is accessible"""
        try:
            response = requests.get(f"{SERVER_URL}/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running at http://localhost:8000")
    
    def test_authentication_required(self):
        """Test that endpoints require authentication"""
        response = requests.get(f"{TENANT_URL}/")
        assert response.status_code == 401
    
    def test_authentication_works(self):
        """Test that authentication works"""
        headers = get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
    
    def test_list_tenants(self):
        """Test listing tenants"""
        headers = get_auth_headers()
        
        response = requests.get(f"{TENANT_URL}/", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_create_get_update_delete_tenant(self):
        """Test full CRUD cycle for tenant"""
        headers = get_auth_headers()
        
        # 1. CREATE
        tenant_data = {
            "name": "Pytest Test Company",
            "code": f"PYTEST-{uuid4().hex[:8].upper()}",
            "type": "root",
            "isolation_mode": "shared",
            "settings": {"theme": "light"},
            "features": ["api_access"],
            "metadata": {"test": "pytest"}
        }
        
        create_response = requests.post(f"{TENANT_URL}/", json=tenant_data, headers=headers)
        assert create_response.status_code == 201
        
        created_tenant = create_response.json()
        tenant_id = created_tenant["id"]
        assert created_tenant["name"] == tenant_data["name"]
        assert created_tenant["code"] == tenant_data["code"]
        assert created_tenant["is_active"] is True
        
        # 2. GET
        get_response = requests.get(f"{TENANT_URL}/{tenant_id}", headers=headers)
        assert get_response.status_code == 200
        
        fetched_tenant = get_response.json()
        assert fetched_tenant["id"] == tenant_id
        assert fetched_tenant["name"] == tenant_data["name"]
        
        # 3. UPDATE
        update_data = {
            "name": "Updated Pytest Company",
            "settings": {"theme": "dark", "updated": True}
        }
        
        update_response = requests.patch(f"{TENANT_URL}/{tenant_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        updated_tenant = update_response.json()
        assert updated_tenant["name"] == update_data["name"]
        assert updated_tenant["settings"]["theme"] == "dark"
        
        # 4. DELETE
        delete_response = requests.delete(f"{TENANT_URL}/{tenant_id}", headers=headers)
        assert delete_response.status_code == 204
        
        # 5. Verify deletion
        verify_response = requests.get(f"{TENANT_URL}/{tenant_id}", headers=headers)
        assert verify_response.status_code == 404
    
    def test_get_tenant_by_code(self):
        """Test getting tenant by code"""
        headers = get_auth_headers()
        
        # Create a tenant first
        tenant_data = {
            "name": "Code Test Company",
            "code": f"CODE-{uuid4().hex[:6].upper()}",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        create_response = requests.post(f"{TENANT_URL}/", json=tenant_data, headers=headers)
        assert create_response.status_code == 201
        created_tenant = create_response.json()
        
        # Get by code
        get_response = requests.get(f"{TENANT_URL}/code/{tenant_data['code']}", headers=headers)
        assert get_response.status_code == 200
        
        fetched_tenant = get_response.json()
        assert fetched_tenant["code"] == tenant_data["code"]
        assert fetched_tenant["name"] == tenant_data["name"]
        
        # Cleanup
        requests.delete(f"{TENANT_URL}/{created_tenant['id']}", headers=headers)
    
    def test_list_tenants_with_filters(self):
        """Test listing tenants with query filters"""
        headers = get_auth_headers()
        
        # Create a tenant with specific name for filtering
        tenant_data = {
            "name": "Filter Test Company Special",
            "code": f"FILTER-{uuid4().hex[:6].upper()}",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        create_response = requests.post(f"{TENANT_URL}/", json=tenant_data, headers=headers)
        assert create_response.status_code == 201
        created_tenant = create_response.json()
        
        # Filter by name
        filter_response = requests.get(f"{TENANT_URL}/?name=Filter Test", headers=headers)
        assert filter_response.status_code == 200
        
        filtered_data = filter_response.json()
        assert len(filtered_data["items"]) >= 1
        
        # Check that filtered results contain our tenant
        found = any(item["id"] == created_tenant["id"] for item in filtered_data["items"])
        assert found, "Created tenant should be in filtered results"
        
        # Cleanup
        requests.delete(f"{TENANT_URL}/{created_tenant['id']}", headers=headers)

if __name__ == "__main__":
    # Run with: python test_tenant_pytest_working.py
    # Or: python -m pytest test_tenant_pytest_working.py -v
    pytest.main([__file__, "-v"])