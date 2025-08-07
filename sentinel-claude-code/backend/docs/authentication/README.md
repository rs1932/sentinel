# 🔐 Sentinel Authentication API Documentation

## Overview

The Sentinel Authentication API provides comprehensive user authentication, token management, and session control for the Sentinel Access Platform. This API follows OAuth 2.0 and JWT standards for secure authentication.

**Base URL**: `http://localhost:8000/api/v1/auth`  
**Environment**: Development (DEBUG=true enables documentation)

## 📋 Quick Reference

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/login` | POST | User authentication | No |
| `/token` | POST | Service account auth | No |
| `/refresh` | POST | Token refresh | No |
| `/validate` | GET | Token validation | Yes |
| `/logout` | POST | User logout | Yes |
| `/revoke` | POST | Token revocation | No |
| `/me/tokens` | GET | List user sessions | Yes |
| `/me/tokens/{id}` | DELETE | Revoke specific session | Yes |
| `/me/tokens` | DELETE | Revoke all sessions | Yes |
| `/password-requirements` | GET | Password policy | No |
| `/security-event` | POST | Log security event | Optional |
| `/introspect` | POST | Token introspection | Yes (Service) |
| `/health` | GET | Health check | No |

## 🚀 Getting Started

### 1. User Authentication Flow

```javascript
// Step 1: Login
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123',
        tenant_code: 'ACME',
        remember_me: false
    })
});

const tokens = await loginResponse.json();
// Store tokens.access_token and tokens.refresh_token securely

// Step 2: Use access token for API calls
const apiResponse = await fetch('http://localhost:8000/api/v1/tenants/', {
    headers: {
        'Authorization': `Bearer ${tokens.access_token}`
    }
});
```

### 2. Token Refresh Flow

```javascript
// When access token expires (401 response), refresh it
const refreshResponse = await fetch('http://localhost:8000/api/v1/auth/refresh', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        refresh_token: storedRefreshToken
    })
});

const newTokens = await refreshResponse.json();
// Update stored access_token and refresh_token
```

### 3. Error Handling

All authentication errors follow this format:

```javascript
{
    "error": "authentication_failed",
    "error_description": "Invalid credentials",
    "error_code": "AUTH_001",
    "retry_after": 60  // Optional, for rate limiting
}
```

## 📁 Documentation Structure

- **[API Endpoints](./api-endpoints.md)** - Detailed endpoint specifications
- **[Authentication Flows](./auth-flows.md)** - Complete authentication workflows  
- **[Request/Response Examples](./examples.md)** - Real-world usage examples
- **[Error Codes](./error-codes.md)** - Complete error code reference
- **[Security Guide](./security.md)** - Security best practices
- **[Frontend Integration](./frontend-integration.md)** - Frontend-specific guidance

## 🔑 Key Features

- **Multi-tenant Authentication**: Tenant-aware user authentication
- **JWT Access Tokens**: Short-lived JWT tokens for API access
- **Refresh Token Rotation**: Secure token refresh mechanism
- **Service Account Support**: Machine-to-machine authentication
- **Session Management**: Device-aware session tracking
- **Rate Limiting**: Built-in rate limiting on sensitive endpoints
- **Security Events**: Comprehensive security event logging
- **Password Policies**: Configurable password complexity requirements

## ⚠️ Important Notes

1. **Token Storage**: Store refresh tokens securely (httpOnly cookies recommended)
2. **HTTPS Required**: Use HTTPS in production
3. **Rate Limiting**: Login endpoint limited to 10 attempts per minute
4. **Token Expiry**: Access tokens expire in 30 minutes by default
5. **Tenant Codes**: Must be uppercase with alphanumeric and hyphens only

## 🛠️ Development Environment

- **Server**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/api/docs`
- **Health Check**: `http://localhost:8000/health`
- **Debug Mode**: Enabled (shows detailed SQL logs)

## 📞 Support

For integration issues or questions:
- Review the API documentation at `/api/docs`
- Check error responses for detailed information
- Ensure proper Content-Type headers
- Validate request schemas against documentation

---

*Last updated: 2025-08-07*  
*API Version: 1.0.0*