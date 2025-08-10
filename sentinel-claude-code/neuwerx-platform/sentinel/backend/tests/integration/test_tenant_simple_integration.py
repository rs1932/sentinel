"""
Simple Tenant Management Integration Tests
Tests against a running server without complex database fixtures
"""
import pytest
import httpx
from uuid import uuid4

# Server configuration
SERVER_URL = "http://localhost:8000"
BASE_URL = f"{SERVER_URL}/api/v1/sentinel"

@pytest.mark.integration
class TestTenantServerIntegration:
    """Integration tests that work with a running server"""
    
    def test_server_running(self):
        """Test that server is accessible"""
        try:
            response = httpx.get(f"{SERVER_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Server not running at http://localhost:8000")
        except httpx.ConnectError:
            pytest.skip("Server not running at http://localhost:8000")

    def test_tenant_health_endpoint(self):
        """Test tenant health endpoint"""
        try:
            response = httpx.get(f"{BASE_URL}/tenants/health", timeout=5)
            
            if response.status_code == 404:
                pytest.skip("Tenant health endpoint not available")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test tenant health endpoint")

    def test_list_tenants_no_auth(self):
        """Test listing tenants without authentication"""
        try:
            response = httpx.get(f"{BASE_URL}/tenants", timeout=5)
            
            # Should return 401 for unauthenticated request
            assert response.status_code == 401
            data = response.json()
            assert "error" in data or "detail" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test tenant list")

    def test_get_tenant_by_id_no_auth(self):
        """Test getting specific tenant without authentication"""
        try:
            tenant_id = str(uuid4())
            response = httpx.get(f"{BASE_URL}/tenants/{tenant_id}", timeout=5)
            
            # Should return 401 for unauthenticated request or 404 if not available
            assert response.status_code in [401, 404]
            data = response.json()
            assert "error" in data or "detail" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test tenant get")

    def test_create_tenant_no_auth(self):
        """Test creating tenant without authentication"""
        try:
            tenant_data = {
                "name": f"Test Tenant {uuid4().hex[:8]}",
                "code": f"TEST{uuid4().hex[:8].upper()}",
                "type": "root",
                "isolation_mode": "shared"
            }
            
            response = httpx.post(f"{BASE_URL}/tenants/", json=tenant_data, timeout=5)
            
            # Should return 401 for unauthenticated request or 404 if not available
            assert response.status_code in [401, 404]
            data = response.json()
            assert "error" in data or "detail" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test tenant create")

    def test_create_tenant_validation_errors(self):
        """Test tenant creation validation"""
        try:
            # Test empty request
            response = httpx.post(f"{BASE_URL}/tenants/", json={}, timeout=5)
            assert response.status_code in [401, 422, 404]  # Auth error, validation error, or not available
            
            # Test invalid data
            invalid_data = {
                "name": "",  # Empty name
                "code": "invalid-code-with-special@chars",
                "type": "invalid_type",
                "isolation_mode": "invalid_mode"
            }
            
            response = httpx.post(f"{BASE_URL}/tenants/", json=invalid_data, timeout=5)
            assert response.status_code in [401, 422, 404]
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test tenant validation")

    def test_update_tenant_no_auth(self):
        """Test updating tenant without authentication"""
        try:
            tenant_id = str(uuid4())
            update_data = {
                "name": "Updated Tenant Name"
            }
            
            response = httpx.patch(f"{BASE_URL}/tenants/{tenant_id}", json=update_data, timeout=5)
            
            # Should return 401 for unauthenticated request or 404 if not available
            assert response.status_code in [401, 404]
            data = response.json()
            assert "error" in data or "detail" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test tenant update")

    def test_delete_tenant_no_auth(self):
        """Test deleting tenant without authentication"""
        try:
            tenant_id = str(uuid4())
            response = httpx.delete(f"{BASE_URL}/tenants/{tenant_id}", timeout=5)
            
            # Should return 401 for unauthenticated request or 404 if not available
            assert response.status_code in [401, 404]
            data = response.json()
            assert "error" in data or "detail" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test tenant delete")

    def test_tenant_api_error_format_consistency(self):
        """Test that tenant API errors have consistent format"""
        try:
            test_cases = [
                (f"{BASE_URL}/tenants", "get", {}, {}),
                (f"{BASE_URL}/tenants/{uuid4()}", "get", {}, {}),
                (f"{BASE_URL}/tenants/", "post", {}, {"name": "test"}),
                (f"{BASE_URL}/tenants/{uuid4()}", "patch", {}, {"name": "test"}),
                (f"{BASE_URL}/tenants/{uuid4()}", "delete", {}, {}),
            ]
            
            for url, method, headers, json_data in test_cases:
                if method == "get":
                    response = httpx.get(url, headers=headers, timeout=5)
                elif method == "post":
                    response = httpx.post(url, headers=headers, json=json_data, timeout=5)
                elif method == "patch":
                    response = httpx.patch(url, headers=headers, json=json_data, timeout=5)
                elif method == "delete":
                    response = httpx.delete(url, headers=headers, timeout=5)
                
                # All should return error responses (401 for auth, 422 for validation)
                assert response.status_code in [401, 422, 404]
                
                data = response.json()
                # Should have some error indicator
                assert "error" in data or "detail" in data, f"No error field in response from {url}"
                
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test error response format")


