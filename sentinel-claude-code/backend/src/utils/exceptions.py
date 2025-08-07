from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class SentinelException(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(SentinelException):
    pass

class ValidationError(SentinelException):
    pass

class AuthenticationError(SentinelException):
    pass

class AuthorizationError(SentinelException):
    pass

class NotFoundError(SentinelException):
    pass

class ConflictError(SentinelException):
    pass

class RateLimitError(SentinelException):
    pass

class TenantError(SentinelException):
    pass

class PermissionError(SentinelException):
    pass

class ResourceLimitError(SentinelException):
    pass

class BadRequestError(HTTPException):
    def __init__(self, detail: str, headers: Optional[Dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers)

class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials", headers: Optional[Dict[str, str]] = None):
        headers = headers or {"WWW-Authenticate": "Bearer"}
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers=headers)

class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "Not enough permissions", headers: Optional[Dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, headers=headers)

class NotFoundHTTPError(HTTPException):
    def __init__(self, detail: str = "Resource not found", headers: Optional[Dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)

class ConflictHTTPError(HTTPException):
    def __init__(self, detail: str = "Resource conflict", headers: Optional[Dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, headers=headers)

class UnprocessableEntityError(HTTPException):
    def __init__(self, detail: str = "Unprocessable entity", headers: Optional[Dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail, headers=headers)

class TooManyRequestsError(HTTPException):
    def __init__(self, detail: str = "Too many requests", headers: Optional[Dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail, headers=headers)

class InternalServerError(HTTPException):
    def __init__(self, detail: str = "Internal server error", headers: Optional[Dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail, headers=headers)

class ServiceUnavailableError(HTTPException):
    def __init__(self, detail: str = "Service temporarily unavailable", headers: Optional[Dict[str, str]] = None):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail, headers=headers)