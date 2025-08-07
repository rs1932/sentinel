"""
RefreshToken model for secure token rotation
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import hashlib

from src.database import Base
from src.utils.types import UUID


class RefreshToken(Base):
    """
    Refresh token model for secure token rotation.
    Stores hashed tokens and device information for security.
    """
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "sentinel"}
    
    # Base fields that exist in the database
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), nullable=True)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.users.id", ondelete="CASCADE"), nullable=False)
    
    # Token data (stored as hash for security)
    token_hash = Column(String(255), unique=True, nullable=False)
    
    # Device/session information
    device_info = Column(JSON, default=dict)  # IP, user agent, device fingerprint
    
    # Expiration and usage tracking
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    def __init__(self, **kwargs):
        # Set default expiration if not provided (30 days)
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.utcnow() + timedelta(days=30)
        
        super().__init__(**kwargs)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a refresh token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @classmethod
    def create_for_user(
        cls, 
        user_id: UUID, 
        token: str, 
        device_info: dict = None,
        expires_in_days: int = 30
    ) -> 'RefreshToken':
        """Create a new refresh token for a user"""
        return cls(
            user_id=user_id,
            token_hash=cls.hash_token(token),
            device_info=device_info or {},
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )
    
    def is_valid(self, provided_token: str) -> bool:
        """Check if the provided token matches and is not expired"""
        if self.is_expired():
            return False
        return self.token_hash == self.hash_token(provided_token)
    
    def is_expired(self) -> bool:
        """Check if the refresh token has expired"""
        return datetime.utcnow() > self.expires_at
    
    def mark_used(self):
        """Mark the token as recently used"""
        self.last_used_at = datetime.utcnow()
    
    def update_device_info(self, device_info: dict):
        """Update device information for this token"""
        if device_info:
            current_info = self.device_info or {}
            current_info.update(device_info)
            self.device_info = current_info
    
    def to_dict(self):
        """Convert to dictionary without exposing token hash"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, UUID):
                result[column.name] = str(value)
            elif hasattr(value, 'isoformat'):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        
        # Never expose token hash
        result.pop('token_hash', None)
        
        return result
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"