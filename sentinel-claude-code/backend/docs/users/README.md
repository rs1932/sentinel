# 👥 Sentinel User Management API Documentation

## Overview

The Sentinel User Management API provides comprehensive user lifecycle management including user CRUD operations, profile management, service accounts, and avatar handling. This API is built on Module 3 and requires authentication for all operations.

**Base URL**: `http://localhost:8000/api/v1`  
**Authentication**: JWT Bearer token required for all endpoints  
**Tenant Isolation**: All operations are automatically scoped to the authenticated user's tenant  

## 📋 Quick Reference

### User Management Endpoints

| Endpoint | Method | Purpose | Required Scope |
|----------|--------|---------|----------------|
| `/users/me` | GET | Get current user profile | None (authenticated) |
| `/users/me` | PATCH | Update current user profile | None (authenticated) |
| `/users/` | POST | Create new user | `user:admin` |
| `/users/` | GET | List users with pagination | `user:read` |
| `/users/{id}` | GET | Get user details | `user:read` |
| `/users/{id}` | PATCH | Update user | `user:write` |
| `/users/{id}` | DELETE | Delete user (soft) | `user:admin` |
| `/users/bulk` | POST | Bulk operations | `user:admin` |
| `/users/{id}/permissions` | GET | Get user permissions | `user:read` |
| `/users/{id}/change-password` | POST | Change password | `user:write` |
| `/users/{id}/lock` | POST | Lock user account | `user:admin` |
| `/users/{id}/unlock` | POST | Unlock user account | `user:admin` |

### Service Account Endpoints

| Endpoint | Method | Purpose | Required Scope |
|----------|--------|---------|----------------|
| `/service-accounts/` | POST | Create service account | `service_account:admin` |
| `/service-accounts/` | GET | List service accounts | `service_account:read` |
| `/service-accounts/{id}` | GET | Get service account details | `service_account:read` |
| `/service-accounts/{id}` | PATCH | Update service account | `service_account:write` |
| `/service-accounts/{id}` | DELETE | Delete service account | `service_account:admin` |
| `/service-accounts/{id}/rotate` | POST | Rotate credentials | `service_account:admin` |

### Avatar Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/users/{id}/avatar` | POST | Upload avatar | Yes (self or admin) |
| `/users/{id}/avatar` | GET | Get avatar | Yes |
| `/users/{id}/avatar` | DELETE | Delete avatar | Yes (self or admin) |

## 🚀 Getting Started

### 1. Authentication Setup

All user management endpoints require authentication. Include the JWT token in the Authorization header:

```javascript
const headers = {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
};
```

### 2. Basic User Operations

```javascript
// Get current user profile
const currentUser = await fetch('http://localhost:8000/api/v1/users/me', {
    headers
});

// Update current user profile
const updateResponse = await fetch('http://localhost:8000/api/v1/users/me', {
    method: 'PATCH',
    headers,
    body: JSON.stringify({
        username: 'john_doe',
        preferences: { theme: 'dark', language: 'en' }
    })
});
```

### 3. User Listing with Filters

```javascript
// List users with pagination and filters
const users = await fetch('http://localhost:8000/api/v1/users/?page=1&limit=25&search=john&is_active=true', {
    headers
});
```

## 🔑 Key Features

- **Profile Management**: Self-service profile updates and preferences
- **User Administration**: Full CRUD operations for user management
- **Service Accounts**: Machine-to-machine authentication accounts
- **Avatar Support**: Profile picture upload and management
- **Advanced Filtering**: Search, sort, and filter users
- **Bulk Operations**: Perform operations on multiple users
- **Account Security**: Lock/unlock accounts and password management
- **Tenant Isolation**: Automatic tenant scoping for all operations
- **Audit Trail**: Track user creation and modifications

## 🔐 Permission Scopes

### User Scopes
- `user:read` - View user information
- `user:write` - Update user information
- `user:admin` - Full user management (create, delete, bulk operations)

### Service Account Scopes  
- `service_account:read` - View service accounts
- `service_account:write` - Update service accounts
- `service_account:admin` - Full service account management

## 📊 Data Models

### User Object
```json
{
    "id": "uuid",
    "tenant_id": "uuid", 
    "email": "user@example.com",
    "username": "optional_username",
    "attributes": {},
    "preferences": {},
    "is_active": true,
    "last_login": "2025-08-07T18:30:00Z",
    "login_count": 42,
    "created_at": "2025-08-01T10:00:00Z",
    "updated_at": "2025-08-07T18:30:00Z"
}
```

### Service Account Object
```json
{
    "id": "uuid",
    "tenant_id": "uuid",
    "name": "api-service",
    "description": "API service account",
    "attributes": {},
    "client_id": "svc_abc123456",
    "is_active": true,
    "last_login": "2025-08-07T18:30:00Z",
    "login_count": 150,
    "created_at": "2025-08-01T10:00:00Z",
    "updated_at": "2025-08-07T18:30:00Z"
}
```

## 📁 Documentation Structure

- **[API Endpoints](./api-endpoints.md)** - Detailed endpoint specifications
- **[Data Models](./data-models.md)** - Complete request/response schemas
- **[Frontend Integration](./frontend-integration.md)** - Frontend-specific integration examples
- **[Error Handling](./error-handling.md)** - Error codes and handling strategies
- **[Examples](./examples.md)** - Real-world usage examples and workflows

## ⚠️ Important Notes

### Security Considerations
1. **Token Required**: All endpoints require valid JWT authentication
2. **Scope Validation**: Operations are restricted by token scopes
3. **Tenant Isolation**: Users can only access data within their tenant
4. **Self-Service**: Users can always update their own profile
5. **Admin Privileges**: Admin scopes required for user management

### Data Constraints
- **Email**: Must be unique within tenant
- **Username**: Optional, 3-100 characters if provided
- **Password**: Minimum 8 characters (when creating users)
- **Avatar**: Max 5MB, PNG/JPEG/WebP formats
- **Bulk Operations**: Maximum 100 users per operation

### Rate Limiting
- **Avatar Upload**: 5 uploads per minute per user
- **Bulk Operations**: 5 operations per minute per user
- **Standard Endpoints**: Follow global API rate limits

## 🛠️ Development Environment

- **Server**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/api/docs`
- **Test Authentication**: Use `/auth/login` to get access token
- **Test User**: `test@example.com` / `password123` (tenant: `TEST`)

## 📞 Frontend Integration Tips

### Common Patterns
1. **Current User Context**: Fetch `/users/me` on app initialization
2. **Profile Updates**: Use PATCH with partial data
3. **User Lists**: Implement pagination with `page`/`limit` parameters
4. **Search**: Use `search` parameter for filtering by email/username
5. **Avatar Handling**: Support file upload with progress indicators

### Error Handling
- **403 Forbidden**: Insufficient permissions (check token scopes)
- **404 Not Found**: User doesn't exist in current tenant
- **409 Conflict**: Email already exists (during creation/updates)
- **422 Validation Error**: Invalid request data format

## 🔄 Typical Workflows

### User Registration Flow
1. Admin creates user with `POST /users/`
2. User receives invitation (if `send_invitation: true`)
3. User sets password via password reset flow
4. User can update profile via `PATCH /users/me`

### Service Account Creation
1. Admin creates service account with `POST /service-accounts/`
2. Store `client_secret` securely (only returned once)
3. Use `client_id` and `client_secret` for API authentication
4. Rotate credentials periodically via `POST /service-accounts/{id}/rotate`

---

*Last updated: 2025-08-07*  
*API Version: 1.0.0*