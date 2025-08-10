"""
Permission and RolePermission models for Module 6
"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.models.base import BaseModel
from src.utils.types import UUID, ARRAY, JSONB


class Permission(BaseModel):
    """Permission definition.

    Maps to sentinel.permissions
    """
    __tablename__ = "permissions"
    __table_args__ = {"schema": "sentinel"}

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Resource targeting
    resource_type = Column(ENUM(
        "product_family", "app", "capability", "service", "entity", "page", "api",
        name="resource_type", schema="sentinel"
    ), nullable=False)
    # Direct resource anchor with proper foreign key relationship  
    resource_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.resources.id", ondelete="CASCADE"), nullable=True)
    resource_path = Column(Text, nullable=True)

    # Actions and conditions
    actions = Column(ARRAY(ENUM(
        "create", "read", "update", "delete", "execute", "approve", "reject",
        name="permission_action", schema="sentinel"
    )), nullable=False)

    conditions = Column(JSONB, nullable=True, default=dict)
    field_permissions = Column(JSONB, nullable=True, default=dict)

    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant")
    resource = relationship("Resource", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<Permission(id='{self.id}', name='{self.name}', type='{self.resource_type}')>"


class RolePermission(BaseModel):
    """Role-Permission assignment mapping.

    Maps to sentinel.role_permissions
    """
    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "sentinel"}

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    role = relationship("Role")
    permission = relationship("Permission")
    granter = relationship("User", foreign_keys=[granted_by])

    def __repr__(self) -> str:
        return f"<RolePermission(role_id='{self.role_id}', permission_id='{self.permission_id}')>"

