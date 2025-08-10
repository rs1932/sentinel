"""
Group-related SQLAlchemy models for Module 5 (Groups)
"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..models.base import BaseModel
from ..models.mixins import MetadataMixin
from ..utils.types import UUID


class Group(MetadataMixin, BaseModel):
    """
    User Group with optional hierarchy and metadata.

    Notes:
    - Database column is `group_metadata` (JSON). MetadataMixin maps API "metadata"
      to this column for compatibility.
    - Unique constraint (tenant_id, name) is handled at the DB level per schema.
    """

    __tablename__ = "groups"
    __table_args__ = {"schema": "sentinel"}

    # Core identification
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Hierarchy
    parent_group_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.groups.id", ondelete="CASCADE"), nullable=True, index=True)

    # Metadata and status
    group_metadata = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant")
    parent_group = relationship("Group", remote_side="Group.id")
    child_groups = relationship("Group", cascade="all, delete-orphan")

    memberships = relationship(
        "UserGroup",
        back_populates="group",
        cascade="all, delete-orphan"
    )

    role_assignments = relationship(
        "GroupRole",
        back_populates="group",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Group(id='{self.id}', name='{self.name}', tenant_id='{self.tenant_id}')>"


class UserGroup(BaseModel):
    """
    User-Group membership with audit trail.
    Enforced unique (user_id, group_id) at DB level.
    """

    __tablename__ = "user_groups"
    __table_args__ = {"schema": "sentinel"}

    user_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.groups.id", ondelete="CASCADE"), nullable=False, index=True)

    # Audit
    added_by = Column(UUID(as_uuid=True), ForeignKey("sentinel.users.id"), nullable=True)
    added_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    group = relationship("Group", back_populates="memberships")

    def __repr__(self) -> str:
        return f"<UserGroup(user_id='{self.user_id}', group_id='{self.group_id}')>"


class GroupRole(BaseModel):
    """
    Group-Role assignment with audit trail.
    Enforced unique (group_id, role_id) at DB level.
    """

    __tablename__ = "group_roles"
    __table_args__ = {"schema": "sentinel"}

    group_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.groups.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.roles.id", ondelete="CASCADE"), nullable=False)

    # Audit
    granted_by = Column(UUID(as_uuid=True), ForeignKey("sentinel.users.id"), nullable=True)
    granted_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    group = relationship("Group", back_populates="role_assignments")
    role = relationship("Role")

    def __repr__(self) -> str:
        return f"<GroupRole(group_id='{self.group_id}', role_id='{self.role_id}')>"

