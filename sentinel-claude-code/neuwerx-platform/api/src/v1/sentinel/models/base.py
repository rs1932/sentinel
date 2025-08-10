from sqlalchemy import Column, DateTime, MetaData
from sqlalchemy.sql import func
import uuid

from ..database import Base
from ..utils.types import UUID

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self):
        result = {}
        for column in self.__table__.columns:
            # Get the value using the column name, but handle AttributeError gracefully
            try:
                value = getattr(self, column.name)
            except AttributeError:
                # Column name might be aliased, skip for now
                # Subclasses can override to handle specific cases
                continue

            if isinstance(value, UUID):
                result[column.name] = str(value)
            elif hasattr(value, 'isoformat'):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    def update(self, **kwargs):
        # Handle metadata field if present (for compatibility)
        if "metadata" in kwargs and hasattr(self, '_get_metadata_field_name'):
            metadata_field = self._get_metadata_field_name()
            if metadata_field:
                kwargs[metadata_field] = kwargs.pop("metadata")
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"