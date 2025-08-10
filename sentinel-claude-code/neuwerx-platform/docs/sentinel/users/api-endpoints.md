# 🔗 User Management API Endpoints

## User Profile Endpoints

### GET /users/me

**Purpose**: Get current authenticated user's profile

**Authentication**: Required (any valid token)

#### Request
```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

#### Response (200 OK)
```json
{
    "id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15",
    "email": "john.doe@acme.com",
    "username": "john_doe",
    "attributes": {
        "department": "Engineering",
        "location": "San Francisco"
    },
    "preferences": {
        "theme": "dark",
        "language": "en",
        "notifications": true
    },
    "is_active": true,
    "last_login": "2025-08-07T18:30:00Z",
    "login_count": 42,
    "created_at": "2025-08-01T10:00:00Z",
    "updated_at": "2025-08-07T18:30:00Z"
}
```

---

### PATCH /users/me

**Purpose**: Update current user's profile

**Authentication**: Required (any valid token)

#### Request
```http
PATCH /api/v1/users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "username": "john_doe_updated",
    "attributes": {
        "department": "Product",
        "location": "Remote"
    },
    "preferences": {
        "theme": "light",
        "language": "en",
        "notifications": false
    }
}
```

#### Response (200 OK)
```json
{
    "id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15",
    "email": "john.doe@acme.com",
    "username": "john_doe_updated",
    "attributes": {
        "department": "Product",
        "location": "Remote"
    },
    "preferences": {
        "theme": "light",
        "language": "en",
        "notifications": false
    },
    "is_active": true,
    "last_login": "2025-08-07T18:30:00Z",
    "login_count": 42,
    "created_at": "2025-08-01T10:00:00Z",
    "updated_at": "2025-08-07T18:35:00Z"
}
```

---

## User Administration Endpoints

### POST /users/

**Purpose**: Create a new user

**Required Scope**: `user:admin`

#### Request
```http
POST /api/v1/users/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "email": "jane.smith@acme.com",
    "username": "jane_smith",
    "password": "SecurePass123!",
    "attributes": {
        "department": "Marketing",
        "role": "Manager"
    },
    "preferences": {
        "theme": "system",
        "language": "en"
    },
    "is_active": true,
    "send_invitation": false
}
```

#### Response (201 Created)
```json
{
    "id": "12345678-1234-1234-1234-123456789012",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15",
    "email": "jane.smith@acme.com",
    "username": "jane_smith",
    "attributes": {
        "department": "Marketing",
        "role": "Manager"
    },
    "preferences": {
        "theme": "system",
        "language": "en"
    },
    "is_active": true,
    "last_login": null,
    "login_count": 0,
    "created_at": "2025-08-07T18:40:00Z",
    "updated_at": "2025-08-07T18:40:00Z"
}
```

#### Error Responses
- **409 Conflict**: Email already exists in tenant
- **422 Validation Error**: Invalid email format or password requirements
- **403 Forbidden**: Insufficient permissions

---

### GET /users/

**Purpose**: List users with filtering and pagination

**Required Scope**: `user:read`

#### Request
```http
GET /api/v1/users/?page=1&limit=25&search=john&is_active=true&sort=created_at&order=desc
Authorization: Bearer <access_token>
```

#### Query Parameters
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number (≥1) | 1 |
| `limit` | integer | Items per page (1-100) | 50 |
| `search` | string | Search email/username | - |
| `is_active` | boolean | Filter by active status | - |
| `role` | string | Filter by role name | - |
| `group` | string | Filter by group name | - |
| `tenant_id` | UUID | Filter by tenant (admin only) | current |
| `sort` | enum | Sort field | created_at |
| `order` | enum | Sort order (asc/desc) | desc |

#### Response (200 OK)
```json
{
    "items": [
        {
            "id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
            "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15",
            "email": "john.doe@acme.com",
            "username": "john_doe",
            "attributes": {
                "department": "Engineering"
            },
            "preferences": {
                "theme": "dark"
            },
            "is_active": true,
            "last_login": "2025-08-07T18:30:00Z",
            "login_count": 42,
            "created_at": "2025-08-01T10:00:00Z",
            "updated_at": "2025-08-07T18:30:00Z"
        }
    ],
    "total": 1,
    "page": 1,
    "limit": 25,
    "pages": 1
}
```

---

### GET /users/{user_id}

**Purpose**: Get detailed user information

**Required Scope**: `user:read`

#### Request
```http
GET /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1
Authorization: Bearer <access_token>
```

#### Response (200 OK)
```json
{
    "id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15",
    "email": "john.doe@acme.com",
    "username": "john_doe",
    "attributes": {
        "department": "Engineering"
    },
    "preferences": {
        "theme": "dark"
    },
    "is_active": true,
    "last_login": "2025-08-07T18:30:00Z",
    "login_count": 42,
    "failed_login_count": 0,
    "locked_until": null,
    "created_at": "2025-08-01T10:00:00Z",
    "updated_at": "2025-08-07T18:30:00Z"
}
```

---

### PATCH /users/{user_id}

**Purpose**: Update user information

**Required Scope**: `user:write`

#### Request
```http
PATCH /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "username": "john_doe_senior",
    "attributes": {
        "department": "Engineering",
        "level": "Senior"
    },
    "is_active": true
}
```

#### Response (200 OK)
```json
{
    "id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15",
    "email": "john.doe@acme.com",
    "username": "john_doe_senior",
    "attributes": {
        "department": "Engineering",
        "level": "Senior"
    },
    "preferences": {
        "theme": "dark"
    },
    "is_active": true,
    "last_login": "2025-08-07T18:30:00Z",
    "login_count": 42,
    "created_at": "2025-08-01T10:00:00Z",
    "updated_at": "2025-08-07T18:45:00Z"
}
```

---

### DELETE /users/{user_id}

**Purpose**: Delete user (soft delete by default)

**Required Scope**: `user:admin`

#### Request
```http
DELETE /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1?hard_delete=false
Authorization: Bearer <access_token>
```

#### Query Parameters
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `hard_delete` | boolean | Permanent deletion | false |

#### Response (204 No Content)
```
(Empty response body)
```

---

## Advanced User Operations

### POST /users/bulk

**Purpose**: Perform bulk operations on multiple users

**Required Scope**: `user:admin`

#### Request
```http
POST /api/v1/users/bulk
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "operation": "deactivate",
    "user_ids": [
        "e5680c44-b5ed-49af-b571-66d7171b9ce1",
        "12345678-1234-1234-1234-123456789012"
    ],
    "data": {}
}
```

#### Available Operations
- `activate` - Activate users
- `deactivate` - Deactivate users  
- `delete` - Soft delete users
- `assign_role` - Assign role (data: {"role_id": "uuid"})
- `remove_role` - Remove role (data: {"role_id": "uuid"})

#### Response (200 OK)
```json
{
    "operation": "deactivate",
    "total_requested": 2,
    "successful": 2,
    "failed": 0,
    "failed_ids": [],
    "errors": []
}
```

---

### GET /users/{user_id}/permissions

**Purpose**: Get user's effective permissions

**Required Scope**: `user:read`

#### Request
```http
GET /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1/permissions
Authorization: Bearer <access_token>
```

#### Response (200 OK)
```json
{
    "user_id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15",
    "direct_permissions": [
        {
            "resource": "user",
            "actions": ["read", "write"],
            "conditions": {}
        }
    ],
    "inherited_permissions": [
        {
            "source": "role:admin",
            "resource": "tenant",
            "actions": ["read", "write", "admin"],
            "conditions": {}
        }
    ],
    "effective_permissions": [
        {
            "resource": "user",
            "actions": ["read", "write"],
            "conditions": {}
        },
        {
            "resource": "tenant",
            "actions": ["read", "write", "admin"],
            "conditions": {}
        }
    ]
}
```

---

## Password Management

### POST /users/{user_id}/change-password

**Purpose**: Change user password

**Required Scope**: `user:write` (own password) or `user:admin` (others)

#### Request
```http
POST /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "current_password": "OldPassword123!",
    "new_password": "NewSecurePassword456!"
}
```

#### Response (204 No Content)
```
(Empty response body)
```

#### Error Responses
- **401 Unauthorized**: Current password incorrect
- **403 Forbidden**: Cannot change other user's password without admin scope
- **422 Validation Error**: New password doesn't meet requirements

---

## Account Security

### POST /users/{user_id}/lock

**Purpose**: Lock user account temporarily

**Required Scope**: `user:admin`

#### Request
```http
POST /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1/lock?duration_minutes=60
Authorization: Bearer <access_token>
```

#### Query Parameters
| Parameter | Type | Description | Default | Range |
|-----------|------|-------------|---------|-------|
| `duration_minutes` | integer | Lock duration | 30 | 1-1440 |

#### Response (204 No Content)
```
(Empty response body)
```

---

### POST /users/{user_id}/unlock

**Purpose**: Unlock user account

**Required Scope**: `user:admin`

#### Request
```http
POST /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1/unlock
Authorization: Bearer <access_token>
```

#### Response (204 No Content)
```
(Empty response body)
```

---

## Service Account Management

### POST /service-accounts/

**Purpose**: Create service account for API access

**Required Scope**: `service_account:admin`

#### Request
```http
POST /api/v1/service-accounts/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "api-integration",
    "description": "Service account for API integration",
    "attributes": {
        "environment": "production",
        "purpose": "data-sync"
    },
    "is_active": true
}
```

#### Response (201 Created)
```json
{
    "service_account": {
        "id": "87654321-4321-4321-4321-876543210987",
        "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15",
        "name": "api-integration",
        "description": "Service account for API integration",
        "attributes": {
            "environment": "production",
            "purpose": "data-sync"
        },
        "client_id": "svc_abc123456",
        "is_active": true,
        "last_login": null,
        "login_count": 0,
        "created_at": "2025-08-07T19:00:00Z",
        "updated_at": "2025-08-07T19:00:00Z"
    },
    "credentials": {
        "client_id": "svc_abc123456",
        "client_secret": "sa_very_long_secret_key_here",
        "created_at": "2025-08-07T19:00:00Z",
        "expires_at": null
    }
}
```

**⚠️ Important**: The `client_secret` is only returned once during creation. Store it securely!

---

### POST /service-accounts/{id}/rotate

**Purpose**: Rotate service account credentials

**Required Scope**: `service_account:admin`

#### Request
```http
POST /api/v1/service-accounts/87654321-4321-4321-4321-876543210987/rotate
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "revoke_existing": true
}
```

#### Response (200 OK)
```json
{
    "client_id": "svc_abc123456",
    "client_secret": "sa_new_secret_key_after_rotation",
    "created_at": "2025-08-07T19:15:00Z",
    "expires_at": null
}
```

---

## Avatar Management

### POST /users/{user_id}/avatar

**Purpose**: Upload user avatar image

**Authentication**: Required (self or admin)  
**Rate Limit**: 5 uploads per minute

#### Request
```http
POST /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1/avatar
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <image_file>
```

#### File Requirements
- **Formats**: PNG, JPEG, WebP
- **Max Size**: 5MB
- **Recommended**: Square aspect ratio, 512x512px or larger

#### Response (200 OK)
```json
{
    "avatar_id": "av_def456789",
    "original_url": "/storage/avatars/e5680c44-b5ed-49af-b571-66d7171b9ce1/original.jpg",
    "sizes": {
        "small": "/storage/avatars/e5680c44-b5ed-49af-b571-66d7171b9ce1/small.jpg",
        "medium": "/storage/avatars/e5680c44-b5ed-49af-b571-66d7171b9ce1/medium.jpg",
        "large": "/storage/avatars/e5680c44-b5ed-49af-b571-66d7171b9ce1/large.jpg"
    },
    "upload_date": "2025-08-07T19:30:00Z"
}
```

---

### GET /users/{user_id}/avatar

**Purpose**: Get user avatar image

**Authentication**: Required

#### Request
```http
GET /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1/avatar?size=medium
Authorization: Bearer <access_token>
```

#### Query Parameters
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `size` | enum | Size variant (small/medium/large) | medium |

#### Response (200 OK)
```
Content-Type: image/jpeg
Content-Length: 45678

