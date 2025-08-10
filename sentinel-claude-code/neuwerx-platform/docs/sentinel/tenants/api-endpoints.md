# 🔗 Tenant Management API Endpoints

## Core Tenant Operations

### GET /tenants/

**Purpose**: List tenants with filtering and pagination

**Required Scope**: `tenant:read`

#### Request
```http
GET /api/v1/tenants/?name=Acme&type=root&is_active=true&limit=50&offset=0
Authorization: Bearer <access_token>
```

#### Query Parameters
| Parameter | Type | Description | Default | Example |
|-----------|------|-------------|---------|---------|
| `name` | string | Filter by tenant name (partial match) | - | "Acme" |
| `code` | string | Filter by tenant code (partial match) | - | "ACME" |
| `type` | enum | Filter by type (root/sub_tenant) | - | "root" |
| `parent_tenant_id` | UUID | Filter by parent tenant | - | "uuid-here" |
| `is_active` | boolean | Filter by active status | - | true |
| `limit` | integer | Items per page (1-1000) | 100 | 50 |
| `offset` | integer | Items to skip (≥0) | 0 | 100 |

#### Response (200 OK)
```json
{
    "items": [
        {
            "id": "6ea84333-4d12-48ce-b869-8a63e35399c2",
            "name": "API Test Tenant",
            "code": "API-TEST-20250806162641",
            "type": "root",
            "parent_tenant_id": null,
            "isolation_mode": "shared",
            "settings": {
                "test": true
            },
            "features": [
                "api_access"
            ],
            "metadata": {
                "created_by": "test_script"
            },
            "is_active": true,
            "created_at": "2025-08-06T20:26:41.801330Z",
            "updated_at": "2025-08-06T20:26:41.801330Z"
        }
    ],
    "total": 3,
    "limit": 50,
    "offset": 0
}
```

---

### POST /tenants/

**Purpose**: Create a new tenant

**Required Scope**: `tenant:admin`

#### Request
```http
POST /api/v1/tenants/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Acme Corporation",
    "code": "ACME-CORP",
    "type": "root",
    "parent_tenant_id": null,
    "isolation_mode": "dedicated",
    "settings": {
        "theme": "corporate",
        "locale": "en-US",
        "timezone": "America/New_York"
    },
    "features": [
        "api_access",
        "sso",
        "advanced_audit",
        "multi_factor_auth"
    ],
    "metadata": {
        "industry": "Technology",
        "company_size": "Enterprise",
        "contract_type": "Annual"
    }
}
```

#### Request Fields
| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `name` | string | ✅ | Tenant display name | 1-255 characters |
| `code` | string | ✅ | Unique tenant identifier | 1-50 chars, uppercase alphanumeric + hyphens |
| `type` | enum | ✅ | Tenant type | "root" or "sub_tenant" |
| `parent_tenant_id` | UUID | ❌ | Parent tenant (required for sub_tenant) | Valid UUID or null |
| `isolation_mode` | enum | ❌ | Data isolation level | "shared" or "dedicated", default: "shared" |
| `settings` | object | ❌ | Custom tenant settings | JSON object |
| `features` | array | ❌ | Enabled feature flags | Array of valid feature strings |
| `metadata` | object | ❌ | Additional tenant metadata | JSON object |

#### Response (201 Created)
```json
{
    "id": "12345678-1234-1234-1234-123456789012",
    "name": "Acme Corporation",
    "code": "ACME-CORP",
    "type": "root",
    "parent_tenant_id": null,
    "isolation_mode": "dedicated",
    "settings": {
        "theme": "corporate",
        "locale": "en-US",
        "timezone": "America/New_York"
    },
    "features": [
        "api_access",
        "sso",
        "advanced_audit",
        "multi_factor_auth"
    ],
    "metadata": {
        "industry": "Technology",
        "company_size": "Enterprise",
        "contract_type": "Annual"
    },
    "is_active": true,
    "created_at": "2025-08-07T19:00:00Z",
    "updated_at": "2025-08-07T19:00:00Z"
}
```

#### Error Responses
- **409 Conflict**: Tenant code already exists
- **422 Validation Error**: Invalid request data or business rule violation
- **403 Forbidden**: Insufficient permissions

---

### GET /tenants/{tenant_id}

**Purpose**: Get detailed tenant information with hierarchy counts

**Required Scope**: `tenant:read`

#### Request
```http
GET /api/v1/tenants/6ea84333-4d12-48ce-b869-8a63e35399c2
Authorization: Bearer <access_token>
```

#### Response (200 OK)
```json
{
    "id": "6ea84333-4d12-48ce-b869-8a63e35399c2",
    "name": "API Test Tenant",
    "code": "API-TEST-20250806162641",
    "type": "root",
    "parent_tenant_id": null,
    "isolation_mode": "shared",
    "settings": {
        "test": true
    },
    "features": [
        "api_access"
    ],
    "metadata": {
        "created_by": "test_script"
    },
    "is_active": true,
    "sub_tenants_count": 2,
    "users_count": 45,
    "hierarchy": [],
    "created_at": "2025-08-06T20:26:41.801330Z",
    "updated_at": "2025-08-06T20:26:41.801330Z"
}
```

