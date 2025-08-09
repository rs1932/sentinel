"""
Resource model for Module 7: Hierarchical resource management
"""
from enum import Enum
from sqlalchemy import Column, String, Text, Boolean, UUID, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from uuid import uuid4
from datetime import datetime, timezone

from .base import BaseModel


class ResourceType(str, Enum):
    """Resource type enumeration matching database enum."""
    PRODUCT_FAMILY = "product_family"
    APP = "app"
    CAPABILITY = "capability"
    SERVICE = "service"
    ENTITY = "entity"
    PAGE = "page"
    API = "api"


class Resource(BaseModel):
    """
    Hierarchical resource model for access control.
    
    Supports multi-level hierarchy: Product Family > App > Capability > Service
    Uses materialized path for efficient hierarchy queries.
    """
    __tablename__ = "resources"
    __table_args__ = (
        CheckConstraint(
            '(parent_id IS NULL AND path = \'/\' || id::text || \'/\') OR '
            '(parent_id IS NOT NULL AND path ~ \'^/[0-9a-f-]+(/[0-9a-f-]+)+/$\')',
            name='valid_path_structure'
        ),
        {'schema': 'sentinel'}
    )
    
    # Core identification
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('sentinel.tenants.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    type = Column(
        ENUM(ResourceType, name='resource_type', schema='sentinel', values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False)  # Unique identifier within type and tenant
    
    # Hierarchy
    parent_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('sentinel.resources.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    path = Column(Text, nullable=True, index=True)  # Materialized path for efficient queries
    
    # Configuration
    attributes = Column(JSONB, default={}, nullable=False)  # Resource-specific attributes
    workflow_enabled = Column(Boolean, default=False, nullable=False)
    workflow_config = Column(JSONB, default={}, nullable=False)
    
    # Activity status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit fields (already inherited from BaseModel: id, created_at, updated_at)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="resources")
    parent = relationship("Resource", remote_side="Resource.id", back_populates="children")
    children = relationship(
        "Resource",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    
    # Permissions relationship (will be used by permissions module)
    permissions = relationship(
        "Permission",
        back_populates="resource",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    
    # Menu items relationship
    menu_items = relationship(
        "MenuItem",
        back_populates="resource",
        passive_deletes=True
    )
    
    # Note: Unique constraint for code within tenant and type is handled in the database migration
    
    @validates('type')
    def validate_type(self, key, type_value):
        """Validate resource type hierarchy rules."""
        if isinstance(type_value, str):
            type_value = ResourceType(type_value)
        return type_value
    
    @validates('parent_id')
    def validate_parent_hierarchy(self, key, parent_id):
        """Validate parent-child hierarchy rules."""
        if parent_id == self.id:
            raise ValueError("Resource cannot be its own parent")
        return parent_id
    
    def __repr__(self) -> str:
        return f"<Resource(id='{self.id}', type='{self.type}', name='{self.name}', tenant_id='{self.tenant_id}')>"
    
    def to_dict(self) -> dict:
        """Convert resource to dictionary representation."""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'type': self.type.value if isinstance(self.type, ResourceType) else self.type,
            'name': self.name,
            'code': self.code,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'path': self.path,
            'attributes': self.attributes,
            'workflow_enabled': self.workflow_enabled,
            'workflow_config': self.workflow_config,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_ancestors(self) -> list:
        """Get list of ancestor resource IDs from materialized path."""
        if not self.path or self.path == f'/{self.id}/':
            return []
        
        # Extract UUIDs from path (format: /uuid1/uuid2/current_uuid/)
        path_parts = [p for p in self.path.split('/') if p and p != str(self.id)]
        return path_parts
    
    def get_depth(self) -> int:
        """Get the depth of this resource in the hierarchy (0 = root)."""
        if not self.path:
            return 0
        return len([p for p in self.path.split('/') if p]) - 1
    
    def is_ancestor_of(self, other_resource) -> bool:
        """Check if this resource is an ancestor of another resource."""
        if not other_resource.path:
            return False
        return other_resource.path.startswith(f'{self.path}{self.id}/')
    
    def is_descendant_of(self, other_resource) -> bool:
        """Check if this resource is a descendant of another resource."""
        return other_resource.is_ancestor_of(self)
    
    @property
    def hierarchy_level_name(self) -> str:
        """Get human-readable hierarchy level name."""
        hierarchy_names = {
            ResourceType.PRODUCT_FAMILY: "Product Family",
            ResourceType.APP: "Application", 
            ResourceType.CAPABILITY: "Capability",
            ResourceType.SERVICE: "Service",
            ResourceType.ENTITY: "Entity",
            ResourceType.PAGE: "Page",
            ResourceType.API: "API Endpoint"
        }
        return hierarchy_names.get(self.type, str(self.type))