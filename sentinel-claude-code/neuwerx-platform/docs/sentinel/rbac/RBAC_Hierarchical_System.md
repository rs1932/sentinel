# Hierarchical RBAC System Documentation

## Overview

The Sentinel platform implements a comprehensive Role-Based Access Control (RBAC) system with hierarchical resource management. This system provides database-driven, dynamic permission resolution with fail-secure principles and support for complex organizational structures.

## Architecture

### Core Components

1. **Dynamic RBAC Service** (`src/services/rbac_service.py`)
2. **Authentication Service** with RBAC integration (`src/services/authentication.py`)
3. **Hierarchical Resource Model** (`src/models/resource.py`)
4. **Permission Model** (`src/models/permission.py`)
5. **Role and User Management Models**

### Key Features

- **Database-driven permissions**: No hardcoded scopes in production
- **Fail-secure principle**: Denies access when permission resolution fails
- **Hierarchical resources**: Product Family → App → Capability → Service → Entity/Page/API
- **Resource-specific permissions**: Fine-grained access control at any hierarchy level
- **Role inheritance**: Parent roles pass permissions to child roles
- **Group-based assignments**: Users can inherit roles through group membership
- **Performance caching**: Configurable permission caching for performance
- **Comprehensive auditing**: Full permission resolution tracking

## Resource Hierarchy Structure

```
Product Family (e.g., Maritime Logistics Platform)
├── App (e.g., Port Operations)
│   ├── Capability (e.g., Vessel Management)
│   │   ├── Service (e.g., Vessel Tracking Service)
│   │   │   ├── Entity (e.g., Vessel Entity)
│   │   │   ├── Page (e.g., Vessel Dashboard)
│   │   │   └── API (e.g., Vessel API)
│   │   └── ... (other services)
│   └── ... (other capabilities)
└── ... (other apps)
```

### Resource Types

- **product_family**: Top-level product grouping
- **app**: Application within a product family
- **capability**: Feature set within an application
- **service**: Backend service or microservice
- **entity**: Data entity or database table
- **page**: UI page or screen
- **api**: REST API endpoint or service

## Permission System

### Permission Structure

```json
{
  "id": "uuid",
  "name": "Vessel Management Access",
  "resource_type": "capability",
  "resource_id": "vessel-mgmt-uuid",
  "actions": ["read", "execute"],
  "conditions": {},
  "field_permissions": {}
}
```

### Available Actions

- **create**: Create new resources
- **read**: View/access resources
- **update**: Modify existing resources
- **delete**: Remove resources
- **execute**: Run operations/services
- **approve**: Approve workflows
- **reject**: Reject workflows

### Permission Types

1. **General Permissions**: Apply to all resources of a type
   ```sql
   resource_type = 'entity', resource_id = NULL
   -- Grants access to all entities
   ```

2. **Resource-Specific Permissions**: Apply to specific resources
   ```sql
   resource_type = 'entity', resource_id = 'vessel-entity-uuid'
   -- Grants access only to vessel entity
   ```

## RBAC Service Implementation

### Core Methods

#### `get_user_scopes(user: User) -> List[str]`
Main method that replaces hardcoded permission resolution.

```python
# Example usage
rbac_service = await RBACServiceFactory.create(db)
scopes = await rbac_service.get_user_scopes(user)
# Returns: ['entity:read', 'entity:update', 'api:execute:vessel-api-uuid']
```

#### Permission Resolution Flow

1. **Superadmin Check**: Users with `attributes.role = 'superadmin'` get full access
2. **Direct Roles**: Get roles directly assigned to user
3. **Group Roles**: Get roles inherited through group membership
4. **Role Inheritance**: Resolve parent role permissions
5. **Permission Collection**: Gather all permissions from resolved roles
6. **Scope Generation**: Convert permissions to scope strings
7. **Conflict Resolution**: Apply priority-based conflict resolution
8. **Caching**: Cache results for performance

