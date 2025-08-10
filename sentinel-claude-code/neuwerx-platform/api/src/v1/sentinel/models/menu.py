"""
Menu and Navigation models for Module 9

Supports hierarchical menu structure with user customization capabilities
"""
from sqlalchemy import Column, String, Integer, Boolean, UUID, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from typing import Dict, Any, List, Optional

from .base import BaseModel


class MenuItem(BaseModel):
    """
    Menu Item model for hierarchical navigation structure.
    
    Supports:
    - Hierarchical menu structure with parent-child relationships
    - Tenant-specific and system-wide menu items
    - Permission-based visibility
    - Custom ordering and metadata
    """
    __tablename__ = "menu_items"
    
    # Tenant relationship (nullable for system-wide items)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey('sentinel.tenants.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    # Self-referencing relationship for hierarchy
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey('sentinel.menu_items.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    # Menu item identification and display
    name = Column(String(100), nullable=False)  # Unique identifier
    display_name = Column(String(255), nullable=True)  # User-friendly name
    icon = Column(String(50), nullable=True)  # Icon name/class
    url = Column(String(500), nullable=True)  # Navigation URL
    
    # Resource and permission linking
    resource_id = Column(
        UUID(as_uuid=True),
        ForeignKey('sentinel.resources.id', ondelete='SET NULL'),
        nullable=True
    )
    required_permission = Column(String(255), nullable=True)  # Permission needed to view
    
    # Display configuration
    display_order = Column(Integer, default=0, nullable=False)
    is_visible = Column(Boolean, default=True, nullable=False)
    menu_metadata = Column(JSONB, default={}, nullable=False)  # Additional configuration
    
    # Relationships
    tenant = relationship("Tenant", back_populates="menu_items")
    resource = relationship("Resource", back_populates="menu_items")
    
    # Hierarchical relationships
    parent = relationship(
        "MenuItem",
        remote_side="MenuItem.id",
        back_populates="children"
    )
    children = relationship(
        "MenuItem",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="MenuItem.display_order"
    )
    
    # User customizations
    user_customizations = relationship(
        "UserMenuCustomization",
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return (f"<MenuItem(id='{self.id}', name='{self.name}', "
                f"display_name='{self.display_name}', parent_id='{self.parent_id}')>")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert menu item to dictionary representation."""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id) if self.tenant_id else None,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'name': self.name,
            'display_name': self.display_name,
            'icon': self.icon,
            'url': self.url,
            'resource_id': str(self.resource_id) if self.resource_id else None,
            'required_permission': self.required_permission,
            'display_order': self.display_order,
            'is_visible': self.is_visible,
            'menu_metadata': self.menu_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_system_wide(self) -> bool:
        """Check if this is a system-wide menu item."""
        return self.tenant_id is None
    
    def is_tenant_specific(self) -> bool:
        """Check if this is a tenant-specific menu item."""
        return self.tenant_id is not None
    
    def has_permission_requirement(self) -> bool:
        """Check if this menu item requires a specific permission."""
        return self.required_permission is not None
    
    def get_full_hierarchy_path(self) -> List[str]:
        """Get the full hierarchy path from root to this item."""
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return path
    
    def get_child_count(self) -> int:
        """Get the number of direct children."""
        return len(self.children) if self.children else 0
    
    def is_leaf_node(self) -> bool:
        """Check if this is a leaf node (no children)."""
        return self.get_child_count() == 0


class UserMenuCustomization(BaseModel):
    """
    User-specific menu customizations.
    
    Allows users to:
    - Hide/show menu items
    - Custom ordering of menu items
    - Personal preferences per user
    """
    __tablename__ = "user_menu_customizations"
    
    # User and menu item references
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('sentinel.users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    menu_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey('sentinel.menu_items.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Customization options
    is_hidden = Column(Boolean, default=False, nullable=False)
    custom_order = Column(Integer, nullable=True)  # User's preferred order
    
    # Relationships
    user = relationship("User", back_populates="menu_customizations")
    menu_item = relationship("MenuItem", back_populates="user_customizations")
    
    # Unique constraint handled by database
    __table_args__ = {'extend_existing': True}
    
    def __repr__(self) -> str:
        return (f"<UserMenuCustomization(id='{self.id}', user_id='{self.user_id}', "
                f"menu_item_id='{self.menu_item_id}', is_hidden={self.is_hidden})>")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert customization to dictionary representation."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'menu_item_id': str(self.menu_item_id),
            'is_hidden': self.is_hidden,
            'custom_order': self.custom_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_visible_override(self) -> bool:
        """Check if this customization makes the item visible."""
        return not self.is_hidden
    
    def has_custom_ordering(self) -> bool:
        """Check if this customization includes custom ordering."""
        return self.custom_order is not None