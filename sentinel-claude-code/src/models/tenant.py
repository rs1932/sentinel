from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
import enum
import uuid

from src.models.base import BaseModel
from src.utils.types import UUID, ARRAY

class TenantType(str, enum.Enum):
    ROOT = "root"
    SUB_TENANT = "sub_tenant"

class IsolationMode(str, enum.Enum):
    SHARED = "shared"
    DEDICATED = "dedicated"

class Tenant(BaseModel):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "sentinel"}
    
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    type = Column(String(50), nullable=False, default='root')
    parent_tenant_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.tenants.id", ondelete="CASCADE"), nullable=True)
    isolation_mode = Column(String(50), nullable=False, default='shared')
    settings = Column(JSON, default=dict)
    features = Column(ARRAY(Text), default=list)
    tenant_metadata = Column("metadata", JSON, default=dict)
    is_active = Column(Boolean, default=True)
    
    parent = relationship("Tenant", remote_side="Tenant.id", backref="sub_tenants")
    users = relationship("User", back_populates="tenant")
    
    def __init__(self, **kwargs):
        # Handle API compatibility: map 'metadata' to 'tenant_metadata'
        if "metadata" in kwargs:
            kwargs["tenant_metadata"] = kwargs.pop("metadata")

        # Handle enum to string conversion for API compatibility
        if "type" in kwargs and hasattr(kwargs["type"], 'value'):
            kwargs["type"] = kwargs["type"].value
        if "isolation_mode" in kwargs and hasattr(kwargs["isolation_mode"], 'value'):
            kwargs["isolation_mode"] = kwargs["isolation_mode"].value

        if "id" not in kwargs and kwargs.get("code") == "PLATFORM":
            kwargs["id"] = uuid.UUID("00000000-0000-0000-0000-000000000000")
        super().__init__(**kwargs)
    
    def to_dict(self):
        result = super().to_dict()
        # type and isolation_mode are now stored as strings directly
        # result["type"] = self.type.value if self.type else None
        # result["isolation_mode"] = self.isolation_mode.value if self.isolation_mode else None

        # Handle API compatibility: map 'tenant_metadata' to 'metadata'
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
    
    def is_sub_tenant_of(self, tenant_id: uuid.UUID) -> bool:
        current = self
        while current.parent:
            if current.parent_tenant_id == tenant_id:
                return True
            current = current.parent
        return False
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, code={self.code}, name={self.name}, type={self.type})>"