"""
Database-agnostic type utilities for SQLAlchemy models
"""
from sqlalchemy import TypeDecorator, String, Text, event
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, ARRAY as PostgreSQLArray, JSONB as PostgreSQLJSONB
from sqlalchemy.engine import Engine
import uuid
import sqlite3
import json


class UUID(TypeDecorator):
    """
    Platform-independent UUID type.
    Uses PostgreSQL's UUID type when available, 
    otherwise uses String(36) for SQLite.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif dialect.name == 'postgresql':
            return value
        else:
            # For SQLite, convert UUID to string
            if isinstance(value, UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        elif dialect.name == 'postgresql':
            return value
        else:
            # For SQLite, convert string back to UUID
            if isinstance(value, str):
                return UUID(value)
            return value


class ARRAY(TypeDecorator):
    """
    Platform-independent ARRAY type.
    Uses PostgreSQL's ARRAY type when available,
    otherwise uses JSON for SQLite.
    """
    impl = Text
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        self.item_type = item_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLArray(self.item_type))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif dialect.name == 'postgresql':
            return value
        else:
            # For SQLite, convert list to JSON string
            if isinstance(value, list):
                return json.dumps(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        elif dialect.name == 'postgresql':
            return value
        else:
            # For SQLite, convert JSON string back to list
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return []
            return value if isinstance(value, list) else []


class JSONB(TypeDecorator):
    """
    Platform-independent JSONB type.
    Uses PostgreSQL's JSONB type when available,
    otherwise uses TEXT for SQLite.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLJSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif dialect.name == 'postgresql':
            return value
        else:
            # For SQLite, convert dict/list to JSON string
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        elif dialect.name == 'postgresql':
            return value
        else:
            # For SQLite, convert JSON string back to dict/list
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return {}
            return value if isinstance(value, (dict, list)) else {}


# Enable UUID support for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        # Enable foreign key support
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()