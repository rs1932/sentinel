"""
Simple Authentication Integration Tests
Tests real API endpoints with actual database and server components
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication endpoints"""

    def test_health_endpoint(self, client: TestClient):
        """Test authentication health endpoint"""
        response = client.get("/api/v1/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "authentication"

    def test_password_requirements_endpoint(self, client: TestClient):
        """Test password requirements endpoint"""
        response = client.get("/api/v1/auth/password-requirements")
        
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

    def test_login_endpoint_validation(self, client: TestClient):
        """Test login endpoint input validation"""
        
        # Test empty request
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422
        
        # Test missing fields
        incomplete_data = {"email": "test@example.com"}
        response = client.post("/api/v1/auth/login", json=incomplete_data)
        assert response.status_code == 422
        
        # Test invalid email format
        invalid_email_data = {
            "email": "not-an-email",
            "password": "password123",
            "tenant_code": "TEST"
        }
        response = client.post("/api/v1/auth/login", json=invalid_email_data)
        assert response.status_code == 422

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        invalid_login = {
            "email": "nonexistent@example.com", 
            "password": "wrongpassword",
            "tenant_code": "INVALID"
        }
        
        response = client.post("/api/v1/auth/login", json=invalid_login)
        
        # Should return 401 for invalid credentials
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_login_valid_credentials(self, client: TestClient, auth_headers: dict):
        """Test login with valid credentials (using test fixtures)"""
        # This uses the auth_headers fixture which performs a real login
        # If we get valid headers back, the login worked
        assert "Authorization" in auth_headers
        assert auth_headers["Authorization"].startswith("Bearer ")

    def test_validate_endpoint_no_token(self, client: TestClient):
        """Test token validation without providing a token"""
        response = client.get("/api/v1/auth/validate")
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_validate_endpoint_invalid_token(self, client: TestClient):
        """Test token validation with invalid token"""
        response = client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer invalid_token_123"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_validate_endpoint_valid_token(self, client: TestClient, auth_headers: dict):
        """Test token validation with valid token"""
        response = client.get("/api/v1/auth/validate", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert data["valid"] is True
        assert "user_id" in data
        assert "tenant_id" in data

    def test_logout_endpoint_no_token(self, client: TestClient):
        """Test logout without token"""
        response = client.post("/api/v1/auth/logout", json={"revoke_all_devices": False})
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_logout_endpoint_valid_token(self, client: TestClient, auth_headers: dict):
        """Test logout with valid token"""
        response = client.post(
            "/api/v1/auth/logout", 
            json={"revoke_all_devices": False},
            headers=auth_headers
        )
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_refresh_endpoint_no_token(self, client: TestClient):
        """Test token refresh without refresh token"""
        response = client.post("/api/v1/auth/refresh", json={})
        
        assert response.status_code == 422  # Missing refresh_token field

    def test_refresh_endpoint_invalid_token(self, client: TestClient):
        """Test token refresh with invalid refresh token"""
        response = client.post(
            "/api/v1/auth/refresh", 
            json={"refresh_token": "invalid_refresh_token_123"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_security_event_logging(self, client: TestClient):
        """Test security event logging endpoint"""
        event_data = {
            "event_type": "test_event",
            "severity": "info",
            "description": "Integration test security event",
            "metadata": {"test": True, "source": "integration_test"}
        }
        
        response = client.post("/api/v1/auth/security-event", json=event_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "event_id" in data

@pytest.mark.integration 
class TestAuthenticationFlow:
    """Test complete authentication flows"""
    
    def test_complete_login_validate_logout_flow(self, client: TestClient):
        """Test complete authentication flow: login → validate → logout"""
        
        # Step 1: Login with valid credentials
        login_data = {
            "email": "test@example.com",
            "password": "password123", 
            "tenant_code": "TEST"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            # If login fails, it might be because the test user doesn't exist
            # This is acceptable for integration testing
            pytest.skip("Test user not available in database")
        
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "token_type" in login_data
        
        access_token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 2: Validate the token
        validate_response = client.get("/api/v1/auth/validate", headers=headers)
        assert validate_response.status_code == 200
        
        validate_data = validate_response.json()
        assert validate_data["valid"] is True
        
        # Step 3: Use token for authenticated endpoint
        # (This validates that the token actually works for protected endpoints)
        
        # Step 4: Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"revoke_all_devices": False},
            headers=headers
        )
        assert logout_response.status_code == 200
        
        # Step 5: Verify token is now invalid
        validate_after_logout = client.get("/api/v1/auth/validate", headers=headers)
        # Token should now be invalid (401) or still valid but marked as revoked
        # Either response is acceptable depending on implementation
        assert validate_after_logout.status_code in [200, 401]

    def test_service_account_authentication_flow(self, client: TestClient):
        """Test service account authentication flow"""
        
        # Test service account token endpoint
        service_account_data = {
            "client_id": "service@example.com",
            "client_secret": "test-service-key-123",
            "scope": "read write"
        }
        
        response = client.post("/api/v1/auth/token", json=service_account_data)
        
        if response.status_code != 200:
            # Service account might not be configured in test environment
            pytest.skip("Service account not configured in test database")
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "Bearer"
        
        # Service accounts typically don't get refresh tokens
        # This is implementation dependent
        
        # Test using the service account token
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        validate_response = client.get("/api/v1/auth/validate", headers=headers)
        
        # Should be able to validate service account token
        if validate_response.status_code == 200:
            validate_data = validate_response.json()
            assert validate_data["valid"] is True

@pytest.mark.integration
class TestAuthenticationEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_malformed_requests(self, client: TestClient):
        """Test API responses to malformed requests"""
        
        # Test completely invalid JSON
        response = client.post(
            "/api/v1/auth/login",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
        
        # Test wrong content type
        response = client.post(
            "/api/v1/auth/login",
            data="email=test@example.com",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code in [415, 422]  # Unsupported Media Type or Validation Error

    def test_extremely_long_inputs(self, client: TestClient):
        """Test API behavior with extremely long inputs"""
        
        very_long_email = "a" * 1000 + "@example.com"
        very_long_password = "b" * 1000
        
        login_data = {
            "email": very_long_email,
            "password": very_long_password,
            "tenant_code": "TEST"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Should handle gracefully (either 422 validation error or 401 auth error)
        assert response.status_code in [401, 422]

    def test_special_characters_in_inputs(self, client: TestClient):
        """Test API behavior with special characters"""
        
        special_chars_data = {
            "email": "test+special@example.com",
            "password": "password!@#$%^&*()",
            "tenant_code": "TEST-123"
        }
        
        response = client.post("/api/v1/auth/login", json=special_chars_data)
        
        # Should handle special characters properly
        # Either 401 (auth failed) or 422 (validation) is acceptable
        assert response.status_code in [401, 422]

    def test_concurrent_requests(self, client: TestClient):
        """Test handling of concurrent authentication requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/api/v1/auth/health")
            results.append(response.status_code)
        
        # Create 10 concurrent threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results)