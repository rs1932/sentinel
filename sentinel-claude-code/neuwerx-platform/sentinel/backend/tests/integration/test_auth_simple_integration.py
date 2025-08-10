"""
Simple Authentication Integration Tests
Tests against a running server without complex database fixtures
"""
import pytest
import httpx
from uuid import uuid4

# Server configuration
SERVER_URL = "http://localhost:8000"
BASE_URL = f"{SERVER_URL}/api/v1"

@pytest.mark.integration
class TestAuthenticationServerIntegration:
    """Integration tests that work with a running server"""
    
    def test_server_running(self):
        """Test that server is accessible"""
        try:
            response = httpx.get(f"{SERVER_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Server not running at http://localhost:8000")
        except httpx.ConnectError:
            pytest.skip("Server not running at http://localhost:8000")

    def test_auth_health_endpoint(self):
        """Test authentication health endpoint"""
        try:
            response = httpx.get(f"{BASE_URL}/auth/health", timeout=5)
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "service" in data
            assert data["service"] == "authentication"
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test auth health endpoint")

    def test_password_requirements_endpoint(self):
        """Test password requirements endpoint"""
        try:
            response = httpx.get(f"{BASE_URL}/auth/password-requirements", timeout=5)
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields exist
            required_fields = [
                "min_length", "require_uppercase", "require_lowercase",
                "require_numbers", "require_symbols"
            ]
            for field in required_fields:
                assert field in data
            
            # Basic validation
            assert isinstance(data["min_length"], int)
            assert data["min_length"] > 0
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test password requirements")

    def test_login_validation_errors(self):
        """Test login endpoint validation"""
        try:
            # Test empty request
            response = httpx.post(f"{BASE_URL}/auth/login", json={}, timeout=5)
            assert response.status_code == 422
            
            # Test missing fields
            incomplete_data = {"email": "test@example.com"}
            response = httpx.post(f"{BASE_URL}/auth/login", json=incomplete_data, timeout=5)
            assert response.status_code == 422
            
            # Test invalid email format
            invalid_email_data = {
                "email": "not-an-email",
                "password": "password123",
                "tenant_code": "TEST"
            }
            response = httpx.post(f"{BASE_URL}/auth/login", json=invalid_email_data, timeout=5)
            assert response.status_code == 422
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test login validation")

    def test_login_with_nonexistent_credentials(self):
        """Test login with credentials that definitely don't exist"""
        try:
            nonexistent_login = {
                "email": f"nonexistent-{uuid4().hex}@example.com",
                "password": f"wrongpassword-{uuid4().hex}",
                "tenant_code": f"NONEXISTENT-{uuid4().hex[:8].upper()}"
            }
            
            response = httpx.post(f"{BASE_URL}/auth/login", json=nonexistent_login, timeout=5)
            
            # Should return 401 for invalid credentials
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test login")

    def test_validate_token_no_token(self):
        """Test token validation without providing a token"""
        try:
            response = httpx.get(f"{BASE_URL}/auth/validate", timeout=5)
            
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test token validation")

    def test_validate_token_invalid_token(self):
        """Test token validation with invalid token"""
        try:
            response = httpx.get(
                f"{BASE_URL}/auth/validate",
                headers={"Authorization": f"Bearer invalid_token_{uuid4().hex}"},
                timeout=5
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test token validation")

    def test_logout_no_token(self):
        """Test logout without token"""
        try:
            response = httpx.post(
                f"{BASE_URL}/auth/logout", 
                json={"revoke_all_devices": False},
                timeout=5
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test logout")

    def test_refresh_token_validation(self):
        """Test token refresh endpoint validation"""
        try:
            # Test without refresh token
            response = httpx.post(f"{BASE_URL}/auth/refresh", json={}, timeout=5)
            assert response.status_code == 422  # Missing refresh_token field
            
            # Test with invalid refresh token
            response = httpx.post(
                f"{BASE_URL}/auth/refresh", 
                json={"refresh_token": f"invalid_refresh_{uuid4().hex}"},
                timeout=5
            )
            assert response.status_code == 401
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test token refresh")

    def test_security_event_logging(self):
        """Test security event logging endpoint"""
        try:
            event_data = {
                "event_type": "integration_test",
                "severity": "info", 
                "description": "Integration test security event",
                "metadata": {
                    "test": True,
                    "source": "integration_test",
                    "event_id": str(uuid4())
                }
            }
            
            response = httpx.post(
                f"{BASE_URL}/auth/security-event", 
                json=event_data,
                timeout=5
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "event_id" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test security event logging")

    def test_service_account_token_validation(self):
        """Test service account token endpoint validation"""
        try:
            # Test empty request
            response = httpx.post(f"{BASE_URL}/auth/token", json={}, timeout=5)
            assert response.status_code == 422
            
            # Test with invalid service account credentials
            invalid_service_account = {
                "client_id": f"invalid_service_{uuid4().hex}@example.com",
                "client_secret": f"invalid_secret_{uuid4().hex}",
                "scope": "read write"
            }
            
            response = httpx.post(
                f"{BASE_URL}/auth/token", 
                json=invalid_service_account,
                timeout=5
            )
            
            # Should return 401 for invalid service account
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test service account tokens")

    def test_api_error_response_format(self):
        """Test that API errors have consistent format"""
        try:
            # Make several different invalid requests and verify error format consistency
            test_cases = [
                (f"{BASE_URL}/auth/validate", "get", {}, {}),
                (f"{BASE_URL}/auth/login", "post", {}, {"email": "invalid"}),
                (f"{BASE_URL}/auth/refresh", "post", {}, {"refresh_token": "invalid"}),
                (f"{BASE_URL}/auth/logout", "post", {}, {"revoke_all_devices": False}),
            ]
            
            for url, method, headers, json_data in test_cases:
                if method == "get":
                    response = httpx.get(url, headers=headers, timeout=5)
                else:
                    response = httpx.post(url, headers=headers, json=json_data, timeout=5)
                
                # All should return error responses
                assert response.status_code in [401, 422]
                
                data = response.json()
                assert "error" in data, f"No error field in response from {url}"
                
                # Check that error has some meaningful content
                assert isinstance(data["error"], (dict, str, list))
                
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test error response format")

@pytest.mark.integration
class TestAuthenticationRealFlow:
    """Test real authentication flows if test users exist"""
    
    def test_real_authentication_flow(self):
        """Test authentication flow with real test user (if available)"""
        try:
            # Try to authenticate with test credentials
            login_data = {
                "email": "test@example.com",
                "password": "password123",
                "tenant_code": "TEST"
            }
            
            login_response = httpx.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
            
            if login_response.status_code != 200:
                pytest.skip("Test user not available - skipping real auth flow test")
            
            # If we get here, login succeeded
            login_data = login_response.json()
            assert "access_token" in login_data
            assert "token_type" in login_data
            
            access_token = login_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Test token validation
            validate_response = httpx.get(f"{BASE_URL}/auth/validate", headers=headers, timeout=5)
            assert validate_response.status_code == 200
            
            validate_data = validate_response.json()
            assert validate_data["valid"] is True
            assert "user_id" in validate_data
            assert "tenant_id" in validate_data
            
            # Test logout
            logout_response = httpx.post(
                f"{BASE_URL}/auth/logout",
                json={"revoke_all_devices": False},
                headers=headers,
                timeout=5
            )
            assert logout_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test real authentication flow")

@pytest.mark.integration  
class TestAuthenticationPerformance:
    """Basic performance tests for authentication endpoints"""
    
    def test_health_endpoint_performance(self):
        """Test health endpoint response time"""
        try:
            import time
            
            start_time = time.time()
            response = httpx.get(f"{BASE_URL}/auth/health", timeout=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # Should respond within 1 second
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test performance")

    def test_concurrent_health_requests(self):
        """Test handling of concurrent requests"""
        try:
            import threading
            import time
            
            results = []
            
            def make_request():
                try:
                    response = httpx.get(f"{BASE_URL}/auth/health", timeout=5)
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
            
            # All requests should succeed
            assert len(results) == 5
            assert all(status == 200 for status in results)
            
        except httpx.ConnectError:
            pytest.skip("Server not running - cannot test concurrent requests")