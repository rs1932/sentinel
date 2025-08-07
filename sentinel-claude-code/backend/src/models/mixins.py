"""
Mixins for SQLAlchemy models to handle common patterns
"""

class MetadataMixin:
    """
    Mixin to handle metadata field mapping for API compatibility.
    
    Since 'metadata' is reserved by SQLAlchemy, we use {table}_metadata
    in the database but expose it as 'metadata' in the API.
    """
    
    def __init__(self, **kwargs):
        # Get the table-specific metadata field name
        metadata_field = self._get_metadata_field_name()
        
        # Handle API compatibility: map 'metadata' to '{table}_metadata'
        if "metadata" in kwargs and metadata_field:
            kwargs[metadata_field] = kwargs.pop("metadata")
        
        super().__init__(**kwargs)
    
    def _get_metadata_field_name(self):
        """Get the table-specific metadata field name"""
        # Map table names to their metadata field names
        table_name = self.__tablename__
        metadata_fields = {
            'tenants': 'tenant_metadata',
            'users': 'user_metadata',
            'roles': 'role_metadata',
            'groups': 'group_metadata',
            'audit_logs': 'audit_metadata',
            'menu_items': 'menu_metadata'
        }
        return metadata_fields.get(table_name)
    
    def __getattr__(self, name):
        """Provide API compatibility for metadata field"""
        if name == 'metadata':
            metadata_field = self._get_metadata_field_name()
            if metadata_field and hasattr(self, metadata_field):
                return getattr(self, metadata_field)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        """Provide API compatibility for metadata field"""
        if name == 'metadata':
            metadata_field = self._get_metadata_field_name()
            if metadata_field:
                super().__setattr__(metadata_field, value)
                return
        super().__setattr__(name, value)
    
    def to_dict(self):
        """Convert model to dictionary with metadata mapping"""
        result = super().to_dict() if hasattr(super(), 'to_dict') else {}
        
        # Handle API compatibility: map '{table}_metadata' to 'metadata'
        metadata_field = self._get_metadata_field_name()
        if metadata_field and metadata_field in result:
            result["metadata"] = result.pop(metadata_field)
        
        return result