"""
Role model for the Sentinel access management platform.
"""
from enum import Enum
from sqlalchemy import Column, String, Text, Boolean, Integer, UUID, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime, timezone

from .base import BaseModel


class RoleType(str, Enum):
    """Role type enumeration."""
    SYSTEM = "system"
    CUSTOM = "custom"


class Role(BaseModel):
    """
    Role model for hierarchical role-based access control.
    
    Roles support inheritance through parent-child relationships and can be
    assigned to users directly or through groups. Each role has a priority
    for conflict resolution and can contain custom metadata.
    """
    __tablename__ = "roles"
    __table_args__ = {'schema': 'sentinel'}
    
    # Core identification
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('sentinel.tenants.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Role configuration
    type = Column(ENUM('system', 'custom', name='role_type', schema='sentinel'), nullable=False, default=RoleType.CUSTOM)
    parent_role_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('sentinel.roles.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    is_assignable = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    role_metadata = Column(JSONB, default={})
    
    # Activity status
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_by = Column(
        UUID(as_uuid=True), 
        ForeignKey('sentinel.users.id'),
        nullable=True
    )
    
    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    parent_role = relationship("Role", remote_side="Role.id")
    child_roles = relationship(
        "Role",
        cascade="all, delete-orphan"
    )
    creator = relationship("User", foreign_keys=[created_by])
    
    # User assignments
    user_assignments = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    # Group and permission assignments will be added when 
    # Modules 5 and 6 are implemented
    
    # Constraints
    __table_args__ = (
        {'schema': 'sentinel'},
        # Unique role names per tenant
        # This will be handled in the migration
    )
    
    def __repr__(self) -> str:
        return f"<Role(id='{self.id}', name='{self.name}', type='{self.type}', tenant_id='{self.tenant_id}')>"
    
    def to_dict(self) -> dict:
        """Convert role to dictionary representation."""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'type': self.type,
            'parent_role_id': str(self.parent_role_id) if self.parent_role_id else None,
            'is_assignable': self.is_assignable,
            'priority': self.priority,
            'role_metadata': self.role_metadata,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': str(self.created_by) if self.created_by else None
        }


class UserRole(BaseModel):
    """
    User-Role assignment model with audit trail.
    
    Tracks when roles are assigned to users, by whom, and supports
    role expiration for temporary access grants.
    """
    __tablename__ = "user_roles"
    __table_args__ = {'schema': 'sentinel'}
    
    # Assignment details
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('sentinel.users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    role_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('sentinel.roles.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Audit information
    granted_by = Column(
        UUID(as_uuid=True), 
        ForeignKey('sentinel.users.id'),
        nullable=True
    )
    granted_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="role_assignments")
    role = relationship("Role", back_populates="user_assignments")
    granter = relationship("User", foreign_keys=[granted_by])
    
    # Unique constraint will be handled in migration
    __table_args__ = (
        {'schema': 'sentinel'},
        # UniqueConstraint('user_id', 'role_id', name='unique_user_role')
    )
    
    def __repr__(self) -> str:
        return f"<UserRole(user_id='{self.user_id}', role_id='{self.role_id}', active={self.is_active})>"


# GroupRole and RolePermission models will be added when 
# Groups (Module 5) and Permissions (Module 6) are implemented