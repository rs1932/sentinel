"""
Password utilities for secure hashing, validation, and complexity checking
"""
import re
import secrets
import string
from typing import Optional, List, Dict, Any
from passlib.context import CryptContext
from passlib.hash import bcrypt

from src.schemas.auth import PasswordRequirements


class PasswordManager:
    """Password management utilities for hashing and validation"""
    
    def __init__(self):
        # Configure password context with bcrypt
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Strong rounds for security
        )
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        if not password:
            raise ValueError("Password cannot be empty")
        
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        if not plain_password or not hashed_password:
            return False
        
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """Check if password hash needs to be updated"""
        return self.pwd_context.needs_update(hashed_password)
    
    def generate_password(self, length: int = 16, include_symbols: bool = True) -> str:
        """Generate a secure random password"""
        if length < 8:
            raise ValueError("Password length must be at least 8 characters")
        
        # Character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?" if include_symbols else ""
        
        # Ensure at least one character from each required set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase), 
            secrets.choice(digits)
        ]
        
        if include_symbols:
            password.append(secrets.choice(symbols))
        
        # Fill remaining length with random choices from all sets
        all_chars = lowercase + uppercase + digits + symbols
        for _ in range(length - len(password)):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password list
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def validate_password_strength(
        self,
        password: str,
        requirements: Optional[PasswordRequirements] = None
    ) -> Dict[str, Any]:
        """
        Validate password against complexity requirements
        
        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        if requirements is None:
            requirements = PasswordRequirements()
        
        errors = []
        
        # Length check
        if len(password) < requirements.min_length:
            errors.append(f"Password must be at least {requirements.min_length} characters long")
        
        # Uppercase check
        if requirements.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Lowercase check  
        if requirements.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Numbers check
        if requirements.require_numbers and not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one number")
        
        # Symbols check
        if requirements.require_symbols and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            errors.append("Password must contain at least one special character")
        
        # Forbidden patterns check
        for pattern in requirements.forbidden_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                errors.append(f"Password contains forbidden pattern: {pattern}")
        
        # Common password patterns
        common_patterns = [
            (r'(.)\1{2,}', "Password cannot contain more than 2 consecutive identical characters"),
            (r'(012|123|234|345|456|567|678|789|890)', "Password cannot contain sequential numbers"),
            (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', "Password cannot contain sequential letters"),
            (r'^(password|admin|user|test|demo|guest|root)', "Password cannot start with common words"),
        ]
        
        for pattern, message in common_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                errors.append(message)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength_score": self._calculate_strength_score(password)
        }
    
    def _calculate_strength_score(self, password: str) -> int:
        """
        Calculate password strength score (0-100)
        """
        score = 0
        
        # Length score (up to 25 points)
        score += min(25, len(password) * 2)
        
        # Character variety (up to 25 points)
        if re.search(r'[a-z]', password):
            score += 5
        if re.search(r'[A-Z]', password):
            score += 5
        if re.search(r'[0-9]', password):
            score += 5
        if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            score += 10
        
        # Complexity patterns (up to 25 points)
        unique_chars = len(set(password))
        score += min(15, unique_chars)
        
        # No common patterns (up to 10 points)
        if not re.search(r'(.)\1{2,}', password):
            score += 3
        if not re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            score += 3
        if not re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk)', password, re.IGNORECASE):
            score += 4
        
        # Additional entropy (up to 25 points)
        if len(password) >= 12:
            score += 5
        if len(password) >= 16:
            score += 5
        if unique_chars >= len(password) * 0.8:  # High character diversity
            score += 5
        if not any(word in password.lower() for word in ['password', 'admin', 'user', 'test']):
            score += 5
        if len(set(password[i:i+3] for i in range(len(password)-2))) == len(password)-2:  # No repeated trigrams
            score += 5
        
        return min(100, score)
    
    def check_common_passwords(self, password: str) -> bool:
        """
        Check if password is in common passwords list
        Returns True if password is common (should be rejected)
        """
        # Common passwords to reject
        common_passwords = {
            'password', '123456', '123456789', '12345678', '12345', '1234567',
            'password1', 'admin', 'qwerty', 'abc123', 'Password1', 'password123',
            'admin123', 'root', 'toor', 'pass', 'test', 'guest', 'user', 'demo',
            'letmein', 'welcome', 'monkey', 'dragon', 'master', 'shadow', 'qwerty123'
        }
        
        return password.lower() in common_passwords
    
    def suggest_improvements(self, password: str, requirements: Optional[PasswordRequirements] = None) -> List[str]:
        """Suggest improvements for weak passwords"""
        if requirements is None:
            requirements = PasswordRequirements()
        
        suggestions = []
        
        if len(password) < requirements.min_length:
            suggestions.append(f"Increase length to at least {requirements.min_length} characters")
        
        if requirements.require_uppercase and not re.search(r'[A-Z]', password):
            suggestions.append("Add uppercase letters (A-Z)")
        
        if requirements.require_lowercase and not re.search(r'[a-z]', password):
            suggestions.append("Add lowercase letters (a-z)")
        
        if requirements.require_numbers and not re.search(r'[0-9]', password):
            suggestions.append("Add numbers (0-9)")
        
        if requirements.require_symbols and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            suggestions.append("Add special characters (!@#$%^&*)")
        
        if self.check_common_passwords(password):
            suggestions.append("Avoid common passwords")
        
        if re.search(r'(.)\1{2,}', password):
            suggestions.append("Avoid repeating characters")
        
        if len(set(password)) < len(password) * 0.6:
            suggestions.append("Use more unique characters")
        
        if len(password) < 12:
            suggestions.append("Consider using 12+ characters for better security")
        
        return suggestions


class PasswordPolicy:
    """Password policy enforcement and management"""
    
    def __init__(self, requirements: Optional[PasswordRequirements] = None):
        self.requirements = requirements or PasswordRequirements()
        self.password_manager = PasswordManager()
    
    def enforce_policy(self, password: str, user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enforce password policy with comprehensive checks
        
        Args:
            password: The password to validate
            user_info: Optional user information for context-aware validation
            
        Returns:
            Dict with validation results
        """
        result = self.password_manager.validate_password_strength(password, self.requirements)
        
        # Additional policy checks
        if user_info:
            # Check if password contains user information
            email = user_info.get('email', '').lower()
            if email:
                email_local = email.split('@')[0]
                if email_local.lower() in password.lower():
                    result['errors'].append("Password cannot contain parts of your email address")
                    result['valid'] = False
            
            # Check if password contains user's name
            name = user_info.get('name', '').lower()
            if name and len(name) > 2 and name in password.lower():
                result['errors'].append("Password cannot contain your name")
                result['valid'] = False
        
        # Check against common passwords
        if self.password_manager.check_common_passwords(password):
            result['errors'].append("This password is too common")
            result['valid'] = False
        
        return result
    
    def get_policy_description(self) -> Dict[str, Any]:
        """Get human-readable policy description"""
        return {
            "min_length": self.requirements.min_length,
            "require_uppercase": self.requirements.require_uppercase,
            "require_lowercase": self.requirements.require_lowercase,
            "require_numbers": self.requirements.require_numbers,
            "require_symbols": self.requirements.require_symbols,
            "forbidden_patterns": self.requirements.forbidden_patterns,
            "description": f"Password must be at least {self.requirements.min_length} characters long and contain: " +
                          ", ".join([
                              "uppercase letters" if self.requirements.require_uppercase else "",
                              "lowercase letters" if self.requirements.require_lowercase else "",
                              "numbers" if self.requirements.require_numbers else "",
                              "special characters" if self.requirements.require_symbols else ""
                          ]).strip(", ")
        }


# Global instances
password_manager = PasswordManager()
default_password_policy = PasswordPolicy()