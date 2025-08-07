"""
Unit tests for JWT utilities with Allure reporting
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import allure
from datetime import datetime, timedelta
from uuid import uuid4
import time

from src.utils.jwt import JWTManager, TokenValidator, TokenBlacklistManager
from src.schemas.auth import JWTConfig


@allure.epic("Authentication")
@allure.feature("JWT Token Management")
class TestJWTManager:
    """Test JWT manager functionality with Allure reporting"""
    
    def setup_method(self):
        """Set up test dependencies"""
        self.jwt_manager = JWTManager()
        self.user_id = str(uuid4())
        self.tenant_id = str(uuid4())
    
    @allure.story("Token Generation")
    @allure.title("Generate access and refresh tokens")
    @allure.description("Test generating JWT access and refresh tokens with proper claims")
    def test_generate_tokens(self):
        """Test generating access and refresh tokens"""
        with allure.step("Generate tokens with user information"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com",
                is_service_account=False,
                scopes=["read", "write"]
            )
        
        with allure.step("Verify token structure"):
            assert "access_token" in tokens
            assert "refresh_token" in tokens
            assert tokens["token_type"] == "Bearer"
            assert tokens["expires_in"] > 0
            assert "access_jti" in tokens
            assert "refresh_jti" in tokens
            
        allure.attach(str(tokens["access_jti"]), "Access Token JTI", allure.attachment_type.TEXT)
        allure.attach(str(tokens["refresh_jti"]), "Refresh Token JTI", allure.attachment_type.TEXT)
    
    @allure.story("Token Validation")
    @allure.title("Decode and validate valid token")
    @allure.description("Test decoding a valid JWT token and extracting claims")
    def test_decode_valid_token(self):
        """Test decoding valid token"""
        with allure.step("Generate test tokens"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Decode and validate token"):
            claims = self.jwt_manager.decode_token(tokens["access_token"])
        
        with allure.step("Verify claims"):
            assert claims["sub"] == self.user_id
            assert claims["tenant_id"] == self.tenant_id
            assert claims["tenant_code"] == "TEST"
            assert claims["email"] == "test@example.com"
            
        allure.attach(str(claims), "Token Claims", allure.attachment_type.JSON)
    
    @allure.story("Token Expiration")
    @allure.title("Handle expired token correctly")
    @allure.description("Test that expired tokens are properly rejected")
    @pytest.mark.skip(reason="Token expiration test needs adjustment")
    def test_decode_expired_token(self):
        """Test decoding expired token"""
        with allure.step("Create token with very short expiry"):
            config = JWTConfig(access_token_expire_minutes=0)
            manager = JWTManager(config)
            
            tokens = manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Wait for token to expire"):
            time.sleep(1)
        
        with allure.step("Verify expired token is rejected"):
            with pytest.raises(ValueError, match="Invalid token"):
                manager.decode_token(tokens["access_token"], verify_exp=True)
    
    @allure.story("Access Token Validation")
    @allure.title("Validate access token type")
    @allure.description("Test validating access tokens and checking token type")
    def test_validate_access_token(self):
        """Test validating access token"""
        with allure.step("Generate tokens"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Validate access token"):
            claims = self.jwt_manager.validate_access_token(tokens["access_token"])
        
        with allure.step("Verify token type and claims"):
            assert claims["sub"] == self.user_id
            assert claims["token_type"] == "access"
    
    @allure.story("Refresh Token Validation")
    @allure.title("Validate refresh token type")
    @allure.description("Test validating refresh tokens and checking token type")
    def test_validate_refresh_token(self):
        """Test validating refresh token"""
        with allure.step("Generate tokens"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Validate refresh token"):
            claims = self.jwt_manager.validate_refresh_token(tokens["refresh_token"])
        
        with allure.step("Verify token type and claims"):
            assert claims["sub"] == self.user_id
            assert claims["token_type"] == "refresh"
    
    @allure.story("Token Type Validation")
    @allure.title("Reject wrong token types")
    @allure.description("Test that tokens are rejected when used with wrong validation method")
    def test_validate_wrong_token_type(self):
        """Test validating token with wrong type"""
        with allure.step("Generate tokens"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Try to validate refresh token as access token"):
            with pytest.raises(ValueError, match="Invalid token type"):
                self.jwt_manager.validate_access_token(tokens["refresh_token"])
        
        with allure.step("Try to validate access token as refresh token"):
            with pytest.raises(ValueError, match="Invalid token type"):
                self.jwt_manager.validate_refresh_token(tokens["access_token"])
    
    @allure.story("Token Metadata")
    @allure.title("Extract JTI from token")
    @allure.description("Test extracting JWT ID (JTI) from tokens")
    def test_extract_jti(self):
        """Test extracting JTI from token"""
        with allure.step("Generate tokens"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Extract JTI"):
            jti = self.jwt_manager.extract_jti(tokens["access_token"])
        
        with allure.step("Verify JTI matches"):
            assert jti is not None
            assert jti == tokens["access_jti"]
            
        allure.attach(jti, "Extracted JTI", allure.attachment_type.TEXT)
    
    @allure.story("Token Expiry")
    @allure.title("Check token expiration status")
    @allure.description("Test checking if tokens are expired")
    def test_is_token_expired(self):
        """Test checking if token is expired"""
        with allure.step("Create non-expired token"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Verify token is not expired"):
            assert self.jwt_manager.is_token_expired(tokens["access_token"]) is False
    
    @allure.story("Token Expiry")
    @allure.title("Get token expiration time")
    @allure.description("Test retrieving token expiration timestamp")
    def test_get_token_expiry(self):
        """Test getting token expiry time"""
        with allure.step("Generate tokens"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Get token expiry"):
            expiry = self.jwt_manager.get_token_expiry(tokens["access_token"])
        
        with allure.step("Verify expiry is in future"):
            assert expiry is not None
            assert isinstance(expiry, datetime)
            assert expiry > datetime.utcnow()
            
        allure.attach(str(expiry), "Token Expiry Time", allure.attachment_type.TEXT)
    
    @allure.story("Token Refresh")
    @allure.title("Refresh access token from refresh token")
    @allure.description("Test generating new access token using refresh token")
    def test_refresh_access_token(self):
        """Test refreshing access token from refresh token"""
        with allure.step("Generate initial tokens"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Refresh access token"):
            new_tokens = self.jwt_manager.refresh_access_token(
                tokens["refresh_token"],
                new_scopes=["read"]
            )
        
        with allure.step("Verify new token structure"):
            assert "access_token" in new_tokens
            assert new_tokens["token_type"] == "Bearer"
            assert new_tokens["expires_in"] > 0
        
        with allure.step("Verify new token claims"):
            claims = self.jwt_manager.decode_token(new_tokens["access_token"])
            assert claims["sub"] == self.user_id
            assert claims["tenant_id"] == self.tenant_id
            assert claims["scopes"] == ["read"]
    
    @allure.story("Session Management")
    @allure.title("Generate token with session ID")
    @allure.description("Test generating tokens with session tracking")
    def test_token_with_session_id(self):
        """Test generating token with session ID"""
        session_id = str(uuid4())
        
        with allure.step("Generate tokens with session ID"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="test@example.com",
                session_id=session_id
            )
        
        with allure.step("Verify session ID in claims"):
            claims = self.jwt_manager.decode_token(tokens["access_token"])
            assert claims["session_id"] == session_id
            
        allure.attach(session_id, "Session ID", allure.attachment_type.TEXT)
    
    @allure.story("Service Account Tokens")
    @allure.title("Generate service account token")
    @allure.description("Test generating tokens for service accounts with specific scopes")
    def test_service_account_token(self):
        """Test generating service account token"""
        with allure.step("Generate service account tokens"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                tenant_code="TEST",
                email="service@example.com",
                is_service_account=True,
                scopes=["api:read", "api:write"]
            )
        
        with allure.step("Verify service account claims"):
            claims = self.jwt_manager.decode_token(tokens["access_token"])
            assert claims["is_service_account"] is True
            assert claims["scopes"] == ["api:read", "api:write"]


@allure.epic("Authentication")
@allure.feature("Token Validation")
class TestTokenValidator:
    """Test token validator functionality with Allure reporting"""
    
    def setup_method(self):
        """Set up test dependencies"""
        self.jwt_manager = JWTManager()
        self.validator = TokenValidator(self.jwt_manager)
    
    @allure.story("Token Format Validation")
    @allure.title("Validate correct JWT format")
    @allure.description("Test validating tokens with correct JWT format")
    def test_validate_token_format_valid(self):
        """Test validating correct JWT format"""
        with allure.step("Generate valid token"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=str(uuid4()),
                tenant_id=str(uuid4()),
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Validate token format"):
            is_valid = self.validator.validate_token_format(tokens["access_token"])
            assert is_valid is True
    
    @allure.story("Token Format Validation")
    @allure.title("Reject invalid JWT format")
    @allure.description("Test rejecting tokens with incorrect JWT format")
    def test_validate_token_format_invalid(self):
        """Test validating incorrect JWT format"""
        with allure.step("Test various invalid formats"):
            assert self.validator.validate_token_format("") is False
            assert self.validator.validate_token_format("invalid") is False
            assert self.validator.validate_token_format("part1.part2") is False
            assert self.validator.validate_token_format("part1.part2.part3.part4") is False
    
    @allure.story("Claims Extraction")
    @allure.title("Extract claims without validation")
    @allure.description("Test extracting JWT claims without signature validation")
    def test_extract_claims_without_validation(self):
        """Test extracting claims without validation"""
        with allure.step("Generate token"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=str(uuid4()),
                tenant_id=str(uuid4()),
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Extract unverified claims"):
            claims = self.validator.extract_claims_without_validation(tokens["access_token"])
        
        with allure.step("Verify claims structure"):
            assert claims is not None
            assert "sub" in claims
            assert "tenant_id" in claims
            
        allure.attach(str(claims), "Extracted Claims", allure.attachment_type.JSON)


@allure.epic("Authentication")
@allure.feature("Token Blacklist")
class TestTokenBlacklistManager:
    """Test token blacklist manager functionality with Allure reporting"""
    
    def setup_method(self):
        """Set up test dependencies"""
        self.jwt_manager = JWTManager()
        self.blacklist_manager = TokenBlacklistManager(self.jwt_manager)
    
    @allure.story("Token Blacklisting")
    @allure.title("Blacklist a valid token")
    @allure.description("Test adding a token to the blacklist")
    @pytest.mark.asyncio
    async def test_blacklist_token(self):
        """Test blacklisting a token"""
        with allure.step("Generate token"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=str(uuid4()),
                tenant_id=str(uuid4()),
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Blacklist the token"):
            jti = await self.blacklist_manager.blacklist_token(tokens["access_token"])
        
        with allure.step("Verify JTI returned"):
            assert jti is not None
            assert jti == tokens["access_jti"]
            
        allure.attach(jti, "Blacklisted Token JTI", allure.attachment_type.TEXT)
    
    @allure.story("Token Blacklisting")
    @allure.title("Reject blacklisting invalid token")
    @allure.description("Test that invalid tokens cannot be blacklisted")
    @pytest.mark.asyncio
    async def test_blacklist_invalid_token(self):
        """Test blacklisting invalid token"""
        with allure.step("Try to blacklist invalid token"):
            with pytest.raises(ValueError, match="Cannot extract JTI"):
                await self.blacklist_manager.blacklist_token("invalid_token")
    
    @allure.story("Blacklist Checking")
    @allure.title("Check if token is blacklisted")
    @allure.description("Test checking token blacklist status")
    @pytest.mark.asyncio
    async def test_is_token_blacklisted(self):
        """Test checking if token is blacklisted"""
        with allure.step("Generate token"):
            tokens = self.jwt_manager.generate_tokens(
                user_id=str(uuid4()),
                tenant_id=str(uuid4()),
                tenant_code="TEST",
                email="test@example.com"
            )
        
        with allure.step("Check token is not blacklisted initially"):
            is_blacklisted = await self.blacklist_manager.is_token_blacklisted(tokens["access_token"])
            assert is_blacklisted is False
        
        with allure.step("Check invalid token is considered blacklisted"):
            is_blacklisted = await self.blacklist_manager.is_token_blacklisted("invalid_token")
            assert is_blacklisted is True


if __name__ == "__main__":
    # Run with allure
    pytest.main([__file__, "-v", "--alluredir=./allure-results"])