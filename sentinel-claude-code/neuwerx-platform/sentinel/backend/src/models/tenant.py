from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
import enum
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from src.models.base import BaseModel
from src.utils.types import UUID, ARRAY

class TenantType(str, enum.Enum):
    root = "root"
    sub_tenant = "sub_tenant"
    # Add uppercase aliases for backward compatibility
    ROOT = "root"
    SUB_TENANT = "sub_tenant"

class IsolationMode(str, enum.Enum):
    shared = "shared"
    dedicated = "dedicated"
    # Add uppercase aliases for backward compatibility
    SHARED = "shared"
    DEDICATED = "dedicated"

class Tenant(BaseModel):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "sentinel"}
    
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    type = Column(Enum(TenantType, name='tenant_type', schema='sentinel'), nullable=False, default=TenantType.ROOT)
    parent_tenant_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.tenants.id", ondelete="CASCADE"), nullable=True)
    isolation_mode = Column(Enum(IsolationMode, name='isolation_mode', schema='sentinel'), nullable=False, default=IsolationMode.SHARED)
    settings = Column(JSON, default=dict)
    features = Column(ARRAY(Text), default=list)
    tenant_metadata = Column("tenant_metadata", JSON, default=dict)
    is_active = Column(Boolean, default=True)
    
    parent = relationship("Tenant", remote_side="Tenant.id", backref="sub_tenants")
    users = relationship("User", back_populates="tenant")
    roles = relationship("Role", back_populates="tenant")
    resources = relationship("Resource", back_populates="tenant", cascade="all, delete-orphan")
    field_definitions = relationship("FieldDefinition", back_populates="tenant", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="tenant", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        # Handle API compatibility: map 'metadata' to 'tenant_metadata'
        if "metadata" in kwargs:
            kwargs["tenant_metadata"] = kwargs.pop("metadata")

        # Convert string values to enum instances if needed
        if "type" in kwargs and isinstance(kwargs["type"], str):
            kwargs["type"] = TenantType(kwargs["type"])
        if "isolation_mode" in kwargs and isinstance(kwargs["isolation_mode"], str):
            kwargs["isolation_mode"] = IsolationMode(kwargs["isolation_mode"])

        if "id" not in kwargs and kwargs.get("code") == "PLATFORM":
            kwargs["id"] = UUID("00000000-0000-0000-0000-000000000000")
        super().__init__(**kwargs)
    
    def to_dict(self):
        result = super().to_dict()

        # Handle API compatibility: map 'tenant_metadata' to 'metadata' for API responses
        if "tenant_metadata" in result:
            result["metadata"] = result.pop("tenant_metadata")

        return result
    
    def get_hierarchy(self):
        hierarchy = [self]
        current = self
        while current.parent:
            hierarchy.append(current.parent)
            current = current.parent
        return list(reversed(hierarchy))
    
    def is_sub_tenant_of(self, tenant_id: UUID) -> bool:
        current = self
        while current.parent:
            if current.parent_tenant_id == tenant_id:
                return True
            current = current.parent
        return False
    
    # =====================================================
    # TERMINOLOGY MAPPING METHODS
    # =====================================================
    
    def get_terminology_config(self) -> Dict[str, Any]:
        """Get raw terminology configuration from settings (no inheritance)"""
        if not self.settings:
            return {}
        return self.settings.get("terminology_config", {})
    
    def set_terminology_config(self, terminology: Dict[str, str], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Set terminology configuration in settings"""
        if not self.settings:
            self.settings = {}
            
        self.settings["terminology_config"] = terminology
        
        # Update metadata
        terminology_metadata = {
            "last_updated": datetime.utcnow().isoformat(),
            "is_inherited": False
        }
        
        if metadata:
            terminology_metadata.update(metadata)
            
        self.settings["terminology_metadata"] = terminology_metadata
    
    def get_effective_terminology(self) -> Dict[str, str]:
        """Get effective terminology with inheritance from parent hierarchy"""
        # Start with default terminology
        effective_terminology = self._get_default_terminology()
        
        # Collect terminology from hierarchy (root to leaf)
        hierarchy = self.get_hierarchy()
        
        # Apply terminology from root down to current tenant
        for tenant in hierarchy:
            tenant_terminology = tenant.get_terminology_config()
            if tenant_terminology:
                effective_terminology.update(tenant_terminology)
        
        return effective_terminology
    
    def get_terminology_with_metadata(self) -> Dict[str, Any]:
        """Get terminology with inheritance metadata"""
        effective_terminology = self.get_effective_terminology()
        local_terminology = self.get_terminology_config()
        
        # Determine inheritance status
        is_inherited = not bool(local_terminology)
        inherited_from = None
        
        if is_inherited:
            # Find the closest parent with terminology
            current = self.parent
            while current:
                if current.get_terminology_config():
                    inherited_from = current.id
                    break
                current = current.parent
        
        # Get metadata from settings
        metadata = {}
        if self.settings:
            metadata = self.settings.get("terminology_metadata", {})
        
        return {
            "terminology": effective_terminology,
            "is_inherited": is_inherited,
            "inherited_from": inherited_from,
            "local_config": local_terminology,
            "last_updated": metadata.get("last_updated"),
            "template_applied": metadata.get("template_applied")
        }
    
    def clear_terminology_config(self) -> None:
        """Clear local terminology configuration (will inherit from parent)"""
        if self.settings:
            # Create a new dict without terminology keys to trigger SQLAlchemy change detection
            new_settings = {k: v for k, v in self.settings.items() 
                          if k not in ["terminology_config", "terminology_metadata"]}
            self.settings = new_settings if new_settings else {}
    
    def apply_terminology_to_children(self, terminology: Dict[str, str], recursive: bool = True) -> None:
        """Apply terminology configuration to all child tenants"""
        for child in self.sub_tenants:
            child.set_terminology_config(
                terminology, 
                metadata={
                    "applied_from_parent": self.id,
                    "applied_at": datetime.utcnow().isoformat()
                }
            )
            
            # Recursively apply to grandchildren if requested
            if recursive and child.sub_tenants:
                child.apply_terminology_to_children(terminology, recursive=True)
    
    def _get_default_terminology(self) -> Dict[str, str]:
        """Get default Sentinel terminology"""
        return {
            # Basic entities
            "tenant": "Tenant",
            "sub_tenant": "Sub-Tenant",
            "user": "User", 
            "role": "Role",
            "permission": "Permission",
            "resource": "Resource",
            "group": "Group",
            
            # Plural forms
            "tenants": "Tenants",
            "sub_tenants": "Sub-Tenants", 
            "users": "Users",
            "roles": "Roles",
            "permissions": "Permissions",
            "resources": "Resources",
            "groups": "Groups",
            
            # Actions
            "create_tenant": "Create Tenant",
            "create_sub_tenant": "Create Sub-Tenant",
            "create_user": "Create User",
            "create_role": "Create Role",
            "create_group": "Create Group",
            
            # Management pages
            "tenant_management": "Tenant Management",
            "sub_tenant_management": "Sub-Tenant Management", 
            "user_management": "User Management",
            "role_management": "Role Management",
            "permission_management": "Permission Management",
            "group_management": "Group Management",
            
            # Dashboard and navigation
            "dashboard": "Dashboard",
            "dashboard_title": "Dashboard",
            "welcome_message": "Welcome back",
            "admin_title": "Administrator",
            
            # Common UI labels
            "name": "Name",
            "type": "Type",
            "status": "Status",
            "actions": "Actions",
            "edit": "Edit",
            "delete": "Delete",
            "view": "View",
            "add": "Add",
            "manage": "Manage",
            "assign": "Assign"
        }
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, code={self.code}, name={self.name}, type={self.type})>"