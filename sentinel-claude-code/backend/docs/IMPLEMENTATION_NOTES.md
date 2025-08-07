# Implementation Notes

## Important Design Decisions and Fixes

### 1. Metadata Column Naming (System-wide Pattern)

**Problem**: SQLAlchemy and Pydantic reserve the attribute name `metadata` for their own use. Having columns named `metadata` in the database creates conflicts.

**Solution**: 
- Database columns are named `{table}_metadata` (e.g., `tenant_metadata`, `role_metadata`, `group_metadata`)
- Created a `MetadataMixin` class that handles the mapping automatically
- The mixin's methods map API `metadata` ↔ database `{table}_metadata`
- Models inherit from `MetadataMixin` to get this functionality

**Implementation**:
- `src/models/mixins.py` - Contains the `MetadataMixin` class
- Each model with metadata inherits from this mixin
- The mixin provides `__init__`, `__getattr__`, `__setattr__`, and `to_dict` methods

**Tables with renamed metadata columns**:
- `sentinel.tenants` → `tenant_metadata`
- `sentinel.roles` → `role_metadata`
- `sentinel.groups` → `group_metadata`
- `sentinel.audit_logs` → `audit_metadata`
- `sentinel.menu_items` → `menu_metadata`

**Example**:
```python
# Model definition
class Tenant(MetadataMixin, BaseModel):
    tenant_metadata = Column(JSON, default=dict)  # Database column

# API request (uses 'metadata')
{
    "name": "Test Tenant",
    "metadata": {"key": "value"}  # API uses 'metadata'
}

# Internal access (both work)
tenant.metadata  # Returns tenant_metadata via __getattr__
tenant.tenant_metadata  # Direct access to column

# API response (uses 'metadata')
{
    "name": "Test Tenant",
    "metadata": {"key": "value"}  # API response uses 'metadata'
}
```

This pattern ensures consistency across all models and maintains clean API interfaces while avoiding framework conflicts.

### 2. Database Schema Approach

**Decision**: Use the complete SQL schema file (`docs/Sentinel_Schema_All_Tables.sql`) to create all tables at once, rather than incremental migrations per module.

**Rationale**:
- Ensures all foreign key relationships are properly established
- Avoids migration conflicts between modules
- Maintains consistency with the provided database design
- Simplifies deployment and testing

**Process**:
1. Run the complete SQL schema to create all tables
2. Build modules to work with the existing schema
3. Use Alembic only for future schema changes after initial setup

### 3. Python Version Requirement

**Requirement**: Python 3.10 (not 3.11 or 3.12)

**Reason**: As specified in the instructions, there are installation issues with newer Python versions for some dependencies.

### 4. Redis Configuration

**Decision**: Redis is disabled by default (`REDIS_ENABLED=false`)

**Implementation**:
- Uses in-memory cache when Redis is disabled
- Cache service factory pattern allows easy switching
- Production environments should enable Redis for better performance

### 5. Module Development Order

**Approach**: Dependency-ordered incremental development

**Order**:
1. Tenants (foundation for multi-tenancy)
2. Authentication (requires tenant context)
3. Users & Service Accounts (requires auth)
4. Roles, Groups, Permissions (requires users)
5. Resources and subsequent modules

Each module must be fully functional and tested before proceeding to the next.