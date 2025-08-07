"""
Authentication middleware for request processing
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, List
import logging
import time

from src.utils.jwt import jwt_manager, blacklist_manager
from src.core.exceptions import AuthenticationError, RateLimitError


logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling authentication across all requests
    """
    
    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/token",
            "/api/v1/auth/password-requirements",
            "/api/v1/auth/health"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
        
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        
        if authorization:
            try:
                # Validate Bearer token format
                parts = authorization.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]
                    
                    # Check if token is blacklisted
                    jti = jwt_manager.extract_jti(token)
                    if jti and await blacklist_manager.is_token_blacklisted(token):
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={
                                "error": "token_revoked",
                                "error_description": "This token has been revoked"
                            }
                        )
                    
                    # Validate token (but don't require it for all endpoints)
                    try:
                        claims = jwt_manager.decode_token(token, verify_exp=True)
                        
                        # Add user context to request state
                        request.state.user_id = claims.get("sub")
                        request.state.tenant_id = claims.get("tenant_id")
                        request.state.tenant_code = claims.get("tenant_code")
                        request.state.is_service_account = claims.get("is_service_account", False)
                        request.state.scopes = claims.get("scopes", [])
                        request.state.session_id = claims.get("session_id")
                        
                    except ValueError as e:
                        # Invalid token - let endpoint decide if auth is required
                        logger.debug(f"Invalid token in request: {str(e)}")
            
            except Exception as e:
                logger.error(f"Error processing authentication: {str(e)}")
        
        # Continue processing request
        response = await call_next(request)
        return response
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path should be excluded from authentication"""
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return True
        return False


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding tenant context to requests
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from various sources
        tenant_id = None
        tenant_code = None
        
        # 1. From JWT token (already set by AuthenticationMiddleware)
        if hasattr(request.state, "tenant_id"):
            tenant_id = request.state.tenant_id
            tenant_code = request.state.tenant_code
        
        # 2. From X-Tenant-ID header (for service accounts)
        elif "x-tenant-id" in request.headers:
            tenant_id = request.headers["x-tenant-id"]
        
        # 3. From X-Tenant-Code header
        elif "x-tenant-code" in request.headers:
            tenant_code = request.headers["x-tenant-code"]
        
        # 4. From subdomain (e.g., tenant1.example.com)
        elif "host" in request.headers:
            host = request.headers["host"]
            parts = host.split(".")
            if len(parts) > 2:  # Has subdomain
                potential_tenant = parts[0]
                if potential_tenant not in ["www", "api", "app"]:
                    tenant_code = potential_tenant.upper()
        
        # Add to request state
        if tenant_id:
            request.state.tenant_id = tenant_id
        if tenant_code:
            request.state.tenant_code = tenant_code
        
        # Continue processing
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding security headers to responses
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add CORS headers if needed (configure based on environment)
        if hasattr(request.state, "tenant_code"):
            response.headers["X-Tenant"] = request.state.tenant_code
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses
    """
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Get response
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware
    """
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.client_calls = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        x_forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.client.host
        
        # Check rate limit
        now = time.time()
        if client_ip not in self.client_calls:
            self.client_calls[client_ip] = []
        
        # Remove old calls
        self.client_calls[client_ip] = [
            call_time for call_time in self.client_calls[client_ip]
            if call_time > now - 60
        ]
        
        # Check if over limit
        if len(self.client_calls[client_ip]) >= self.calls_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "error_description": f"Maximum {self.calls_per_minute} requests per minute exceeded",
                    "retry_after": 60
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.calls_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + 60))
                }
            )
        
        # Record this call
        self.client_calls[client_ip].append(now)
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls_per_minute - len(self.client_calls[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + 60))
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except RateLimitError as e:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": e.error_code or "rate_limit_exceeded",
                    "error_description": str(e)
                }
            )
            
        except AuthenticationError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": e.error_code or "authentication_failed",
                    "error_description": str(e)
                }
            )
            
        except HTTPException as e:
            # Let FastAPI handle HTTP exceptions
            raise
            
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_server_error",
                    "error_description": "An unexpected error occurred"
                }
            )