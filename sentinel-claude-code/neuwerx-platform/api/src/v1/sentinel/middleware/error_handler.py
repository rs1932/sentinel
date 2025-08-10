from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from typing import Union

from ..utils.exceptions import SentinelException
from ..config import settings

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url),
                "method": request.method
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Validation error",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "details": errors,
                "path": str(request.url),
                "method": request.method
            }
        }
    )

async def sentinel_exception_handler(request: Request, exc: SentinelException):
    logger.error(f"SentinelException: {exc.message}", extra={"details": exc.details})
    
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if exc.__class__.__name__ in ["NotFoundError"]:
        status_code = status.HTTP_404_NOT_FOUND
    elif exc.__class__.__name__ in ["ValidationError"]:
        status_code = status.HTTP_400_BAD_REQUEST
    elif exc.__class__.__name__ in ["AuthenticationError"]:
        status_code = status.HTTP_401_UNAUTHORIZED
    elif exc.__class__.__name__ in ["AuthorizationError", "PermissionError"]:
        status_code = status.HTTP_403_FORBIDDEN
    elif exc.__class__.__name__ in ["ConflictError"]:
        status_code = status.HTTP_409_CONFLICT
    elif exc.__class__.__name__ in ["RateLimitError"]:
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": exc.message,
                "status_code": status_code,
                "type": exc.__class__.__name__,
                "details": exc.details if settings.DEBUG else {},
                "path": str(request.url),
                "method": request.method
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "message": str(exc),
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "type": exc.__class__.__name__,
                    "traceback": traceback.format_exc(),
                    "path": str(request.url),
                    "method": request.method
                }
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "message": "An internal server error occurred",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "path": str(request.url),
                    "method": request.method
                }
            }
        )