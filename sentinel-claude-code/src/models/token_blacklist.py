"""
TokenBlacklist model for revoked JWT tokens
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models.base import BaseModel
from src.utils.types import UUID


class TokenBlacklist(BaseModel):
    """
    Token blacklist model for revoked JWT tokens.
    Prevents reuse of revoked access and refresh tokens.
    """
    __tablename__ = "token_blacklist"
    __table_args__ = {"schema": "sentinel"}
    
    # JWT identifier (jti claim)
    jti = Column(String(255), unique=True, nullable=False)
    
    # User who owned the token
    user_id = Column(UUID(as_uuid=True), ForeignKey("sentinel.users.id", ondelete="CASCADE"), nullable=True)
    
    # Token type and expiration
    token_type = Column(String(50), nullable=False)  # 'access', 'refresh'
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Revocation details
    revoked_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    revoked_by = Column(UUID(as_uuid=True), ForeignKey("sentinel.users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    revoked_by_user = relationship("User", foreign_keys=[revoked_by])
    
    @classmethod
    def create_for_token(
        cls,
        jti: str,
        token_type: str,
        expires_at: datetime,
        user_id: uuid.UUID = None,
        revoked_by: uuid.UUID = None,
        reason: str = None
    ) -> 'TokenBlacklist':
        """Create a blacklist entry for a token"""
        return cls(
            jti=jti,
            token_type=token_type,
            expires_at=expires_at,
            user_id=user_id,
            revoked_by=revoked_by,
            reason=reason
        )
    
    def is_expired(self) -> bool:
        """Check if the blacklisted token has expired (can be cleaned up)"""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def is_token_blacklisted(cls, db_session, jti: str) -> bool:
        """Check if a token JTI is blacklisted"""
        blacklisted = db_session.query(cls).filter(
            cls.jti == jti,
            cls.expires_at > datetime.utcnow()  # Only check non-expired blacklist entries
        ).first()
        return blacklisted is not None
    
    @classmethod
    def blacklist_token(
        cls,
        db_session,
        jti: str,
        token_type: str,
        expires_at: datetime,
        user_id: uuid.UUID = None,
        revoked_by: uuid.UUID = None,
        reason: str = None
    ) -> 'TokenBlacklist':
        """Add a token to the blacklist"""
        blacklist_entry = cls.create_for_token(
            jti=jti,
            token_type=token_type,
            expires_at=expires_at,
            user_id=user_id,
            revoked_by=revoked_by,
            reason=reason
        )
        db_session.add(blacklist_entry)
        return blacklist_entry
    
    @classmethod
    def cleanup_expired(cls, db_session) -> int:
        """Remove expired blacklist entries and return count removed"""
        expired_count = db_session.query(cls).filter(
            cls.expires_at <= datetime.utcnow()
        ).count()
        
        db_session.query(cls).filter(
            cls.expires_at <= datetime.utcnow()
        ).delete()
        
        return expired_count
    
    def to_dict(self):
        """Convert to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            elif hasattr(value, 'isoformat'):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        
        return result
    
    def __repr__(self):
        return f"<TokenBlacklist(id={self.id}, jti={self.jti}, token_type={self.token_type}, revoked_at={self.revoked_at})>"