@pytest.mark.integration
class TestTenantAuthenticatedFlow:
    """Test tenant operations with authentication (if test user available)"""
    
    async def get_auth_token(self):
        """Helper to get authentication token"""
        try:
            login_data = {
                "email": "test@example.com",
                "password": "password123",
                "tenant_code": "TEST"
            }
            
            response = httpx.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
            if response.status_code == 200:
                return response.json().get("access_token")
            return None
        except:
            return None
    
    def test_authenticated_tenant_list(self):
        """Test listing tenants with authentication"""
        try:
            # Try to get auth token
            login_data = {
                "email": "test@example.com", 
                "password": "password123",
                "tenant_code": "TEST"
            }
            
            auth_response = httpx.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
            if auth_response.status_code != 200:
                pytest.skip("Test user not available for authenticated tenant tests")
            
            token = auth_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test authenticated tenant list
            response = httpx.get(f"{BASE_URL}/tenants", headers=headers, timeout=5)
            
            # Should succeed with authentication (or return 403 if no permissions)
            assert response.status_code in [200, 403]
            
            if response.status_code == 200:
                data = response.json()
                # Should be a list or paginated response
                assert isinstance(data, (list, dict))
                
                if isinstance(data, dict):
                    # Paginated response
                    assert "items" in data or "data" in data or "tenants" in data
                
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test authenticated tenant operations")

    def test_authenticated_tenant_create_flow(self):
        """Test creating tenant with authentication"""
        try:
            # Get auth token
            login_data = {
                "email": "test@example.com",
                "password": "password123", 
                "tenant_code": "TEST"
            }
            
            auth_response = httpx.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
            if auth_response.status_code != 200:
                pytest.skip("Test user not available for authenticated tenant tests")
                
            token = auth_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test creating a new tenant
            unique_id = uuid4().hex[:8]
            tenant_data = {
                "name": f"Integration Test Tenant {unique_id}",
                "code": f"INT{unique_id.upper()}",
                "type": "child",  # Use child instead of root to avoid conflicts
                "isolation_mode": "shared",
                "settings": {
                    "test_tenant": True,
                    "created_by": "integration_test"
                },
                "features": ["basic"],
                "metadata": {
                    "source": "integration_test",
                    "test_id": unique_id
                }
            }
            
            response = httpx.post(f"{BASE_URL}/tenants/", json=tenant_data, headers=headers, timeout=5)
            
            # Could succeed (201), fail due to permissions (403), or validation (422)
            assert response.status_code in [201, 403, 422]
            
            if response.status_code == 201:
                # Tenant created successfully
                data = response.json()
                assert "id" in data
                assert data["name"] == tenant_data["name"]
                assert data["code"] == tenant_data["code"]
                
                # Try to get the created tenant
                tenant_id = data["id"]
                get_response = httpx.get(f"{BASE_URL}/tenants/{tenant_id}", headers=headers, timeout=5)
                assert get_response.status_code in [200, 403, 404]
                
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test authenticated tenant creation")


@pytest.mark.integration
class TestTenantPerformance:
    """Basic performance tests for tenant endpoints"""
    
    def test_tenant_list_performance(self):
        """Test tenant list endpoint response time"""
        try:
            import time
            
            start_time = time.time()
            response = httpx.get(f"{BASE_URL}/tenants", timeout=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Should respond quickly even if returning 401
            assert response_time < 2.0  # Should respond within 2 seconds
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test performance")

    def test_concurrent_tenant_requests(self):
        """Test handling of concurrent tenant requests"""
        try:
            import threading
            
            results = []
            
            def make_request():
                try:
                    response = httpx.get(f"{BASE_URL}/tenants", timeout=5)
                    results.append(response.status_code)
                except Exception as e:
                    results.append(str(e))
            
            # Create 5 concurrent threads
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # All requests should get responses (even if 401)
            assert len(results) == 5
            # All should be valid HTTP status codes
            assert all(isinstance(status, int) and status >= 200 for status in results)
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test concurrent requests")