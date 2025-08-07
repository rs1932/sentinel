"""
Custom exceptions for the Sentinel application
"""

class SentinelException(Exception):
    """Base exception class for Sentinel application"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ValidationError(SentinelException):
    """Raised when input validation fails"""
    pass


class AuthenticationError(SentinelException):
    """Raised when authentication fails"""
    pass


class AuthorizationError(SentinelException):
    """Raised when authorization fails"""
    pass


class NotFoundError(SentinelException):
    """Raised when a resource is not found"""
    pass


class ConflictError(SentinelException):
    """Raised when a resource conflict occurs"""
    pass


class TenantError(SentinelException):
    """Raised when tenant-related operations fail"""
    pass


class TokenError(SentinelException):
    """Raised when token operations fail"""
    pass


class RateLimitError(SentinelException):
    """Raised when rate limit is exceeded"""
    pass