<image_binary_data>
```

---

### DELETE /users/{user_id}/avatar

**Purpose**: Delete user avatar

**Authentication**: Required (self or admin)

#### Request
```http
DELETE /api/v1/users/e5680c44-b5ed-49af-b571-66d7171b9ce1/avatar
Authorization: Bearer <access_token>
```

#### Response (204 No Content)
```
(Empty response body)
```

---

## Common Headers

### Request Headers
```http
Authorization: Bearer <access_token>     # Required for all endpoints
Content-Type: application/json          # For JSON requests
Content-Type: multipart/form-data       # For file uploads
X-Tenant-ID: <tenant_id>               # Optional, auto-detected from token
```

### Response Headers
```http
Content-Type: application/json          # For JSON responses
X-RateLimit-Remaining: 58               # For rate-limited endpoints
X-Total-Count: 150                      # For paginated responses
```

## 🔍 Query Examples

### Complex User Search
```http
GET /api/v1/users/?search=engineer&is_active=true&sort=last_login&order=desc&page=1&limit=20
```

### Filter by Custom Attributes (using search)
```http
GET /api/v1/users/?search=Marketing
```

### Service Account Listing
```http
GET /api/v1/service-accounts/?is_active=true&page=1&limit=10
```

## 📝 Notes

1. **Tenant Isolation**: All operations automatically scope to the authenticated user's tenant
2. **Soft Deletes**: Default deletion is soft (sets `is_active: false`)
3. **Pagination**: Maximum limit is 100 items per page
4. **Search**: Searches across email and username fields
5. **Attributes**: Custom JSON data for user metadata and attributes
6. **Preferences**: User-specific UI/UX preferences stored as JSON