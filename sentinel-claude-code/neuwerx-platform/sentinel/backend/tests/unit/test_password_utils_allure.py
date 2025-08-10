"""
Unit tests for password utilities with Allure reporting
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import allure
from src.utils.password import PasswordManager, PasswordPolicy, PasswordRequirements


@allure.epic("Authentication")
@allure.feature("Password Management")
class TestPasswordManager:
    """Test password manager functionality with Allure reporting"""
    
    def setup_method(self):
        """Set up test dependencies"""
        self.password_manager = PasswordManager()
    
    @allure.story("Password Hashing")
    @allure.title("Hash password with bcrypt")
    @allure.description("Test password hashing using bcrypt algorithm")
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        
        with allure.step("Hash the password"):
            hashed = self.password_manager.hash_password(password)
        
        with allure.step("Verify hash properties"):
            assert hashed is not None
            assert hashed != password
            assert len(hashed) > 50  # bcrypt hashes are long
            
        allure.attach(f"Original: {password}", "Password", allure.attachment_type.TEXT)
        allure.attach(f"Hash length: {len(hashed)}", "Hash Info", allure.attachment_type.TEXT)
    
    @allure.story("Password Verification")
    @allure.title("Verify correct password")
    @allure.description("Test verifying a correct password against its hash")
    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "TestPassword123!"
        
        with allure.step("Hash the password"):
            hashed = self.password_manager.hash_password(password)
        
        with allure.step("Verify correct password"):
            is_valid = self.password_manager.verify_password(password, hashed)
            assert is_valid is True
    
    @allure.story("Password Verification")
    @allure.title("Reject incorrect password")
    @allure.description("Test rejecting an incorrect password")
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        
        with allure.step("Hash the correct password"):
            hashed = self.password_manager.hash_password(password)
        
        with allure.step("Verify incorrect password is rejected"):
            is_valid = self.password_manager.verify_password(wrong_password, hashed)
            assert is_valid is False
    
    @allure.story("Password Verification")
    @allure.title("Handle empty passwords")
    @allure.description("Test handling empty password verification")
    def test_verify_password_empty(self):
        """Test verifying empty password"""
        with allure.step("Test empty password"):
            assert self.password_manager.verify_password("", "somehash") is False
        
        with allure.step("Test empty hash"):
            assert self.password_manager.verify_password("password", "") is False
    
    @allure.story("Password Generation")
    @allure.title("Generate secure password with default settings")
    @allure.description("Test generating a secure random password with all character types")
    def test_generate_password_default(self):
        """Test generating password with default settings"""
        with allure.step("Generate password"):
            password = self.password_manager.generate_password()
        
        with allure.step("Verify password meets requirements"):
            assert len(password) == 16
            assert any(c.isupper() for c in password), "Should contain uppercase"
            assert any(c.islower() for c in password), "Should contain lowercase"
            assert any(c.isdigit() for c in password), "Should contain digits"
            assert any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password), "Should contain symbols"
            
        allure.attach(password, "Generated Password", allure.attachment_type.TEXT)
    
    @allure.story("Password Generation")
    @allure.title("Generate password with custom length")
    @allure.description("Test generating password with specified length")
    def test_generate_password_custom_length(self):
        """Test generating password with custom length"""
        with allure.step("Generate 20-character password"):
            password = self.password_manager.generate_password(length=20)
        
        with allure.step("Verify length"):
            assert len(password) == 20
    
    @allure.story("Password Generation")
    @allure.title("Generate password without symbols")
    @allure.description("Test generating password without special characters")
    def test_generate_password_no_symbols(self):
        """Test generating password without symbols"""
        with allure.step("Generate password without symbols"):
            password = self.password_manager.generate_password(include_symbols=False)
        
        with allure.step("Verify no symbols present"):
            assert len(password) == 16
            assert not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    @allure.story("Password Generation")
    @allure.title("Reject password generation with invalid length")
    @allure.description("Test that password generation fails with length < 8")
    def test_generate_password_min_length(self):
        """Test password generation with minimum length"""
        with allure.step("Try to generate password with length < 8"):
            with pytest.raises(ValueError, match="at least 8 characters"):
                self.password_manager.generate_password(length=5)
    
    @allure.story("Password Strength Validation")
    @allure.title("Validate strong password")
    @allure.description("Test validating a password that meets all requirements")
    def test_validate_password_strength_strong(self):
        """Test validating strong password"""
        with allure.step("Validate strong password"):
            # Use a password without sequential numbers
            result = self.password_manager.validate_password_strength("MyStr0ng!PasswordZ#9")
        
        with allure.step("Verify validation result"):
            assert result["valid"] is True
            assert len(result["errors"]) == 0
            assert result["strength_score"] > 60
            
        allure.attach(str(result["strength_score"]), "Strength Score", allure.attachment_type.TEXT)
    
    @allure.story("Password Strength Validation")
    @allure.title("Reject weak password")
    @allure.description("Test rejecting a password that doesn't meet requirements")
    def test_validate_password_strength_weak(self):
        """Test validating weak password"""
        with allure.step("Validate weak password"):
            result = self.password_manager.validate_password_strength("weak")
        
        with allure.step("Verify validation failure"):
            assert result["valid"] is False
            assert len(result["errors"]) > 0
            assert "at least 8 characters" in result["errors"][0]
            
        allure.attach(str(result["errors"]), "Validation Errors", allure.attachment_type.TEXT)
    
    @allure.story("Password Requirements")
    @allure.title("Check missing uppercase requirement")
    @allure.description("Test that passwords without uppercase letters are rejected when required")
    def test_validate_password_missing_uppercase(self):
        """Test password missing uppercase letters"""
        requirements = PasswordRequirements(require_uppercase=True)
        
        with allure.step("Validate password without uppercase"):
            result = self.password_manager.validate_password_strength("password123!", requirements)
        
        with allure.step("Verify uppercase requirement failure"):
            assert result["valid"] is False
            assert any("uppercase" in error for error in result["errors"])
    
    @allure.story("Password Requirements")
    @allure.title("Check missing lowercase requirement")
    @allure.description("Test that passwords without lowercase letters are rejected when required")
    def test_validate_password_missing_lowercase(self):
        """Test password missing lowercase letters"""
        requirements = PasswordRequirements(require_lowercase=True)
        
        with allure.step("Validate password without lowercase"):
            result = self.password_manager.validate_password_strength("PASSWORD123!", requirements)
        
        with allure.step("Verify lowercase requirement failure"):
            assert result["valid"] is False
            assert any("lowercase" in error for error in result["errors"])
    
    @allure.story("Password Requirements")
    @allure.title("Check missing numbers requirement")
    @allure.description("Test that passwords without numbers are rejected when required")
    def test_validate_password_missing_numbers(self):
        """Test password missing numbers"""
        requirements = PasswordRequirements(require_numbers=True)
        
        with allure.step("Validate password without numbers"):
            result = self.password_manager.validate_password_strength("Password!", requirements)
        
        with allure.step("Verify number requirement failure"):
            assert result["valid"] is False
            assert any("number" in error for error in result["errors"])
    
    @allure.story("Password Requirements")
    @allure.title("Check missing symbols requirement")
    @allure.description("Test that passwords without symbols are rejected when required")
    def test_validate_password_missing_symbols(self):
        """Test password missing symbols"""
        requirements = PasswordRequirements(require_symbols=True)
        
        with allure.step("Validate password without symbols"):
            result = self.password_manager.validate_password_strength("Password123", requirements)
        
        with allure.step("Verify symbol requirement failure"):
            assert result["valid"] is False
            assert any("special character" in error for error in result["errors"])
    
    @allure.story("Password Patterns")
    @allure.title("Reject sequential numbers")
    @allure.description("Test that passwords with sequential numbers are rejected")
    def test_validate_password_sequential_numbers(self):
        """Test password with sequential numbers"""
        with allure.step("Validate password with '123'"):
            result = self.password_manager.validate_password_strength("Password123!")
        
        with allure.step("Verify sequential numbers detected"):
            assert result["valid"] is False
            assert any("sequential numbers" in error for error in result["errors"])
    
    @allure.story("Password Patterns")
    @allure.title("Reject repeated characters")
    @allure.description("Test that passwords with repeated characters are rejected")
    def test_validate_password_repeated_characters(self):
        """Test password with repeated characters"""
        with allure.step("Validate password with 'sss'"):
            result = self.password_manager.validate_password_strength("Passsword1!")
        
        with allure.step("Verify repeated characters detected"):
            assert result["valid"] is False
            assert any("consecutive identical" in error for error in result["errors"])
    
    @allure.story("Common Passwords")
    @allure.title("Detect common passwords")
    @allure.description("Test detection of commonly used passwords")
    def test_check_common_passwords(self):
        """Test checking common passwords"""
        with allure.step("Check known common passwords"):
            assert self.password_manager.check_common_passwords("password") is True
            assert self.password_manager.check_common_passwords("123456") is True
            assert self.password_manager.check_common_passwords("admin") is True
        
        with allure.step("Check unique password"):
            assert self.password_manager.check_common_passwords("MyUniquePassword123!") is False
    
    @allure.story("Password Improvements")
    @allure.title("Suggest password improvements")
    @allure.description("Test generating improvement suggestions for weak passwords")
    def test_suggest_improvements(self):
        """Test password improvement suggestions"""
        with allure.step("Get suggestions for weak password"):
            suggestions = self.password_manager.suggest_improvements("weak")
        
        with allure.step("Verify suggestions provided"):
            assert len(suggestions) > 0
            assert any("length" in s for s in suggestions)
            assert any("uppercase" in s for s in suggestions)
            
        allure.attach(str(suggestions), "Suggestions", allure.attachment_type.TEXT)


@allure.epic("Authentication")
@allure.feature("Password Policy")
class TestPasswordPolicy:
    """Test password policy enforcement with Allure reporting"""
    
    def setup_method(self):
        """Set up test dependencies"""
        self.policy = PasswordPolicy()
    
    @allure.story("Policy Enforcement")
    @allure.title("Enforce policy on valid password")
    @allure.description("Test that valid passwords pass policy enforcement")
    def test_enforce_policy_valid(self):
        """Test enforcing policy on valid password"""
        with allure.step("Enforce policy on valid password"):
            result = self.policy.enforce_policy("ValidP@ssw0rd")
        
        with allure.step("Verify password passes"):
            assert result["valid"] is True
    
    @allure.story("Policy Enforcement")
    @allure.title("Prevent password containing email")
    @allure.description("Test that passwords containing user email are rejected")
    def test_enforce_policy_with_user_email(self):
        """Test policy prevents password containing email"""
        user_info = {"email": "user@example.com"}
        
        with allure.step("Enforce policy with email check"):
            result = self.policy.enforce_policy("user123!", user_info)
        
        with allure.step("Verify email-based password rejected"):
            assert result["valid"] is False
            assert any("email" in error for error in result["errors"])
    
    @allure.story("Policy Enforcement")
    @allure.title("Prevent password containing name")
    @allure.description("Test that passwords containing user name are rejected")
    def test_enforce_policy_with_user_name(self):
        """Test policy prevents password containing name"""
        user_info = {"name": "John", "email": "john@example.com"}
        
        with allure.step("Enforce policy with name check"):
            result = self.policy.enforce_policy("John123!", user_info)
        
        with allure.step("Verify name-based password rejected"):
            assert result["valid"] is False
            assert any("name" in error for error in result["errors"])
    
    @allure.story("Policy Configuration")
    @allure.title("Get policy description")
    @allure.description("Test retrieving human-readable policy description")
    def test_get_policy_description(self):
        """Test getting policy description"""
        with allure.step("Get policy description"):
            description = self.policy.get_policy_description()
        
        with allure.step("Verify description structure"):
            assert description["min_length"] == 8
            assert description["require_uppercase"] is True
            assert description["require_lowercase"] is True
            assert description["require_numbers"] is True
            assert description["require_symbols"] is True
            assert "description" in description
            
        allure.attach(str(description), "Policy Description", allure.attachment_type.JSON)


if __name__ == "__main__":
    # Run with allure
    pytest.main([__file__, "-v", "--alluredir=./allure-results"])