#### Error Responses
- **404 Not Found**: Tenant doesn't exist or no access
- **403 Forbidden**: Insufficient permissions

---

### PATCH /tenants/{tenant_id}

**Purpose**: Update tenant information

**Required Scope**: `tenant:write`

#### Request
```http
PATCH /api/v1/tenants/6ea84333-4d12-48ce-b869-8a63e35399c2
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Updated Tenant Name",
    "settings": {
        "theme": "dark",
        "locale": "en-US",
        "new_setting": "value"
    },
    "features": [
        "api_access",
        "sso",
        "advanced_audit"
    ],
    "metadata": {
        "updated_reason": "Feature upgrade",
        "version": 2
    },
    "is_active": true
}
```

#### Request Fields (All Optional)
| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| `name` | string | Update tenant name | 1-255 characters |
| `settings` | object | Replace tenant settings | Completely replaces existing |
| `features` | array | Replace enabled features | Must be from allowed list |
| `metadata` | object | Replace metadata | Completely replaces existing |
| `is_active` | boolean | Activate/deactivate tenant | Use activation endpoints instead |

#### Response (200 OK)
```json
{
    "id": "6ea84333-4d12-48ce-b869-8a63e35399c2",
    "name": "Updated Tenant Name",
    "code": "API-TEST-20250806162641",
    "type": "root",
    "parent_tenant_id": null,
    "isolation_mode": "shared",
    "settings": {
        "theme": "dark",
        "locale": "en-US",
        "new_setting": "value"
    },
    "features": [
        "api_access",
        "sso",
        "advanced_audit"
    ],
    "metadata": {
        "updated_reason": "Feature upgrade",
        "version": 2
    },
    "is_active": true,
    "created_at": "2025-08-06T20:26:41.801330Z",
    "updated_at": "2025-08-07T19:15:00Z"
}
```

---

### DELETE /tenants/{tenant_id}

**Purpose**: Delete tenant (hard delete - use with caution)

**Required Scope**: `tenant:admin`

#### Request
```http
DELETE /api/v1/tenants/6ea84333-4d12-48ce-b869-8a63e35399c2
Authorization: Bearer <access_token>
```

#### Response (204 No Content)
```
(Empty response body)
```

#### Error Responses
- **404 Not Found**: Tenant doesn't exist
- **403 Forbidden**: Insufficient permissions  
- **409 Conflict**: Tenant has dependencies (users, sub-tenants)

**⚠️ Warning**: This performs a hard delete. Consider using deactivation instead.

---

## Tenant Lookup Operations

### GET /tenants/code/{tenant_code}

**Purpose**: Get tenant by unique code

**Required Scope**: `tenant:read`

#### Request
```http
GET /api/v1/tenants/code/API-TEST-20250806162641
Authorization: Bearer <access_token>
```

#### Response (200 OK)
```json
{
    "id": "6ea84333-4d12-48ce-b869-8a63e35399c2",
    "name": "API Test Tenant",
    "code": "API-TEST-20250806162641",
    "type": "root",
    "parent_tenant_id": null,
    "isolation_mode": "shared",
    "settings": {
        "test": true
    },
    "features": [
        "api_access"
    ],
    "metadata": {
        "created_by": "test_script"
    },
    "is_active": true,
    "created_at": "2025-08-06T20:26:41.801330Z",
    "updated_at": "2025-08-06T20:26:41.801330Z"
}
```

---

## Hierarchical Tenant Operations

### POST /tenants/{parent_tenant_id}/sub-tenants

**Purpose**: Create sub-tenant under parent

**Required Scope**: `tenant:admin`

#### Request
```http
POST /api/v1/tenants/6ea84333-4d12-48ce-b869-8a63e35399c2/sub-tenants
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Marketing Division",
    "code": "ACME-MARKETING",
    "isolation_mode": "shared",
    "settings": {
        "department": "marketing",
        "budget_limit": 50000
    },
    "features": [
        "api_access",
        "custom_workflows"
    ],
    "metadata": {
        "division": "Marketing",
        "manager": "Jane Smith"
    }
}
```

#### Response (201 Created)
```json
{
    "id": "87654321-4321-4321-4321-876543210987",
    "name": "Marketing Division",
    "code": "ACME-MARKETING",
    "type": "sub_tenant",
    "parent_tenant_id": "6ea84333-4d12-48ce-b869-8a63e35399c2",
    "isolation_mode": "shared",
    "settings": {
        "department": "marketing",
        "budget_limit": 50000
    },
    "features": [
        "api_access",
        "custom_workflows"
    ],
    "metadata": {
        "division": "Marketing",
        "manager": "Jane Smith"
    },
    "is_active": true,
    "created_at": "2025-08-07T19:30:00Z",
    "updated_at": "2025-08-07T19:30:00Z"
}
```

---

### GET /tenants/{tenant_id}/hierarchy

**Purpose**: Get complete tenant hierarchy (parent and all descendants)

**Required Scope**: `tenant:read`