### Scope Format

- **General**: `{resource_type}:{action}` (e.g., `entity:read`)
- **Resource-specific**: `{resource_type}:{action}:{resource_id}` (e.g., `entity:read:vessel-uuid`)

## Security Features

### Fail-Secure Principle

The system implements strict fail-secure behavior:

```python
try:
    scopes = await self._resolve_user_permissions(user)
    return scopes
except Exception as e:
    logger.error(f"Error resolving user scopes for {user.id}: {e}")
    # SECURITY: Fail secure - deny all access if RBAC resolution fails
    logger.warning(f"RBAC resolution failed for user {user.id}. Denying all access for security.")
    return []  # Return empty scopes - no permissions
```

### Dynamic RBAC Configuration

```python
# Enable/disable dynamic RBAC via environment variable
USE_DYNAMIC_RBAC = os.getenv("USE_DYNAMIC_RBAC", "true").lower() == "true"
```

When disabled, the system falls back to hardcoded scopes for development/testing only.

## Database Schema

### Key Tables

#### Resources
```sql
CREATE TABLE sentinel.resources (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id),
    type resource_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(100) NOT NULL,
    parent_id UUID REFERENCES sentinel.resources(id),
    path TEXT, -- Materialized path for hierarchy queries
    attributes JSONB DEFAULT '{}',
    workflow_enabled BOOLEAN DEFAULT FALSE,
    workflow_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Permissions
```sql
CREATE TABLE sentinel.permissions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id),
    name VARCHAR(255) NOT NULL,
    resource_type resource_type NOT NULL,
    resource_id UUID REFERENCES sentinel.resources(id),
    resource_path TEXT,
    actions permission_action[] NOT NULL,
    conditions JSONB,
    field_permissions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Role Permissions
```sql
CREATE TABLE sentinel.role_permissions (
    id UUID PRIMARY KEY,
    role_id UUID NOT NULL REFERENCES sentinel.roles(id),
    permission_id UUID NOT NULL REFERENCES sentinel.permissions(id),
    granted_by UUID REFERENCES sentinel.users(id),
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(role_id, permission_id)
);
```

## Testing Results

### Test Scenarios Completed

1. **Superadmin Access**: Platform admin gets full access (33 scopes)
2. **Role-based Access**: Maritime users get role-specific permissions
3. **Fail-secure Behavior**: Users without roles get 0 scopes
4. **Hierarchical Permissions**: Permissions can be assigned at any hierarchy level
5. **Resource-specific Access**: Fine-grained control over specific resources

### Test Data Structure

```
Maritime Logistics Platform (Product Family)
└── Port Operations (App)
    └── Vessel Management (Capability)
        └── Vessel Tracking Service (Service)
            ├── Vessel Dashboard (Page)
            ├── Vessel Entity (Entity)
            └── Vessel API (API)
```

### User Test Results

| User | Role | Scopes | Access Level |
|------|------|--------|-------------|
| `admin@sentinel.com` | Superadmin (attribute) | 33 | Full platform |
| `port.manager@maritime.com` | Test Manager | 3 | Entity permissions |
| `vessel.coord@maritime.com` | Test Manager | 3 | Entity permissions |
| `dock.worker@maritime.com` | None | 0 | No access (fail-secure) |

## Usage Examples

### Creating Hierarchical Resources

```python
# Create product family
product_family = Resource(
    tenant_id=tenant_id,
    type=ResourceType.PRODUCT_FAMILY,
    name="Maritime Logistics Platform",
    code="maritime-logistics",
    attributes={"description": "Complete maritime operations management platform"}
)

# Create app under product family
app = Resource(
    tenant_id=tenant_id,
    type=ResourceType.APP,
    name="Port Operations",
    code="port-ops",
    parent_id=product_family.id,
    attributes={"description": "Port operations management application"}
)
```

### Creating Permissions

