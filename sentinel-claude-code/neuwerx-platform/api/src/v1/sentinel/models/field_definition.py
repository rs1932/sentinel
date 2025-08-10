"""
Field Definition model for Module 8: Three-tier field management
"""
from sqlalchemy import Column, String, Text, Boolean, UUID, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import relationship, validates
from typing import Dict, Any

from .base import BaseModel
from .field_definition_types import FieldType, FieldDataType, FieldPermission


class FieldDefinition(BaseModel):
    """
    Field Definition model for three-tier field management.

    Supports three field types:
    - core: Fields with dedicated database columns
    - platform_dynamic: Dynamic fields stored in JSON (platform-wide)
    - tenant_specific: Dynamic fields stored in JSON (tenant-specific)
    """
    __tablename__ = "field_definitions"
    __table_args__ = (
        CheckConstraint(
            '(field_type = \'core\' AND storage_column IS NOT NULL) OR '
            '(field_type IN (\'platform_dynamic\', \'tenant_specific\') AND storage_path IS NOT NULL)',
            name='check_field_type_storage'
        ),
        {'schema': 'sentinel'}
    )

    # Tenant relationship (nullable for platform-wide fields)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey('sentinel.tenants.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )

    # Field identification
    entity_type = Column(String(100), nullable=False, index=True)  # e.g., 'vessel', 'container'
    field_name = Column(String(100), nullable=False)
    field_type = Column(String(50), nullable=False, index=True)  # core, platform_dynamic, tenant_specific
    data_type = Column(String(50), nullable=False)

    # Storage configuration
    storage_column = Column(String(100), nullable=True)  # For core fields
    storage_path = Column(String(255), nullable=True)   # JSON path for dynamic fields

    # Display configuration
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Validation and permissions
    validation_rules = Column(JSONB, default={}, nullable=False)
    default_visibility = Column(
        ENUM('read', 'write', 'hidden', name='field_permission', schema='sentinel', create_type=False),
        default='read',
        nullable=False
    )

    # Configuration flags
    is_indexed = Column(Boolean, default=False, nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit fields (already inherited from BaseModel: id, created_at, updated_at)

    # Relationships
    tenant = relationship("Tenant", back_populates="field_definitions")

    # Note: Unique constraint handled by database unique index with COALESCE

    @validates('field_type')
    def validate_field_type(self, key, field_type_value):
        """Validate field type."""
        if isinstance(field_type_value, str):
            if field_type_value not in [e.value for e in FieldType]:
                raise ValueError(f"Invalid field type: {field_type_value}")
            return field_type_value
        return field_type_value.value if isinstance(field_type_value, FieldType) else field_type_value

    @validates('data_type')
    def validate_data_type(self, key, data_type_value):
        """Validate data type."""
        if isinstance(data_type_value, str):
            if data_type_value not in [e.value for e in FieldDataType]:
                raise ValueError(f"Invalid data type: {data_type_value}")
            return data_type_value
        return data_type_value.value if isinstance(data_type_value, FieldDataType) else data_type_value

    @validates('default_visibility')
    def validate_default_visibility(self, key, visibility_value):
        """Validate default visibility."""
        if isinstance(visibility_value, str):
            try:
                # Ensure the string value is valid and return as string (not enum instance)
                FieldPermission(visibility_value)
                return visibility_value
            except ValueError:
                raise ValueError(f"Invalid field permission: {visibility_value}")
        elif isinstance(visibility_value, FieldPermission):
            return visibility_value.value
        return visibility_value

    def __repr__(self) -> str:
        return (f"<FieldDefinition(id='{self.id}', entity_type='{self.entity_type}', "
                f"field_name='{self.field_name}', field_type='{self.field_type}')>")

    def to_dict(self) -> dict:
        """Convert field definition to dictionary representation."""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id) if self.tenant_id else None,
            'entity_type': self.entity_type,
            'field_name': self.field_name,
            'field_type': self.field_type,
            'data_type': self.data_type,
            'storage_column': self.storage_column,
            'storage_path': self.storage_path,
            'display_name': self.display_name,
            'description': self.description,
            'validation_rules': self.validation_rules,
            'default_visibility': (self.default_visibility.value
                                   if isinstance(self.default_visibility, FieldPermission)
                                   else self.default_visibility),
            'is_indexed': self.is_indexed,
            'is_required': self.is_required,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_platform_wide(self) -> bool:
        """Check if this is a platform-wide field definition."""
        return self.tenant_id is None

    def is_tenant_specific(self) -> bool:
        """Check if this is a tenant-specific field definition."""
        return self.tenant_id is not None

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information based on field type."""
        if self.field_type == FieldType.CORE.value:
            return {
                'type': 'column',
                'location': self.storage_column,
                'path': None
            }
        else:
            location = ('custom_attributes' if self.field_type == FieldType.PLATFORM_DYNAMIC.value
                        else 'tenant_attributes')
            return {
                'type': 'json',
                'location': location,
                'path': self.storage_path
            }

    def validate_storage_configuration(self) -> bool:
        """Validate that storage configuration is correct for field type."""
        if self.field_type == FieldType.CORE.value:
            return self.storage_column is not None and self.storage_path is None
        else:
            return self.storage_path is not None and self.storage_column is None

    @property
    def full_field_path(self) -> str:
        """Get the full field path for JSON storage."""
        if self.field_type == FieldType.CORE.value:
            return self.field_name
        elif self.field_type == FieldType.PLATFORM_DYNAMIC.value:
            return f"custom_attributes.{self.field_name}"
        else:  # tenant_specific
            return f"tenant_attributes.{self.field_name}"
