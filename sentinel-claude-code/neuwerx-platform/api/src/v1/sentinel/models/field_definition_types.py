"""
Enums and types for field definitions to avoid circular imports
"""
from enum import Enum


class FieldType(str, Enum):
    """Field type enumeration for three-tier model."""
    CORE = "core"
    PLATFORM_DYNAMIC = "platform_dynamic"
    TENANT_SPECIFIC = "tenant_specific"


class FieldDataType(str, Enum):
    """Field data type enumeration."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    ARRAY = "array"
    EMAIL = "email"
    URL = "url"
    UUID = "uuid"
    TEXT = "text"


class FieldPermission(str, Enum):
    """Field permission enumeration matching database enum."""
    READ = "read"
    WRITE = "write"
    HIDDEN = "hidden"