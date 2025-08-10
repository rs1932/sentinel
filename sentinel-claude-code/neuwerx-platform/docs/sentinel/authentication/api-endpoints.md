# 🔗 Authentication API Endpoints

## POST /auth/login

**Purpose**: Authenticate user with email/password credentials

### Request
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123",
    "tenant_code": "ACME",
    "mfa_code": "123456",          // Optional
    "remember_me": false           // Optional, default: false
}
```

### Response (200 OK)
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "def502006b8c...",
    "token_type": "Bearer",
    "expires_in": 1800,
    "scope": "user:read user:write tenant:admin",
    "user_id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15"
}
```

### Error Responses
- **401 Unauthorized**: Invalid credentials or account locked
- **422 Unprocessable Entity**: Invalid request format
- **429 Too Many Requests**: Rate limit exceeded (10 attempts/minute)

---

## POST /auth/token

**Purpose**: Authenticate service account for machine-to-machine communication

### Request
```http
POST /api/v1/auth/token
Content-Type: application/json

{
    "client_id": "svc_abc123456",
    "client_secret": "service_account_secret_key",
    "tenant_id": "ACME",           // Optional
    "scope": "api:read api:write"  // Optional
}
```

### Response (200 OK)
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "api:read api:write tenant:admin service_account:admin",
    "user_id": "12345678-1234-1234-1234-123456789012",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15"
}
```

---

## POST /auth/refresh

**Purpose**: Refresh access token using refresh token

### Request
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
    "refresh_token": "def502006b8c..."
}
```

### Response (200 OK)
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "def502007c9d...",
    "token_type": "Bearer",
    "expires_in": 1800,
    "scope": "user:read user:write tenant:admin",
    "user_id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15"
}
```

### Error Responses
- **401 Unauthorized**: Invalid or expired refresh token

---

## GET /auth/validate

**Purpose**: Validate access token and get token information

### Request
```http
GET /api/v1/auth/validate
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Response (200 OK)
```json
{
    "valid": true,
    "user_id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15",
    "scopes": ["user:read", "user:write", "tenant:admin"],
    "expires_at": "2025-08-07T19:28:04.578330+00:00",
    "is_service_account": false
}
```

### Error Responses
- **401 Unauthorized**: Invalid or expired token

---

## POST /auth/logout

**Purpose**: Logout user and revoke tokens

### Request
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
    "revoke_all_devices": false    // Optional, default: false
}
```

### Response (200 OK)
```json
{
    "message": "Logout successful"
}
```

---

## POST /auth/revoke

**Purpose**: Revoke specific access or refresh token

### Request
```http
POST /api/v1/auth/revoke
Content-Type: application/json

{
    "token": "token_to_revoke",
    "token_type": "access_token"   // or "refresh_token"
}
```

### Response (200 OK)
```json
{
    "message": "Token revoked successfully"
}
```

---

## GET /auth/me/tokens

**Purpose**: List user's active sessions (refresh tokens)

### Request
```http
GET /api/v1/auth/me/tokens
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Response (200 OK)
```json
[
    {
        "id": "779f49ae-d42d-4237-8cc5-81c26fe6f713",
        "device_info": {
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
            "device_name": null,
            "platform": "web",
            "location": null
        },
        "created_at": "2025-08-07T18:28:04.590",
        "last_used_at": "2025-08-07T18:28:04.590",
        "expires_at": "2025-09-06T18:28:04.589790"
    }
]
```

---

## DELETE /auth/me/tokens/{token_id}

**Purpose**: Revoke specific session (logout from device)

### Request
```http
DELETE /api/v1/auth/me/tokens/779f49ae-d42d-4237-8cc5-81c26fe6f713
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Response (200 OK)
```json
{
    "message": "Token revoked successfully"
}
```

---

## DELETE /auth/me/tokens

**Purpose**: Revoke all user sessions (logout from all devices)

### Request
```http
DELETE /api/v1/auth/me/tokens?keep_current=true
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Response (200 OK)
```json
{
    "message": "Revoked 3 tokens",
    "revoked_count": 3
}
```

---

## GET /auth/password-requirements

**Purpose**: Get password complexity requirements (public endpoint)

### Request
```http
GET /api/v1/auth/password-requirements
```

### Response (200 OK)
```json
{
    "min_length": 8,
    "require_uppercase": true,
    "require_lowercase": true,
    "require_numbers": true,
    "require_symbols": true,
    "forbidden_patterns": ["123456", "password", "qwerty"]
}
```

---

## POST /auth/security-event

**Purpose**: Log security event for monitoring

### Request
```http
POST /api/v1/auth/security-event
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...  # Optional
Content-Type: application/json

{
    "event_type": "suspicious_login",
    "severity": "warning",
    "description": "Login from unusual location",
    "metadata": {
        "ip_address": "192.168.1.100",
        "country": "US"
    },
    "user_id": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "ip_address": "192.168.1.100"
}
```

### Response (201 Created)
```json
{
    "message": "Security event logged",
    "event_id": "placeholder"
}
```

---

## POST /auth/introspect

**Purpose**: RFC 7662 token introspection (service accounts only)

### Request
```http
POST /api/v1/auth/introspect
Authorization: Bearer service_account_token
Content-Type: application/x-www-form-urlencoded

token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...&token_type_hint=access_token
```

### Response (200 OK)
```json
{
    "active": true,
    "sub": "e5680c44-b5ed-49af-b571-66d7171b9ce1",
    "aud": ["sentinel-api"],
    "iss": "sentinel-platform",
    "exp": 1725740884,
    "iat": 1725739084,
    "scope": "user:read user:write tenant:admin",
    "client_id": null,
    "token_type": "access_token",
    "tenant_id": "f3c417f3-d9f6-44e6-912a-442e02f15e15"
}
```

---

## GET /auth/health

**Purpose**: Authentication service health check

### Request
```http
GET /api/v1/auth/health
```

### Response (200 OK)
```json
{
    "status": "healthy",
    "service": "authentication",
    "timestamp": "2025-08-07T18:30:00Z"
}
```

## 🔍 Common Headers

### Request Headers
```http
Content-Type: application/json          # For POST requests
Authorization: Bearer <access_token>     # For authenticated endpoints
User-Agent: MyApp/1.0                   # For device tracking
X-Forwarded-For: 192.168.1.100         # For IP tracking (if behind proxy)
```

### Response Headers
```http
Content-Type: application/json
Cache-Control: no-store, no-cache       # For token responses
X-RateLimit-Remaining: 8                # For rate-limited endpoints
```

## 📝 Notes

1. **Rate Limiting**: Login endpoint is limited to 10 attempts per minute per IP
2. **Token Expiry**: Access tokens expire in 30 minutes, refresh tokens in 30 days
3. **Device Tracking**: All token requests track device information for security
4. **Tenant Isolation**: All operations are tenant-aware and isolated
5. **Security Events**: Consider logging security-relevant events for monitoring