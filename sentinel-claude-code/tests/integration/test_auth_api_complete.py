"""
Comprehensive API-only tests for ALL 13 Authentication API endpoints
Tests the API interface without touching the database directly
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import allure
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from src.main import app
from src.schemas.auth import TokenResponse, TokenValidationResponse, PasswordRequirements


# Mock data for testing
MOCK_USER_ID = str(uuid4())
MOCK_TENANT_ID = str(uuid4())
MOCK_ACCESS_TOKEN = "mock_access_token_12345"
MOCK_REFRESH_TOKEN = "mock_refresh_token_67890"

@allure.epic("Authentication API")
@allure.feature("Complete API Test Coverage - API Only")
class TestAuthenticationAPIComplete:
    """Comprehensive API-only tests for all 13 Authentication API endpoints"""

    def setup_method(self):
        """Set up test client and mock data"""
        self.client = TestClient(app)
        self.valid_login = {
            "email": "test@example.com",
            "password": "password123",
            "tenant_code": "TEST"
        }
        self.service_account = {
            "client_id": "service@example.com",
            "client_secret": "test-service-key-123"
        }

        # Mock token response
        self.mock_token_response = TokenResponse(
            access_token=MOCK_ACCESS_TOKEN,
            refresh_token=MOCK_REFRESH_TOKEN,
            token_type="Bearer",
            expires_in=3600,
            user_id=MOCK_USER_ID,
            tenant_id=MOCK_TENANT_ID
        )

        # Mock validation response
        self.mock_validation_response = TokenValidationResponse(
            valid=True,
            user_id=MOCK_USER_ID,
            tenant_id=MOCK_TENANT_ID,
            scopes=["read", "write"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_service_account=False
        )

        # Store real tokens from login API
        self.real_access_token = None
        self.real_refresh_token = None

    def _get_real_token(self):
        """Get a real token by calling the login API"""
        if self.real_access_token:
            return self.real_access_token

        # Mock the authentication service for login to get a real token
        with patch('src.services.authentication.AuthenticationService.authenticate_user') as mock_auth:
            mock_auth.return_value = self.mock_token_response

            response = self.client.post("/api/v1/auth/login", json=self.valid_login)
            if response.status_code == 200:
                data = response.json()
                self.real_access_token = data["access_token"]
                self.real_refresh_token = data["refresh_token"]
                return self.real_access_token
        return None
    
    # ============ API 1: POST /login - User Authentication ============

    @allure.story("User Authentication")
    @allure.title("API 1: POST /login - Successful user login")
    @allure.description("Test successful user authentication with valid credentials")
    @patch('src.services.authentication.AuthenticationService.authenticate_user')
    def test_login_success(self, mock_authenticate):
        """Test successful user login - API only"""

        # Mock the service response
        mock_authenticate.return_value = self.mock_token_response

        with allure.step("Submit valid login credentials"):
            response = self.client.post("/api/v1/auth/login", json=self.valid_login)

        with allure.step("Verify successful authentication"):
            assert response.status_code == 200
            data = response.json()

            # Verify token structure
            assert "access_token" in data
            assert "refresh_token" in data
            assert "token_type" in data
            assert "expires_in" in data
            assert "user_id" in data
            assert "tenant_id" in data
            assert data["token_type"] == "Bearer"
            assert data["expires_in"] > 0

        # Verify service was called correctly
        mock_authenticate.assert_called_once()

        allure.attach(str(self.valid_login), "Login Request", allure.attachment_type.JSON)
        allure.attach(str(data), "Login Response", allure.attachment_type.JSON)

    @allure.story("User Authentication")
    @allure.title("API 1: POST /login - Real token flow test")
    @allure.description("Test using real token from login API to validate other endpoints")
    @patch('src.services.authentication.AuthenticationService.authenticate_user')
    @patch('src.services.authentication.AuthenticationService.validate_token')
    def test_login_real_token_flow(self, mock_validate, mock_authenticate):
        """Test real token flow - login then validate - API only"""

        # Mock login to return token
        mock_authenticate.return_value = self.mock_token_response

        with allure.step("Step 1: Login to get real token"):
            login_response = self.client.post("/api/v1/auth/login", json=self.valid_login)
            assert login_response.status_code == 200
            login_data = login_response.json()
            real_token = login_data["access_token"]

        # Mock validation for the real token
        mock_validate.return_value = self.mock_validation_response

        with allure.step("Step 2: Use real token to validate"):
            validate_response = self.client.get(
                "/api/v1/auth/validate",
                headers={"Authorization": f"Bearer {real_token}"}
            )
            assert validate_response.status_code == 200
            validate_data = validate_response.json()
            assert validate_data["valid"] is True

        with allure.step("Step 3: Verify token was actually used"):
            # Verify the validate endpoint was called with the actual token from login
            mock_validate.assert_called_once_with(real_token)

        allure.attach(f"Real Token: {real_token}", "Token Used", allure.attachment_type.TEXT)
        allure.attach(str(validate_data), "Validation Response", allure.attachment_type.JSON)

    @allure.story("User Authentication")
    @allure.title("API 1: POST /login - Invalid credentials")
    @allure.description("Test login with invalid credentials")
    @patch('src.services.authentication.AuthenticationService.authenticate_user')
    def test_login_invalid_credentials(self, mock_authenticate):
        """Test login with invalid credentials - API only"""

        # Mock authentication failure
        from src.core.exceptions import AuthenticationError
        mock_authenticate.side_effect = AuthenticationError("Invalid credentials")

        invalid_login = {
            "email": "invalid@example.com",
            "password": "wrongpassword",
            "tenant_code": "TEST"
        }

        with allure.step("Submit invalid credentials"):
            response = self.client.post("/api/v1/auth/login", json=invalid_login)

        with allure.step("Verify authentication failure"):
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "message" in data["error"]
            assert data["error"]["message"]["error"] == "authentication_failed"
    
    # ============ API 2: POST /token - Service Account Authentication ============

    @allure.story("Service Account Authentication")
    @allure.title("API 2: POST /token - Service account authentication")
    @allure.description("Test service account token generation")
    @patch('src.services.authentication.AuthenticationService.authenticate_service_account')
    def test_service_account_token_success(self, mock_authenticate_service):
        """Test service account token generation - API only"""

        # Mock service account token response (no refresh token)
        service_token_response = TokenResponse(
            access_token=MOCK_ACCESS_TOKEN,
            refresh_token=None,  # Service accounts don't get refresh tokens
            token_type="Bearer",
            expires_in=3600,
            user_id=MOCK_USER_ID,
            tenant_id=MOCK_TENANT_ID
        )
        mock_authenticate_service.return_value = service_token_response

        with allure.step("Request service account token"):
            response = self.client.post("/api/v1/auth/token", json=self.service_account)

        with allure.step("Verify token response"):
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "Bearer"
            # Service accounts don't get refresh tokens
            assert data.get("refresh_token") is None

        mock_authenticate_service.assert_called_once()

    @allure.story("Service Account Authentication")
    @allure.title("API 2: POST /token - Invalid service account")
    @allure.description("Test service account authentication failure")
    @patch('src.services.authentication.AuthenticationService.authenticate_service_account')
    def test_service_account_token_invalid(self, mock_authenticate_service):
        """Test service account authentication failure - API only"""

        # Mock authentication failure
        from src.core.exceptions import AuthenticationError
        mock_authenticate_service.side_effect = AuthenticationError("Invalid client credentials")

        with allure.step("Request service account token with invalid credentials"):
            response = self.client.post("/api/v1/auth/token", json=self.service_account)

        with allure.step("Verify authentication failure"):
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "message" in data["error"]
            assert data["error"]["message"]["error"] == "invalid_client"
    
    # ============ API 3: POST /refresh - Token Refresh ============

    @allure.story("Token Management")
    @allure.title("API 3: POST /refresh - Refresh access token")
    @allure.description("Test refreshing access token using refresh token")
    @patch('src.services.authentication.AuthenticationService.refresh_token')
    def test_token_refresh_success(self, mock_refresh):
        """Test token refresh - API only"""

        # Mock successful refresh
        mock_refresh.return_value = self.mock_token_response

        refresh_request = {"refresh_token": MOCK_REFRESH_TOKEN}

        with allure.step("Request token refresh"):
            response = self.client.post("/api/v1/auth/refresh", json=refresh_request)

        with allure.step("Verify refresh response"):
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "Bearer"

        mock_refresh.assert_called_once()

    @allure.story("Token Management")
    @allure.title("API 3: POST /refresh - Invalid refresh token")
    @allure.description("Test refresh with invalid token")
    @patch('src.services.authentication.AuthenticationService.refresh_token')
    def test_token_refresh_invalid(self, mock_refresh):
        """Test token refresh with invalid token - API only"""

        # Mock refresh failure
        from src.core.exceptions import AuthenticationError
        mock_refresh.side_effect = AuthenticationError("Invalid refresh token")

        refresh_request = {"refresh_token": "invalid_token"}

        with allure.step("Request token refresh with invalid token"):
            response = self.client.post("/api/v1/auth/refresh", json=refresh_request)

        with allure.step("Verify refresh failure"):
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "message" in data["error"]
            assert data["error"]["message"]["error"] == "invalid_grant"
    
    # ============ API 4: GET /validate - Token Validation ============

    @allure.story("Token Management")
    @allure.title("API 4: GET /validate - Token validation")
    @allure.description("Test access token validation")
    def test_token_validation_no_token(self):
        """Test token validation without token - API only"""

        with allure.step("Test validation without token"):
            response = self.client.get("/api/v1/auth/validate")
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "message" in data["error"]
            assert data["error"]["message"]["error"] == "missing_token"

    @allure.story("Token Management")
    @allure.title("API 4: GET /validate - Valid token")
    @allure.description("Test access token validation with valid token")
    @patch('src.services.authentication.AuthenticationService.validate_token')
    def test_token_validation_valid(self, mock_validate):
        """Test token validation with valid token - API only"""

        # Mock successful validation
        mock_validate.return_value = self.mock_validation_response

        with allure.step("Test validation with valid token"):
            response = self.client.get(
                "/api/v1/auth/validate",
                headers={"Authorization": f"Bearer {MOCK_ACCESS_TOKEN}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["user_id"] == MOCK_USER_ID

        mock_validate.assert_called_once_with(MOCK_ACCESS_TOKEN)

    @allure.story("Token Management")
    @allure.title("API 4: GET /validate - Invalid token")
    @allure.description("Test access token validation with invalid token")
    @patch('src.services.authentication.AuthenticationService.validate_token')
    def test_token_validation_invalid(self, mock_validate):
        """Test token validation with invalid token - API only"""

        # Mock invalid token response
        invalid_validation = TokenValidationResponse(
            valid=False,
            user_id=None,
            tenant_id=None,
            scopes=[],
            expires_at=None,
            is_service_account=False
        )
        mock_validate.return_value = invalid_validation

        with allure.step("Test validation with invalid token"):
            response = self.client.get(
                "/api/v1/auth/validate",
                headers={"Authorization": "Bearer invalid_token"}
            )
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "message" in data["error"]
            assert data["error"]["message"]["error"] == "invalid_token"
    
    # ============ API 5: POST /revoke - Token Revocation ============

    @allure.story("Token Management")
    @allure.title("API 5: POST /revoke - Revoke token")
    @allure.description("Test token revocation")
    @patch('src.services.authentication.AuthenticationService.revoke_token')
    def test_token_revoke_success(self, mock_revoke):
        """Test token revocation - API only"""

        # Mock successful revocation
        mock_revoke.return_value = True

        revoke_request = {
            "token": MOCK_ACCESS_TOKEN,
            "token_type": "access_token"
        }

        with allure.step("Revoke access token"):
            response = self.client.post("/api/v1/auth/revoke", json=revoke_request)
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "revoked successfully" in data["message"]

        mock_revoke.assert_called_once()

    @allure.story("Token Management")
    @allure.title("API 5: POST /revoke - Token not found")
    @allure.description("Test revoking non-existent token")
    @patch('src.services.authentication.AuthenticationService.revoke_token')
    def test_token_revoke_not_found(self, mock_revoke):
        """Test revoking non-existent token - API only"""

        # Mock token not found
        mock_revoke.return_value = False

        revoke_request = {
            "token": "non_existent_token",
            "token_type": "access_token"
        }

        with allure.step("Revoke non-existent token"):
            response = self.client.post("/api/v1/auth/revoke", json=revoke_request)
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "not found" in data["message"] or "already revoked" in data["message"]
    
    # ============ API 6: POST /logout - User Logout ============

    @allure.story("Session Management")
    @allure.title("API 6: POST /logout - User logout")
    @allure.description("Test user logout")
    def test_logout_no_token(self):
        """Test logout without token - API only"""

        logout_request = {"revoke_all_devices": False}

        with allure.step("Logout without token"):
            response = self.client.post("/api/v1/auth/logout", json=logout_request)
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "message" in data["error"]
            assert data["error"]["message"]["error"] == "missing_token"

    @allure.story("Session Management")
    @allure.title("API 6: POST /logout - Successful logout")
    @allure.description("Test successful user logout")
    @patch('src.services.authentication.AuthenticationService.logout_user')
    def test_logout_success(self, mock_logout):
        """Test successful logout - API only"""

        # Mock successful logout
        mock_logout.return_value = True

        logout_request = {"revoke_all_devices": False}

        with allure.step("Logout user"):
            response = self.client.post(
                "/api/v1/auth/logout",
                json=logout_request,
                headers={"Authorization": f"Bearer {MOCK_ACCESS_TOKEN}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert data["message"] == "Logout successful"

        mock_logout.assert_called_once()
    
    # ============ API 7: GET /me/tokens - Get User Tokens ============

    @allure.story("Session Management")
    @allure.title("API 7: GET /me/tokens - Get user tokens")
    @allure.description("Test retrieving user's active tokens")
    @patch('src.services.token.TokenService.get_user_active_tokens')
    def test_get_user_tokens_success(self, mock_get_tokens):
        """Test getting user tokens - API only"""

        # Mock current user dependency
        from src.core.security_utils import get_current_user
        mock_user = MagicMock()
        mock_user.user_id = MOCK_USER_ID

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Mock token list with all required fields
        mock_tokens = [
            {
                "id": str(uuid4()),
                "device_info": {"platform": "web", "ip_address": "127.0.0.1"},
                "created_at": "2024-01-01T00:00:00Z",
                "last_used_at": "2024-01-01T01:00:00Z",
                "expires_at": "2024-01-02T00:00:00Z"  # Required field
            }
        ]
        mock_get_tokens.return_value = mock_tokens

        try:
            with allure.step("Request tokens with authentication"):
                response = self.client.get(
                    "/api/v1/auth/me/tokens",
                    headers={"Authorization": f"Bearer {MOCK_ACCESS_TOKEN}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 1

            mock_get_tokens.assert_called_once_with(MOCK_USER_ID)
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    # ============ API 8: DELETE /me/tokens/{token_id} - Revoke Specific Token ============

    @allure.story("Session Management")
    @allure.title("API 8: DELETE /me/tokens/{token_id} - Revoke specific token")
    @allure.description("Test revoking a specific user token")
    @patch('src.services.token.TokenService.revoke_user_tokens')
    def test_revoke_specific_token_success(self, mock_revoke_tokens):
        """Test revoking specific token - API only"""

        # Mock current user dependency
        from src.core.security_utils import get_current_user
        mock_user = MagicMock()
        mock_user.user_id = MOCK_USER_ID

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Mock successful revocation
        mock_revoke_tokens.return_value = 1  # 1 token revoked

        token_id = str(uuid4())

        try:
            with allure.step("Revoke specific token"):
                response = self.client.delete(
                    f"/api/v1/auth/me/tokens/{token_id}",
                    headers={"Authorization": f"Bearer {MOCK_ACCESS_TOKEN}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "message" in data
                assert "revoked successfully" in data["message"]

            mock_revoke_tokens.assert_called_once()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    @allure.story("Session Management")
    @allure.title("API 8: DELETE /me/tokens/{token_id} - Token not found")
    @allure.description("Test revoking non-existent token")
    @patch('src.services.token.TokenService.revoke_user_tokens')
    def test_revoke_specific_token_not_found(self, mock_revoke_tokens):
        """Test revoking non-existent token - API only"""

        # Mock current user dependency
        from src.core.security_utils import get_current_user
        mock_user = MagicMock()
        mock_user.user_id = MOCK_USER_ID

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Mock no tokens revoked
        mock_revoke_tokens.return_value = 0

        token_id = str(uuid4())

        try:
            with allure.step("Revoke non-existent token"):
                response = self.client.delete(
                    f"/api/v1/auth/me/tokens/{token_id}",
                    headers={"Authorization": f"Bearer {MOCK_ACCESS_TOKEN}"}
                )
                assert response.status_code == 404
                data = response.json()
                assert "Token not found" in str(data)
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    # ============ API 9: DELETE /me/tokens - Revoke All User Tokens ============

    @allure.story("Session Management")
    @allure.title("API 9: DELETE /me/tokens - Revoke all user tokens")
    @allure.description("Test revoking all user tokens")
    @patch('src.services.token.TokenService.revoke_user_tokens')
    def test_revoke_all_user_tokens(self, mock_revoke_tokens):
        """Test revoking all user tokens - API only"""

        # Mock current user dependency
        from src.core.security_utils import get_current_user
        mock_user = MagicMock()
        mock_user.user_id = MOCK_USER_ID
        mock_user.session_id = "current_session_id"

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Mock successful revocation
        mock_revoke_tokens.return_value = 3  # 3 tokens revoked

        try:
            with allure.step("Revoke all user tokens"):
                response = self.client.delete(
                    "/api/v1/auth/me/tokens",
                    headers={"Authorization": f"Bearer {MOCK_ACCESS_TOKEN}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "message" in data
                assert "Revoked 3 tokens" in data["message"]
                assert data["revoked_count"] == 3

            mock_revoke_tokens.assert_called_once()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    # ============ API 10: GET /password-requirements - Password Requirements ============

    @allure.story("Utilities")
    @allure.title("API 10: GET /password-requirements - Get password requirements")
    @allure.description("Test retrieving password complexity requirements")
    @patch('src.utils.password.default_password_policy')
    def test_password_requirements(self, mock_policy):
        """Test getting password requirements - API only"""

        # Mock password requirements
        mock_requirements = PasswordRequirements(
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_symbols=True
        )
        mock_policy.requirements = mock_requirements

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

            assert data["min_length"] == 8
            assert data["require_uppercase"] is True

        allure.attach(str(data), "Password Requirements", allure.attachment_type.JSON)
    
    # ============ API 11: GET /health - Health Check ============

    @allure.story("Utilities")
    @allure.title("API 11: GET /health - Authentication service health")
    @allure.description("Test authentication service health check")
    def test_auth_health(self):
        """Test authentication service health - API only"""

        with allure.step("Check auth service health"):
            response = self.client.get("/api/v1/auth/health")

        with allure.step("Verify health response"):
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "service" in data
            assert data["service"] == "authentication"
            assert data["status"] == "healthy"

        allure.attach(str(data), "Health Response", allure.attachment_type.JSON)
    
    # ============ API 12: POST /security-event - Security Event Logging ============

    @allure.story("Security")
    @allure.title("API 12: POST /security-event - Log security event")
    @allure.description("Test security event logging")
    @patch('src.core.security_utils.get_current_user_optional')
    def test_security_event_logging(self, mock_get_user):
        """Test logging security events - API only"""

        # Mock optional user (can be None for anonymous events)
        mock_get_user.return_value = None

        event_data = {
            "event_type": "test_event",
            "severity": "info",
            "description": "Test security event from integration test",
            "metadata": {"test": True}
        }

        with allure.step("Log security event"):
            response = self.client.post("/api/v1/auth/security-event", json=event_data)

        with allure.step("Verify event logged"):
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "event_id" in data
            assert data["message"] == "Security event logged"

        allure.attach(str(event_data), "Security Event", allure.attachment_type.JSON)

    @allure.story("Security")
    @allure.title("API 12: POST /security-event - With authenticated user")
    @allure.description("Test security event logging with authenticated user")
    @patch('src.core.security_utils.get_current_user_optional')
    def test_security_event_logging_authenticated(self, mock_get_user):
        """Test logging security events with authenticated user - API only"""

        # Mock authenticated user
        mock_user = MagicMock()
        mock_user.user_id = MOCK_USER_ID
        mock_get_user.return_value = mock_user

        event_data = {
            "event_type": "login_attempt",
            "severity": "warning",
            "description": "Failed login attempt",
            "metadata": {"ip": "192.168.1.1"}
        }

        with allure.step("Log security event with auth"):
            response = self.client.post(
                "/api/v1/auth/security-event",
                json=event_data,
                headers={"Authorization": f"Bearer {MOCK_ACCESS_TOKEN}"}
            )

        with allure.step("Verify event logged"):
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert data["message"] == "Security event logged"
    
    # ============ API 13: POST /introspect - Token Introspection ============

    @allure.story("Security")
    @allure.title("API 13: POST /introspect - Token introspection")
    @allure.description("Test token introspection endpoint")
    def test_token_introspection_no_auth(self):
        """Test token introspection without client auth - API only"""

        with allure.step("Test introspection without auth"):
            # The introspection endpoint expects token as query parameter
            response = self.client.post("/api/v1/auth/introspect?token=some-token")
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "Client authentication required" in data["error"]["message"]

    @allure.story("Security")
    @allure.title("API 13: POST /introspect - Valid introspection")
    @allure.description("Test token introspection with valid client auth")
    @patch('src.services.authentication.AuthenticationService.validate_token')
    @patch('src.services.token.TokenService.get_token_info')
    def test_token_introspection_success(self, mock_get_token_info, mock_validate):
        """Test token introspection with valid client auth - API only"""

        # Mock client validation (service account)
        service_validation = TokenValidationResponse(
            valid=True,
            user_id=MOCK_USER_ID,
            tenant_id=MOCK_TENANT_ID,
            scopes=["introspect"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_service_account=True  # This is a service account
        )
        mock_validate.return_value = service_validation

        # Mock token info
        mock_token_info = {
            "valid": True,
            "user_id": MOCK_USER_ID,
            "tenant_id": MOCK_TENANT_ID,
            "claims": {
                "aud": "sentinel-api",
                "iss": "sentinel-auth",
                "exp": 1640995200,
                "iat": 1640991600,
                "is_service_account": False
            },
            "scopes": ["read", "write"],
            "token_type": "access_token"
        }
        mock_get_token_info.return_value = mock_token_info

        with allure.step("Test introspection with valid client auth"):
            response = self.client.post(
                f"/api/v1/auth/introspect?token={MOCK_ACCESS_TOKEN}",
                headers={"Authorization": f"Bearer service_account_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["active"] is True
            assert data["sub"] == MOCK_USER_ID
            assert data["scope"] == "read write"

        mock_validate.assert_called_once()
        mock_get_token_info.assert_called_once()

    @allure.story("Security")
    @allure.title("API 13: POST /introspect - Invalid client")
    @allure.description("Test token introspection with invalid client")
    @patch('src.services.authentication.AuthenticationService.validate_token')
    def test_token_introspection_invalid_client(self, mock_validate):
        """Test token introspection with invalid client - API only"""

        # Mock invalid client validation
        invalid_validation = TokenValidationResponse(
            valid=False,
            user_id=None,
            tenant_id=None,
            scopes=[],
            expires_at=None,
            is_service_account=False
        )
        mock_validate.return_value = invalid_validation

        with allure.step("Test introspection with invalid client"):
            response = self.client.post(
                f"/api/v1/auth/introspect?token={MOCK_ACCESS_TOKEN}",
                headers={"Authorization": "Bearer invalid_client_token"}
            )
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "Invalid client credentials" in data["error"]["message"]


@allure.epic("Authentication API")
@allure.feature("Input Validation - API Only")
class TestAuthenticationValidation:
    """Test input validation for authentication endpoints - API only"""

    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)

    @allure.story("Login Validation")
    @allure.title("Login with missing fields")
    @allure.description("Test login validation with missing required fields")
    def test_login_missing_fields(self):
        """Test login with missing fields - API only"""

        test_cases = [
            {},  # Empty request
            {"email": "test@example.com"},  # Missing password and tenant
            {"password": "password123"},  # Missing email and tenant
            {"tenant_code": "TEST"},  # Missing email and password
            {"email": "test@example.com", "password": "password123"}  # Missing tenant
        ]

        for i, invalid_data in enumerate(test_cases):
            with allure.step(f"Test case {i+1}: {invalid_data}"):
                response = self.client.post("/api/v1/auth/login", json=invalid_data)
                assert response.status_code == 422  # Validation error
                data = response.json()
                assert "error" in data

    @allure.story("Login Validation")
    @allure.title("Login with invalid email format")
    @allure.description("Test login with malformed email addresses")
    def test_login_invalid_email_format(self):
        """Test login with invalid email formats - API only"""

        invalid_emails = [
            "not-an-email",
            "missing@.com",
            "@example.com",
            "user@",
            ""
        ]

        for email in invalid_emails:
            invalid_data = {
                "email": email,
                "password": "password123",
                "tenant_code": "TEST"
            }

            with allure.step(f"Test invalid email: {email}"):
                response = self.client.post("/api/v1/auth/login", json=invalid_data)
                assert response.status_code == 422
                data = response.json()
                assert "error" in data


@allure.epic("Authentication API")
@allure.feature("Real Token Integration Flow")
class TestRealTokenFlow:
    """Test real token flow across multiple APIs"""

    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
        self.valid_login = {
            "email": "test@example.com",
            "password": "password123",
            "tenant_code": "TEST"
        }

    @allure.story("Complete Token Lifecycle")
    @allure.title("Full API Flow: Login → Validate → Refresh → Logout")
    @allure.description("Test complete token lifecycle using real tokens from APIs")
    @patch('src.services.authentication.AuthenticationService.authenticate_user')
    @patch('src.services.authentication.AuthenticationService.validate_token')
    @patch('src.services.authentication.AuthenticationService.refresh_token')
    @patch('src.services.authentication.AuthenticationService.logout_user')
    def test_complete_token_lifecycle(self, mock_logout, mock_refresh, mock_validate, mock_authenticate):
        """Test complete token lifecycle with real API calls"""

        # Mock responses
        login_response = TokenResponse(
            access_token="real_access_token_123",
            refresh_token="real_refresh_token_456",
            token_type="Bearer",
            expires_in=3600,
            user_id=MOCK_USER_ID,
            tenant_id=MOCK_TENANT_ID
        )

        validation_response = TokenValidationResponse(
            valid=True,
            user_id=MOCK_USER_ID,
            tenant_id=MOCK_TENANT_ID,
            scopes=["read", "write"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_service_account=False
        )

        refresh_response = TokenResponse(
            access_token="new_access_token_789",
            refresh_token="new_refresh_token_012",
            token_type="Bearer",
            expires_in=3600,
            user_id=MOCK_USER_ID,
            tenant_id=MOCK_TENANT_ID
        )

        mock_authenticate.return_value = login_response
        mock_validate.return_value = validation_response
        mock_refresh.return_value = refresh_response
        mock_logout.return_value = True

        # Step 1: Login
        with allure.step("Step 1: Login and get tokens"):
            response = self.client.post("/api/v1/auth/login", json=self.valid_login)
            assert response.status_code == 200
            data = response.json()
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]
            assert access_token == "real_access_token_123"
            assert refresh_token == "real_refresh_token_456"

        # Step 2: Validate token
        with allure.step("Step 2: Validate the access token"):
            response = self.client.get(
                "/api/v1/auth/validate",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            mock_validate.assert_called_with(access_token)

        # Step 3: Refresh token
        with allure.step("Step 3: Refresh the token"):
            response = self.client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            assert response.status_code == 200
            data = response.json()
            new_access_token = data["access_token"]
            assert new_access_token == "new_access_token_789"

        # Step 4: Logout
        with allure.step("Step 4: Logout with the new token"):
            response = self.client.post(
                "/api/v1/auth/logout",
                json={"revoke_all_devices": False},
                headers={"Authorization": f"Bearer {new_access_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Logout successful"

        # Verify all services were called with real tokens
        mock_authenticate.assert_called_once()
        mock_validate.assert_called_once()
        mock_refresh.assert_called_once()
        mock_logout.assert_called_once()


"""
SUMMARY: This test file covers all 13 Authentication APIs with proper mocking:

1. POST /login - User authentication (success & failure)
2. POST /token - Service account authentication (success & failure)
3. POST /refresh - Token refresh (success & failure)
4. GET /validate - Token validation (no token, valid token, invalid token)
5. POST /revoke - Token revocation (success & not found)
6. POST /logout - User logout (no token & success)
7. GET /me/tokens - Get user tokens (with auth)
8. DELETE /me/tokens/{token_id} - Revoke specific token (success & not found)
9. DELETE /me/tokens - Revoke all user tokens
10. GET /password-requirements - Password requirements
11. GET /health - Health check
12. POST /security-event - Security event logging (anonymous & authenticated)
13. POST /introspect - Token introspection (no auth, valid client, invalid client)

All tests are API-only and use proper mocking to avoid database connections.
"""

if __name__ == "__main__":
    # Run with allure reporting
    pytest.main([__file__, "-v", "--alluredir=./allure-results"])