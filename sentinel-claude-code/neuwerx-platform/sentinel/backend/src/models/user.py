"""
User model for authentication (Module 2)
Basic auth fields only - full user management in Module 3
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models.base import BaseModel
from src.models.mixins import MetadataMixin
from src.utils.types import UUID


class User(MetadataMixin, BaseModel):
    """
    User model with basic authentication fields.
    Full user management features will be added in Module 3.
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "sentinel"}
    
    # Core identification
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    username = Column(String(100), nullable=True)
    
    # Authentication fields
    password_hash = Column(String(255), nullable=True)  # NULL for SSO users
    is_service_account = Column(Boolean, default=False, nullable=False)
    service_account_key = Column(String(255), unique=True, nullable=True)  # For M2M authentication
    
    # Basic user attributes (expanded in Module 3)
    attributes = Column(JSON, default=dict)  # User attributes for ABAC
    preferences = Column(JSON, default=dict)  # UI preferences, etc.
    
    # Profile information
    avatar_url = Column(String(500), nullable=True)  # URL to avatar image
    avatar_file_id = Column(String(255), nullable=True)  # Internal file reference
    
    # Authentication tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column('login_count', Integer, default=0, nullable=True)
    failed_login_count = Column('failed_login_count', Integer, default=0, nullable=True)  # Track failed logins
    locked_until = Column(DateTime(timezone=True), nullable=True)  # Account lockout
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    role_assignments = relationship("UserRole", foreign_keys="UserRole.user_id", back_populates="user", cascade="all, delete-orphan")
    menu_customizations = relationship("UserMenuCustomization", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        # Handle service account initialization
        if kwargs.get("is_service_account") and not kwargs.get("service_account_key"):
            kwargs["service_account_key"] = f"svc_{uuid.uuid4().hex[:12]}"
        
        # Call mixin init which handles metadata mapping
        super().__init__(**kwargs)
    
    def to_dict(self):
        """Convert model to dictionary with metadata mapping"""
        # First get the base dictionary
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, UUID):
                result[column.name] = str(value)
            elif hasattr(value, 'isoformat'):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        
        # No metadata mapping needed for this simplified model
        
        # Never expose sensitive fields in dict
        sensitive_fields = ['password_hash', 'service_account_key']
        for field in sensitive_fields:
            result.pop(field, None)
            
        # Ensure timestamps are present (for testing without DB)
        if not result.get('created_at'):
            result['created_at'] = datetime.utcnow().isoformat()
        if not result.get('updated_at'):
            result['updated_at'] = datetime.utcnow().isoformat()
        
        return result
    
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    def can_authenticate(self) -> bool:
        """Check if user can authenticate (active, not locked, email verified for regular users)"""
        if not self.is_active:
            return False
        if self.is_locked():
            return False
        # For now, skip email verification check since we don't have that field in DB
        return True
    
    def increment_failed_login(self, max_attempts: int = 5, lockout_duration_minutes: int = 30):
        """Increment failed login attempts and lock account if threshold exceeded"""
        current_attempts = self.failed_login_count or 0
        current_attempts += 1
        self.failed_login_count = current_attempts
        
        if current_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_duration_minutes)
    
    def reset_failed_logins(self):
        """Reset failed login attempts after successful authentication"""
        self.failed_login_count = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()
        # Increment login count
        self.login_count = (self.login_count or 0) + 1
    
    def is_service_account_valid(self, provided_key: str) -> bool:
        """Validate service account key"""
        if not self.is_service_account or not self.service_account_key:
            return False
        return self.service_account_key == provided_key
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tenant_id={self.tenant_id}, is_service_account={self.is_service_account})>"