```python
# General entity permission
entity_permission = Permission(
    tenant_id=tenant_id,
    name="Entity Read Access",
    resource_type="entity",
    resource_id=None,  # General permission
    actions=["read"]
)

# Resource-specific permission
vessel_permission = Permission(
    tenant_id=tenant_id,
    name="Vessel Entity Access",
    resource_type="entity",
    resource_id=vessel_entity_id,  # Specific resource
    actions=["read", "update"]
)
```

### Assigning Permissions to Roles

```python
# Create role permission assignment
role_permission = RolePermission(
    role_id=manager_role_id,
    permission_id=entity_permission.id,
    granted_by=admin_user_id
)
```

### Checking User Permissions

```python
# Get user scopes
rbac_service = await RBACServiceFactory.create(db)
scopes = await rbac_service.get_user_scopes(user)

# Check specific permission
has_access = "entity:read" in scopes
has_vessel_access = f"entity:read:{vessel_id}" in scopes
```

## Performance Considerations

### Caching

The system implements multi-level caching:

1. **User Scope Cache**: Cache resolved scopes per user (5min TTL)
2. **Role Permission Cache**: Cache role permissions
3. **Inheritance Cache**: Cache resolved role hierarchies

### Database Optimization

1. **Materialized Paths**: Efficient hierarchy queries using path strings
2. **Indexed Lookups**: Proper indexing on tenant_id, user_id, role_id
3. **Batch Operations**: Minimize database queries during resolution

## Monitoring and Auditing

### Performance Statistics

```python
stats = rbac_service.get_stats()
# Returns: {
#   "cache_hits": 150,
#   "cache_misses": 50,
#   "db_queries": 25,
#   "permission_resolutions": 200
# }
```

### Detailed Permission Information

```python
details = await rbac_service.get_effective_permissions(user_id)
# Returns comprehensive permission breakdown for debugging/auditing
```

## Security Best Practices

1. **Never hardcode permissions**: Always use database-driven resolution
2. **Implement fail-secure**: Deny access on errors, never grant fallback permissions
3. **Regular permission audits**: Use `get_effective_permissions()` for auditing
4. **Cache invalidation**: Properly invalidate caches when permissions change
5. **Least privilege**: Assign minimal required permissions
6. **Resource specificity**: Use resource-specific permissions for sensitive operations

## Migration from Hardcoded Scopes

### Environment Configuration

```bash
# Enable dynamic RBAC (production)
USE_DYNAMIC_RBAC=true

# Disable for development/testing only
USE_DYNAMIC_RBAC=false
```

### Gradual Migration Steps

1. **Phase 1**: Run both systems in parallel
2. **Phase 2**: Compare results and fix discrepancies
3. **Phase 3**: Switch to dynamic-only with fallback logging
4. **Phase 4**: Remove hardcoded scopes entirely

## Troubleshooting

### Common Issues

1. **Empty scopes for valid users**:
   - Check role assignments in `user_roles` table
   - Verify role has permissions in `role_permissions` table
   - Check permission `is_active` status

2. **Performance issues**:
   - Enable caching via `RBACServiceFactory.create(db, use_cache=True)`
   - Monitor cache hit/miss ratios
   - Consider denormalizing frequently accessed permissions

3. **Permission resolution errors**:
   - Check database connectivity
   - Verify schema integrity
   - Review error logs for SQL issues

### Debug Commands

```python
# Get detailed permission breakdown
details = await rbac_service.get_effective_permissions(user_id)

# Check cache performance
stats = rbac_service.get_stats()

# Invalidate user cache
await rbac_service.invalidate_user_cache(user_id)
```

## Future Enhancements

1. **Conditional Permissions**: Implement dynamic conditions based on context
2. **Time-based Permissions**: Add temporal constraints to permissions  
3. **Delegation**: Allow users to delegate permissions to others
4. **Permission Requests**: Workflow for requesting additional permissions
5. **Advanced Caching**: Redis-based distributed caching for multi-instance deployments