from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
import enum
import uuid

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
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, code={self.code}, name={self.name}, type={self.type})>"