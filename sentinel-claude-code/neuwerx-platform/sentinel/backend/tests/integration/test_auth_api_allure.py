"""
Integration tests for Authentication API with Allure reporting
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import allure
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.main import app
from src.schemas.auth import LoginRequest, TokenResponse


@allure.epic("Authentication API")
@allure.feature("REST API Endpoints")
class TestAuthenticationAPI:
    """Integration tests for Authentication API endpoints"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    @allure.story("Health Check")
    @allure.title("Authentication service health check")
    @allure.description("Test that auth service health endpoint responds correctly")
    def test_auth_health_check(self):
        """Test authentication service health endpoint"""
        
        with allure.step("Make health check request"):
            response = self.client.get("/api/v1/auth/health")
        
        with allure.step("Verify health response"):
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "service" in data
            assert data["service"] == "authentication"
        
        allure.attach(str(data), "Health Response", allure.attachment_type.JSON)
    
    @allure.story("Password Requirements")
    @allure.title("Get password complexity requirements")
    @allure.description("Test retrieving password requirements for client-side validation")
    def test_get_password_requirements(self):
        """Test getting password requirements"""
        
        with allure.step("Request password requirements"):
            response = self.client.get("/api/v1/auth/password-requirements")
        
        with allure.step("Verify requirements structure"):
            assert response.status_code == 200
            data = response.json()
            
            required_fields = [
                "min_length", "require_uppercase", "require_lowercase",
                "require_numbers", "require_symbols"
            ]
            for field in required_fields:
                assert field in data
        
        allure.attach(str(data), "Password Requirements", allure.attachment_type.JSON)
    
    @allure.story("User Authentication")
    @allure.title("Login with invalid credentials")
    @allure.description("Test that invalid login attempts are properly rejected")
    @patch('src.services.authentication.AuthenticationService.authenticate_user')
    def test_login_invalid_credentials(self, mock_auth):
        """Test login with invalid credentials"""
        
        # Mock authentication failure
        from src.core.exceptions import AuthenticationError
        mock_auth.side_effect = AuthenticationError("Invalid credentials")
        
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword",
            "tenant_code": "TEST"
        }
        
        with allure.step("Attempt login with invalid credentials"):
            response = self.client.post("/api/v1/auth/login", json=login_data)
        
        with allure.step("Verify authentication failure"):
            assert response.status_code == 401
            error_data = response.json()
            assert "error" in error_data
            assert error_data["error"] == "authentication_failed"
        
        allure.attach(str(login_data), "Login Attempt", allure.attachment_type.JSON)
        allure.attach(str(error_data), "Error Response", allure.attachment_type.JSON)
    
    @allure.story("User Authentication")
    @allure.title("Login with missing fields")
    @allure.description("Test validation of required login fields")
    def test_login_missing_fields(self):
        """Test login with missing required fields"""
        
        incomplete_data = {
            "email": "user@example.com"
            # Missing password and tenant_code
        }
        
        with allure.step("Attempt login with incomplete data"):
            response = self.client.post("/api/v1/auth/login", json=incomplete_data)
        
        with allure.step("Verify validation error"):
            assert response.status_code == 422  # Validation error
            error_data = response.json()
            assert "detail" in error_data
        
        allure.attach(str(incomplete_data), "Incomplete Login Data", allure.attachment_type.JSON)
    
    @allure.story("Token Validation")
    @allure.title("Validate token without authorization header")
    @allure.description("Test that token validation requires proper authorization")
    def test_validate_token_no_header(self):
        """Test token validation without authorization header"""
        
        with allure.step("Request token validation without auth header"):
            response = self.client.get("/api/v1/auth/validate")
        
        with allure.step("Verify unauthorized response"):
            assert response.status_code == 401
            error_data = response.json()
            assert "error" in error_data
            assert error_data["error"] == "missing_token"
        
        allure.attach(str(error_data), "Error Response", allure.attachment_type.JSON)
    
    @allure.story("Token Validation")
    @allure.title("Validate token with invalid format")
    @allure.description("Test validation of malformed JWT tokens")
    def test_validate_token_invalid_format(self):
        """Test token validation with invalid token format"""
        
        with allure.step("Request validation with invalid token"):
            response = self.client.get(
                "/api/v1/auth/validate",
                headers={"Authorization": "Bearer invalid-token-format"}
            )
        
        with allure.step("Verify token rejection"):
            assert response.status_code == 401
            error_data = response.json()
            assert "error" in error_data
            assert error_data["error"] == "invalid_token"
    
    @allure.story("Service Account Authentication")
    @allure.title("Service account token with missing credentials")
    @allure.description("Test service account authentication validation")
    def test_service_account_missing_credentials(self):
        """Test service account token with missing credentials"""
        
        incomplete_data = {
            "client_id": "test-service"
            # Missing client_secret
        }
        
        with allure.step("Request service account token"):
            response = self.client.post("/api/v1/auth/token", json=incomplete_data)
        
        with allure.step("Verify validation error"):
            assert response.status_code == 422  # Validation error
    
    @allure.story("Token Refresh")
    @allure.title("Refresh token with invalid token")
    @allure.description("Test token refresh with invalid refresh token")
    def test_refresh_invalid_token(self):
        """Test token refresh with invalid refresh token"""
        
        refresh_data = {
            "refresh_token": "invalid-refresh-token"
        }
        
        with allure.step("Attempt token refresh"):
            response = self.client.post("/api/v1/auth/refresh", json=refresh_data)
        
        with allure.step("Verify refresh failure"):
            assert response.status_code == 401
            error_data = response.json()
            assert "error" in error_data
            assert error_data["error"] == "invalid_grant"
    
    @allure.story("Token Revocation")
    @allure.title("Revoke token with invalid format")
    @allure.description("Test token revocation validation")
    def test_revoke_invalid_token_type(self):
        """Test token revocation with invalid token type"""
        
        revoke_data = {
            "token": "some-token",
            "token_type": "invalid_type"  # Should be 'access_token' or 'refresh_token'
        }
        
        with allure.step("Attempt token revocation"):
            response = self.client.post("/api/v1/auth/revoke", json=revoke_data)
        
        with allure.step("Verify validation error"):
            assert response.status_code == 422  # Validation error
    
    @allure.story("User Session Management")
    @allure.title("Get user tokens without authentication")
    @allure.description("Test that session management requires authentication")
    def test_get_user_tokens_unauthenticated(self):
        """Test getting user tokens without authentication"""
        
        with allure.step("Request user tokens without auth"):
            response = self.client.get("/api/v1/auth/me/tokens")
        
        with allure.step("Verify authentication required"):
            assert response.status_code == 401
    
    @allure.story("Security Events")
    @allure.title("Log security event")
    @allure.description("Test security event logging endpoint")
    def test_log_security_event(self):
        """Test logging security events"""
        
        event_data = {
            "event_type": "failed_login",
            "severity": "warning", 
            "description": "Failed login attempt from suspicious IP",
            "metadata": {
                "ip_address": "192.168.1.100",
                "user_agent": "test-client"
            }
        }
        
        with allure.step("Log security event"):
            response = self.client.post("/api/v1/auth/security-event", json=event_data)
        
        with allure.step("Verify event logged"):
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "event_id" in data
        
        allure.attach(str(event_data), "Security Event", allure.attachment_type.JSON)
    
    @allure.story("Token Introspection")
    @allure.title("Token introspection without client auth")
    @allure.description("Test that token introspection requires client authentication")
    def test_introspect_token_no_auth(self):
        """Test token introspection without client authentication"""
        
        introspect_data = {
            "token": "some-token-to-introspect"
        }
        
        with allure.step("Attempt token introspection"):
            response = self.client.post("/api/v1/auth/introspect", json=introspect_data)
        
        with allure.step("Verify client authentication required"):
            assert response.status_code == 401
            error_data = response.json()
            assert "Client authentication required" in error_data["detail"]