#### Request
```http
GET /api/v1/tenants/6ea84333-4d12-48ce-b869-8a63e35399c2/hierarchy
Authorization: Bearer <access_token>
```

#### Response (200 OK)
```json
[
    {
        "id": "6ea84333-4d12-48ce-b869-8a63e35399c2",
        "name": "API Test Tenant",
        "code": "API-TEST-20250806162641",
        "type": "root",
        "parent_tenant_id": null,
        "isolation_mode": "shared",
        "settings": {
            "test": true
        },
        "features": [
            "api_access"
        ],
        "metadata": {
            "created_by": "test_script"
        },
        "is_active": true,
        "created_at": "2025-08-06T20:26:41.801330Z",
        "updated_at": "2025-08-06T20:26:41.801330Z"
    },
    {
        "id": "87654321-4321-4321-4321-876543210987",
        "name": "Marketing Division",
        "code": "ACME-MARKETING",
        "type": "sub_tenant",
        "parent_tenant_id": "6ea84333-4d12-48ce-b869-8a63e35399c2",
        "isolation_mode": "shared",
        "settings": {
            "department": "marketing"
        },
        "features": [
            "api_access"
        ],
        "metadata": {
            "division": "Marketing"
        },
        "is_active": true,
        "created_at": "2025-08-07T19:30:00Z",
        "updated_at": "2025-08-07T19:30:00Z"
    }
]
```

---

## Tenant Activation Operations

### POST /tenants/{tenant_id}/activate

**Purpose**: Activate a deactivated tenant

**Required Scope**: `tenant:admin`

#### Request
```http
POST /api/v1/tenants/6ea84333-4d12-48ce-b869-8a63e35399c2/activate
Authorization: Bearer <access_token>
```

#### Response (200 OK)
```json
{
    "id": "6ea84333-4d12-48ce-b869-8a63e35399c2",
    "name": "API Test Tenant",
    "code": "API-TEST-20250806162641",
    "type": "root",
    "parent_tenant_id": null,
    "isolation_mode": "shared",
    "settings": {
        "test": true
    },
    "features": [
        "api_access"
    ],
    "metadata": {
        "created_by": "test_script"
    },
    "is_active": true,
    "created_at": "2025-08-06T20:26:41.801330Z",
    "updated_at": "2025-08-07T19:45:00Z"
}
```

---

### POST /tenants/{tenant_id}/deactivate

**Purpose**: Deactivate tenant (soft disable)

**Required Scope**: `tenant:admin`

#### Request
```http
POST /api/v1/tenants/6ea84333-4d12-48ce-b869-8a63e35399c2/deactivate
Authorization: Bearer <access_token>
```

#### Response (200 OK)
```json
{
    "id": "6ea84333-4d12-48ce-b869-8a63e35399c2",
    "name": "API Test Tenant", 
    "code": "API-TEST-20250806162641",
    "type": "root",
    "parent_tenant_id": null,
    "isolation_mode": "shared",
    "settings": {
        "test": true
    },
    "features": [
        "api_access"
    ],
    "metadata": {
        "created_by": "test_script"
    },
    "is_active": false,
    "created_at": "2025-08-06T20:26:41.801330Z",
    "updated_at": "2025-08-07T19:50:00Z"
}
```

---

## Common Headers

### Request Headers
```http
Authorization: Bearer <access_token>     # Required for all endpoints
Content-Type: application/json          # For POST/PATCH requests  
X-Tenant-ID: <tenant_id>               # Optional, auto-detected from token
```

### Response Headers
```http
Content-Type: application/json          # For JSON responses
X-Total-Count: 150                      # For paginated responses
X-RateLimit-Remaining: 58               # For rate-limited endpoints
```

## 📋 Allowed Features

Valid values for the `features` array:

- `multi_factor_auth` - Multi-factor authentication support
- `advanced_audit` - Enhanced audit logging and reporting
- `ai_insights` - AI-powered analytics and insights  
- `custom_workflows` - Custom workflow builder
- `api_access` - REST API access
- `sso` - Single sign-on integration
- `field_encryption` - Field-level encryption
- `compliance_reporting` - Compliance and regulatory reporting

## 🔍 Query Examples

### Complex Tenant Search
```http
GET /api/v1/tenants/?name=Corp&type=root&is_active=true&limit=25&offset=0
```

### Find All Sub-tenants
```http
GET /api/v1/tenants/?parent_tenant_id=6ea84333-4d12-48ce-b869-8a63e35399c2
```

### Feature-based Filtering (via code search)
```http
GET /api/v1/tenants/?code=ACME
```

## 📝 Notes

1. **Tenant Isolation**: Operations automatically scope to accessible tenants
2. **Soft Deactivation**: Preferred over hard deletion for data integrity
3. **Code Uniqueness**: Tenant codes must be globally unique across system
4. **Hierarchy Limits**: Maximum 10 levels of tenant hierarchy supported
5. **Feature Inheritance**: Sub-tenants can inherit parent tenant features
6. **Settings Merging**: Sub-tenant settings can override parent settings

---

*Last updated: 2025-08-07*  
*API Version: 1.0.0*