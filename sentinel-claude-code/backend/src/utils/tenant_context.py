"""
Tenant context utilities for multi-tenant operations
"""
from contextvars import ContextVar
from typing import Optional
from src.utils.types import UUID

# Context variable to store current tenant ID
_tenant_context: ContextVar[Optional[UUID]] = ContextVar('tenant_id', default=None)


def set_current_tenant_id(tenant_id: UUID) -> None:
    """Set the current tenant ID in context"""
    _tenant_context.set(tenant_id)


def get_current_tenant_id() -> Optional[UUID]:
    """Get the current tenant ID from context"""
    return _tenant_context.get()


def clear_tenant_context() -> None:
    """Clear the tenant context"""
    _tenant_context.set(None)