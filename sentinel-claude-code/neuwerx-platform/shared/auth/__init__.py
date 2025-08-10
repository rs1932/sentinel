"""Shared authentication utilities."""
from .dependencies import (
    AuthService, 
    get_current_user, 
    get_current_active_user,
    RequirePermission,
    auth_service
)

__all__ = [
    'AuthService',
    'get_current_user',
    'get_current_active_user', 
    'RequirePermission',
    'auth_service'
]