@allure.epic("Authentication API")
@allure.feature("API Schema Validation")
class TestAuthenticationSchemaValidation:
    """Test API schema validation for authentication endpoints"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    @allure.story("Input Validation")
    @allure.title("Login email validation")
    @allure.description("Test email format validation in login requests")
    def test_login_invalid_email_format(self):
        """Test login with invalid email format"""
        
        invalid_login_data = {
            "email": "not-an-email",
            "password": "password123",
            "tenant_code": "TEST"
        }
        
        with allure.step("Submit invalid email format"):
            response = self.client.post("/api/v1/auth/login", json=invalid_login_data)
        
        with allure.step("Verify email validation"):
            assert response.status_code == 422
            error_data = response.json()
            assert "detail" in error_data
        
        allure.attach(str(invalid_login_data), "Invalid Login Data", allure.attachment_type.JSON)
    
    @allure.story("Input Validation") 
    @allure.title("Tenant code format validation")
    @allure.description("Test tenant code format validation")
    def test_login_invalid_tenant_code(self):
        """Test login with invalid tenant code format"""
        
        invalid_login_data = {
            "email": "user@example.com",
            "password": "password123",
            "tenant_code": "invalid-tenant-code!"  # Contains invalid characters
        }
        
        with allure.step("Submit invalid tenant code"):
            response = self.client.post("/api/v1/auth/login", json=invalid_login_data)
        
        with allure.step("Verify tenant code validation"):
            assert response.status_code == 422
    
    @allure.story("Input Validation")
    @allure.title("Service account scope validation")
    @allure.description("Test scope format validation for service accounts")
    def test_service_account_invalid_scope(self):
        """Test service account with invalid scope format"""
        
        invalid_service_data = {
            "client_id": "test-service",
            "client_secret": "secret",
            "scope": "invalid scope format!"  # Contains invalid characters
        }
        
        with allure.step("Submit invalid scope format"):
            response = self.client.post("/api/v1/auth/token", json=invalid_service_data)
        
        with allure.step("Verify scope validation"):
            assert response.status_code == 422


if __name__ == "__main__":
    # Run with allure
    pytest.main([__file__, "-v", "--alluredir=./allure-results"])