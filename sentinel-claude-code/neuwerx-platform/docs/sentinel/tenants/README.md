# 🏢 Sentinel Tenant Management API Documentation

## Overview

The Sentinel Tenant Management API provides comprehensive tenant lifecycle management including tenant CRUD operations, hierarchical tenant structures, sub-tenant management, and tenant activation controls. This API is built on Module 2 and requires authentication for all operations.

**Base URL**: `http://localhost:8000/api/v1`  
**Authentication**: JWT Bearer token required for all endpoints  
**Multi-Tenant**: All operations respect tenant isolation and hierarchy  

## 📋 Quick Reference

### Tenant Management Endpoints

| Endpoint | Method | Purpose | Required Scope |
|----------|--------|---------|----------------|
| `/tenants/` | GET | List tenants with filtering | `tenant:read` |
| `/tenants/` | POST | Create new tenant | `tenant:admin` |
| `/tenants/{id}` | GET | Get tenant details | `tenant:read` |
| `/tenants/{id}` | PATCH | Update tenant | `tenant:write` |
| `/tenants/{id}` | DELETE | Delete tenant | `tenant:admin` |
| `/tenants/code/{code}` | GET | Get tenant by code | `tenant:read` |

### Hierarchical Operations

| Endpoint | Method | Purpose | Required Scope |
|----------|--------|---------|----------------|
| `/tenants/{id}/sub-tenants` | POST | Create sub-tenant | `tenant:admin` |
| `/tenants/{id}/hierarchy` | GET | Get tenant hierarchy | `tenant:read` |
| `/tenants/{id}/activate` | POST | Activate tenant | `tenant:admin` |
| `/tenants/{id}/deactivate` | POST | Deactivate tenant | `tenant:admin` |

## 🚀 Getting Started

### 1. Authentication Setup

All tenant endpoints require authentication. Include the JWT token in the Authorization header:

```javascript
const headers = {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
};
```

### 2. Basic Tenant Operations

```javascript
// List all tenants
const tenants = await fetch('http://localhost:8000/api/v1/tenants/', {
    headers
});

// Get specific tenant by ID
const tenant = await fetch('http://localhost:8000/api/v1/tenants/6ea84333-4d12-48ce-b869-8a63e35399c2', {
    headers
});

// Get tenant by code
const tenantByCode = await fetch('http://localhost:8000/api/v1/tenants/code/API-TEST-20250806162641', {
    headers
});
```

### 3. Tenant Creation

```javascript
// Create new root tenant
const newTenant = await fetch('http://localhost:8000/api/v1/tenants/', {
    method: 'POST',
    headers,
    body: JSON.stringify({
        name: 'Acme Corporation',
        code: 'ACME-CORP',
        type: 'root',
        isolation_mode: 'dedicated',
        settings: {
            theme: 'corporate',
            locale: 'en-US'
        },
        features: ['api_access', 'sso', 'advanced_audit'],
        metadata: {
            industry: 'Technology',
            size: 'Enterprise'
        }
    })
});
```

## 🔑 Key Features

- **Hierarchical Tenancy**: Support for root tenants and sub-tenants
- **Flexible Isolation**: Shared or dedicated isolation modes
- **Feature Management**: Granular feature enablement per tenant
- **Custom Settings**: JSON-based configuration storage
- **Metadata Support**: Extensible metadata for tenant attributes
- **Activation Control**: Enable/disable tenants without deletion
- **Code-based Lookup**: Fast tenant retrieval by unique codes
- **Advanced Filtering**: Search and filter tenants by multiple criteria

## 🔐 Permission Scopes

### Tenant Scopes
- `tenant:read` - View tenant information and hierarchies
- `tenant:write` - Update tenant information and settings
- `tenant:admin` - Full tenant management (create, delete, activate/deactivate)

## 📊 Data Models

