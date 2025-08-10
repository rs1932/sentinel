"""
Password reset token model for secure password reset workflows
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import secrets

from ..models.base import BaseModel
from ..utils.types import UUID


class PasswordResetToken(BaseModel):
    """
    Model for storing password reset tokens with expiration
    """
    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": "sentinel"}
    
    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.users.id", ondelete="CASCADE"), nullable=False)
    
    # Token information
    token = Column(String(255), unique=True, nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)  # For secure comparison
    
    # Expiration and usage
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    is_used = Column(Boolean, default=False, nullable=False)
    
    # Request metadata
    request_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", backref="password_reset_tokens")
    
    @classmethod
    def generate_token(cls):
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def create_for_user(cls, user_id, request_ip=None, user_agent=None, expires_in_hours=1):
        """Create a new password reset token for a user"""
        import hashlib
        
        token = cls.generate_token()
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        return cls(
            user_id=user_id,
            token=token,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
            request_ip=request_ip,
            user_agent=user_agent
        )
    
    def is_valid(self):
        """Check if token is still valid"""
        return (
            not self.is_used and 
            self.expires_at > datetime.now(timezone.utc)
        )
    
    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)