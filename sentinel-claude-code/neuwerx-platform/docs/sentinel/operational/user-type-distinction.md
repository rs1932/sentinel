# User Type Distinction System

This document explains how the Sentinel Platform distinguishes between different user types and their permission levels.

## User Types Overview

The system recognizes three primary user types:
1. **Super Admin** - Global system administrators
2. **Tenant Admin** - Administrators within a specific tenant
3. **Regular User** - Standard users within a tenant

## Detection Mechanism

The system determines user type through a combination of database attributes and business logic during authentication.

### 1. Database Attributes

#### User Model Fields
```python
class User:
    tenant_id: UUID           # Links user to their tenant
    is_service_account: bool  # Distinguishes service accounts
    is_active: bool          # Account status
    email: str               # User identifier
```

#### Tenant Model Fields
```python
class Tenant:
    id: UUID                 # Tenant identifier
    code: str               # Human-readable tenant code
    name: str               # Tenant display name
```

### 2. Business Logic Detection

The detection happens in the `AuthenticationService._get_user_scopes()` method:

```python
def _get_user_scopes(self, user: User) -> List[str]:
    # Step 1: Check if user is on PLATFORM tenant (Super Admin)
    platform_tenant_id = "00000000-0000-0000-0000-000000000000"
    is_super_admin = str(user.tenant_id) == platform_tenant_id
    
    # Step 2: Check service account flag
    if user.is_service_account:
        return [...service_account_scopes...]
    
    # Step 3: Super Admin gets global scopes
    elif is_super_admin:
        return [...global_scopes...]
    
    # Step 4: Regular users get tenant-scoped permissions
    else:
        return [...tenant_scoped_scopes...]
```

## User Type Characteristics

### Super Admin
**Detection Criteria:**
- `user.tenant_id == "00000000-0000-0000-0000-000000000000"` (PLATFORM tenant)
- `user.is_service_account == False`

**Capabilities:**
- Access to ALL tenants in the system
- Global resource management (users, tenants, roles across all tenants)
- System-level administration
- Audit log access
- Platform configuration

**JWT Token Scopes (21 total):**
```
user:profile
platform:admin          # Exclusive to super admin
tenant:read, tenant:write, tenant:admin, tenant:global  # :global exclusive
user:read, user:write, user:admin, user:global          # :global exclusive  
service_account:read, service_account:write, service_account:admin, service_account:global  # :global exclusive
role:read, role:write, role:admin, role:global          # :global exclusive
system:admin             # Exclusive to super admin
audit:read, audit:write  # Exclusive to super admin
```

### Tenant Admin
**Detection Criteria:**
- `user.tenant_id != "00000000-0000-0000-0000-000000000000"` (Not PLATFORM tenant)
- `user.is_service_account == False`
- Has admin-level scopes within their tenant

**Capabilities:**
- Full administrative access within their tenant only
- Can manage users, roles, service accounts within their tenant
- Cannot access other tenants
- Cannot perform system-level operations

**JWT Token Scopes (7 total):**
```
user:profile
tenant:read, tenant:write, tenant:admin      # Tenant-scoped only
user:read, user:write, user:admin           # Tenant-scoped only
service_account:read, service_account:write, service_account:admin  # Tenant-scoped
role:read, role:write, role:admin           # Tenant-scoped only
```

### Regular User
**Detection Criteria:**
- `user.tenant_id != "00000000-0000-0000-0000-000000000000"` (Not PLATFORM tenant)
- `user.is_service_account == False`
- Has basic user scopes

**Capabilities:**
- Access to their own profile
- Limited read access to tenant resources
- Cannot perform administrative operations
- Cannot access other tenants

**JWT Token Scopes (7 total):**
```
user:profile
tenant:read, tenant:write, tenant:admin      # Same as tenant admin currently
user:read, user:write, user:admin           # Same as tenant admin currently
service_account:read, service_account:write, service_account:admin
role:read, role:write, role:admin
```
*Note: The current implementation grants admin-level scopes to all regular users. This will be refined when role-based access control is implemented.*

### Service Account
**Detection Criteria:**
- `user.is_service_account == True`
- Any tenant (including PLATFORM)

**Capabilities:**
- API access for automated systems
- No web interface access
- Scoped permissions based on service account configuration

## Authentication Flow

### 1. Login Request
```json
{
  "email": "user@example.com",
  "password": "password123",
  "tenant_code": "TENANT_CODE"
}
```

### 2. User Resolution
1. Find tenant by `tenant_code`
2. Find user by `email` + `tenant_id`
3. Verify password and account status

### 3. Scope Assignment
1. Check if `user.tenant_id == PLATFORM_TENANT_ID`
2. Check if `user.is_service_account == True`
3. Assign appropriate scopes based on user type

### 4. JWT Token Generation
```json
{
  "sub": "user_id",
  "tenant_id": "tenant_id",
  "tenant_code": "TENANT_CODE",
  "email": "user@example.com",
  "is_service_account": false,
  "scopes": ["scope1", "scope2", ...],
  "session_id": "session_id"
}
```

## Scope-Based Authorization

### Global vs Tenant-Scoped Permissions

#### Global Scopes (Super Admin Only)
- `platform:admin` - Platform-wide administration
- `tenant:global` - Access to all tenants
- `user:global` - Manage users across all tenants
- `service_account:global` - Manage service accounts across all tenants
- `role:global` - Manage roles across all tenants
- `system:admin` - System configuration
- `audit:read`, `audit:write` - Audit log access

#### Tenant-Scoped Permissions
- `tenant:read/write/admin` - Limited to user's tenant
- `user:read/write/admin` - Limited to user's tenant
- `service_account:read/write/admin` - Limited to user's tenant
- `role:read/write/admin` - Limited to user's tenant

## API Endpoint Authorization

Endpoints check JWT token scopes to determine access:

```python
# Example: Tenant management endpoint
@require_scope("tenant:admin")  # Tenant admin can access
@require_scope("tenant:global") # Super admin can access (global override)
def get_tenant_users(tenant_id: str):
    # Implementation
```

## Future Enhancements

### Role-Based Access Control (RBAC)
- Replace hardcoded scopes with database-driven roles
- Granular permission assignment
- Custom role creation per tenant

### Permission Hierarchy
- More nuanced permission levels between admin and user
- Department-based access controls
- Resource-specific permissions

### Multi-Factor Authentication
- Additional security layer for super admins
- Risk-based authentication
- Device trust management

## Troubleshooting User Types

### Check User Type via Database
```sql
-- Super Admin Check
SELECT u.email, t.code as tenant_code, u.is_service_account
FROM sentinel.users u
JOIN sentinel.tenants t ON u.tenant_id = t.id
WHERE t.code = 'PLATFORM' AND u.is_service_account = false;

-- Tenant Admin Check  
SELECT u.email, t.code as tenant_code, t.name as tenant_name
FROM sentinel.users u
JOIN sentinel.tenants t ON u.tenant_id = t.id
WHERE t.code != 'PLATFORM' AND u.is_service_account = false;
```

### Verify JWT Token Scopes
1. Decode JWT token using jwt.io or similar tool
2. Check `scopes` array in token payload
3. Look for `:global` suffixes (super admin indicator)
4. Verify `tenant_id` matches expected tenant

### Common Issues
1. **User appears as regular user instead of admin**: Check if user is on correct tenant
2. **Super admin lacks global access**: Verify user is on PLATFORM tenant with correct UUID
3. **Service account behaving like user**: Check `is_service_account` flag in database
4. **Cross-tenant access denied**: Confirm user has `:global` scopes in JWT token