### Tenant Object
```json
{
    "id": "uuid",
    "name": "Tenant Name",
    "code": "TENANT-CODE",
    "type": "root|sub_tenant",
    "parent_tenant_id": "uuid|null",
    "isolation_mode": "shared|dedicated", 
    "settings": {},
    "features": [],
    "metadata": {},
    "is_active": true,
    "created_at": "2025-08-07T18:30:00Z",
    "updated_at": "2025-08-07T18:30:00Z"
}
```

### Tenant Detail Object (with hierarchy)
```json
{
    "id": "uuid",
    "name": "Tenant Name",
    "code": "TENANT-CODE",
    "type": "root",
    "parent_tenant_id": null,
    "isolation_mode": "dedicated",
    "settings": {},
    "features": [],
    "metadata": {},
    "is_active": true,
    "sub_tenants_count": 3,
    "users_count": 150,
    "hierarchy": [],
    "created_at": "2025-08-07T18:30:00Z",
    "updated_at": "2025-08-07T18:30:00Z"
}
```

## 📁 Documentation Structure

- **[API Endpoints](./api-endpoints.md)** - Detailed endpoint specifications
- **[Frontend Integration](./frontend-integration.md)** - Frontend-specific integration examples
- **[Error Handling](./error-handling.md)** - Error codes and handling strategies

## ⚠️ Important Notes

### Security Considerations
1. **Token Required**: All endpoints require valid JWT authentication
2. **Scope Validation**: Operations are restricted by token scopes
3. **Tenant Isolation**: Users can only access their tenant and sub-tenants
4. **Admin Privileges**: Admin scopes required for sensitive operations
5. **Code Uniqueness**: Tenant codes must be globally unique

### Data Constraints
- **Name**: 1-255 characters, required
- **Code**: 1-50 characters, uppercase alphanumeric with hyphens, unique
- **Type**: Either 'root' or 'sub_tenant'
- **Features**: Must be from predefined allowed list
- **Isolation Mode**: Either 'shared' or 'dedicated'
- **Hierarchy**: Sub-tenants must have parent_tenant_id

### Business Rules
- **Root Tenants**: Cannot have a parent_tenant_id
- **Sub-Tenants**: Must have a valid parent_tenant_id
- **Code Format**: Must match pattern `^[A-Z0-9][A-Z0-9-]*$`
- **Soft Delete**: Deactivation preferred over hard deletion
- **Feature Inheritance**: Sub-tenants can inherit parent features

## 🛠️ Development Environment

- **Server**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/api/docs`
- **Test Authentication**: Use `/auth/login` to get access token
- **Test Tenant**: API-TEST-20250806162641 (for testing)

## 📞 Frontend Integration Tips

### Common Patterns
1. **Current Tenant Context**: Include tenant info in app state
2. **Hierarchical Display**: Show tenant trees with parent-child relationships  
3. **Feature Gating**: Use tenant features to enable/disable UI components
4. **Settings Management**: Provide UI for tenant configuration
5. **Code Validation**: Validate tenant codes client-side before submission

### Error Handling
- **403 Forbidden**: Insufficient permissions (check token scopes)
- **404 Not Found**: Tenant doesn't exist or no access
- **409 Conflict**: Tenant code already exists
- **422 Validation Error**: Invalid request data format

## 🔄 Typical Workflows

### Tenant Onboarding Flow
1. Admin creates root tenant with `POST /tenants/`
2. Configure tenant settings and features via `PATCH /tenants/{id}`
3. Create sub-tenants if needed with `POST /tenants/{id}/sub-tenants`
4. Activate tenant with `POST /tenants/{id}/activate`

### Multi-Tenant Navigation
1. Get current user's tenant from JWT token
2. Load tenant hierarchy with `GET /tenants/{id}/hierarchy`
3. Allow tenant switching (if user has access to multiple)
4. Filter data by selected tenant context

### Feature Management
1. Get tenant details to check enabled features
2. Enable/disable UI components based on feature flags
3. Update features via `PATCH /tenants/{id}` with new feature array
4. Validate feature dependencies before changes

---

*Last updated: 2025-08-07*  
*API Version: 1.0.0*