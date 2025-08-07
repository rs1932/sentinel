# RBAC Implementation Plan

## Current Problem: Hardcoded Scopes

The authentication system currently uses hardcoded scopes in `authentication.py:376`:

```python
def _get_user_scopes(self, user: User) -> List[str]:
    # TODO: Implement proper role-based scope resolution
    # Hardcoded scopes based on user type only
```

**Issues:**
- All tenant admins have identical permissions
- No customization per tenant or department
- Can't create granular roles like "HR Manager" or "Finance Read-Only"

## Solution: Database-Driven RBAC

### Phase 1: Permission Model (Module 6)
Create permission tables to store granular permissions:

```python
class Permission(BaseModel):
    __tablename__ = "permissions"
    
    name = Column(String(100))          # "user:read", "tenant:admin"
    resource = Column(String(50))       # "user", "tenant", "role"
    action = Column(String(50))         # "read", "write", "admin"
    scope = Column(String(50))          # "tenant", "global"
    description = Column(Text)

class RolePermission(BaseModel):
    __tablename__ = "role_permissions"
    
    role_id = Column(UUID, ForeignKey('roles.id'))
    permission_id = Column(UUID, ForeignKey('permissions.id'))
```

### Phase 2: Group Model (Module 5)
Add group support for department-based roles:

```python
class Group(BaseModel):
    __tablename__ = "groups"
    
    tenant_id = Column(UUID, ForeignKey('tenants.id'))
    name = Column(String(100))          # "HR", "Finance", "Engineering"
    description = Column(Text)

class UserGroup(BaseModel):
    user_id = Column(UUID, ForeignKey('users.id'))
    group_id = Column(UUID, ForeignKey('groups.id'))

class GroupRole(BaseModel):
    group_id = Column(UUID, ForeignKey('groups.id'))
    role_id = Column(UUID, ForeignKey('roles.id'))
```

### Phase 3: Dynamic Scope Resolution
Replace hardcoded `_get_user_scopes()` with database queries:

```python
async def _get_user_scopes(self, user: User) -> List[str]:
    """Get user permissions from roles and groups"""
    scopes = set()
    
    # 1. Direct role assignments
    user_roles = await self._get_user_roles(user.id)
    for role in user_roles:
        role_permissions = await self._get_role_permissions(role.id)
        scopes.update([p.name for p in role_permissions])
    
    # 2. Group-based role assignments  
    user_groups = await self._get_user_groups(user.id)
    for group in user_groups:
        group_roles = await self._get_group_roles(group.id)
        for role in group_roles:
            role_permissions = await self._get_role_permissions(role.id)
            scopes.update([p.name for p in role_permissions])
    
    # 3. Handle role inheritance
    scopes = await self._resolve_inherited_permissions(scopes, user_roles)
    
    return list(scopes)
```

## Implementation Benefits

### 1. Flexible Role Creation
```python
# Create custom roles per tenant
hr_manager = Role(
    tenant_id=tenant.id,
    name="HR Manager",
    type=RoleType.CUSTOM
)

# Assign specific permissions
permissions = [
    "user:read", "user:write",        # Can manage users
    "role:read",                      # Can view roles
    "tenant:read"                     # Can view tenant info
]
```

### 2. Department-Based Access
```python
# HR group gets HR Manager role
hr_group = Group(name="Human Resources", tenant_id=tenant.id)
GroupRole(group_id=hr_group.id, role_id=hr_manager.id)

# All HR users automatically get HR Manager permissions
UserGroup(user_id=hr_user.id, group_id=hr_group.id)
```

### 3. Hierarchical Inheritance
```python
# Manager role inherits from Employee role
employee_role = Role(name="Employee", permissions=["user:profile", "tenant:read"])
manager_role = Role(name="Manager", parent_role_id=employee_role.id, 
                   permissions=["user:read", "user:write"])
# Manager gets: user:profile, tenant:read, user:read, user:write
```

### 4. Super Admin via Roles
```python
# Replace hardcoded super admin detection
platform_admin_role = Role(
    name="Platform Administrator",
    tenant_id=PLATFORM_TENANT_ID,
    type=RoleType.SYSTEM,
    permissions=[
        "platform:admin", "system:admin", "audit:read", "audit:write",
        "tenant:global", "user:global", "role:global"
    ]
)
```

## Migration Strategy

### Step 1: Add Permission & Group Models
- Create migration for permissions, groups tables
- Populate with current hardcoded permissions
- Create default system roles

### Step 2: Migrate Existing Users  
- Create default roles: "Super Admin", "Tenant Admin", "User"
- Assign roles based on current user type logic
- Preserve existing functionality

### Step 3: Update Authentication Service
- Replace `_get_user_scopes()` with database queries
- Add caching for performance
- Maintain backward compatibility

### Step 4: Enable Custom Role Management
- Add role/permission management APIs
- Create admin UI for role assignment
- Documentation for custom role creation

## Database Schema Changes Required

```sql
-- Permissions table
CREATE TABLE sentinel.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    scope VARCHAR(50) DEFAULT 'tenant',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name)
);

-- Role-Permission junction
CREATE TABLE sentinel.role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES sentinel.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES sentinel.permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(role_id, permission_id)
);

-- Groups table
CREATE TABLE sentinel.groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

-- User-Group junction
CREATE TABLE sentinel.user_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES sentinel.groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, group_id)
);

-- Group-Role junction
CREATE TABLE sentinel.group_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES sentinel.groups(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES sentinel.roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(group_id, role_id)
);
```

## Performance Considerations

### Caching Strategy
- Cache user permissions in Redis/memory
- Invalidate cache on role/permission changes
- Background refresh for frequently accessed users

### Query Optimization
- Use database views for complex permission queries
- Index foreign keys properly
- Consider materialized views for large tenants

## Next Steps

1. **Complete Modules 5 & 6**: Add Group and Permission models
2. **Create Migration**: Add new tables and populate defaults
3. **Update Authentication**: Replace hardcoded scopes with DB queries  
4. **Add Management APIs**: Allow role/permission customization
5. **Performance Optimization**: Add caching and query optimization

This will transform your system from rigid hardcoded permissions to a flexible, tenant-customizable RBAC system while leveraging your existing role infrastructure.