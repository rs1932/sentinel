# ❌ Authentication Error Codes

## Error Response Format

All authentication errors follow a consistent format:

```json
{
    "error": "error_type",
    "error_description": "Human-readable error message",
    "error_code": "SPECIFIC_CODE",    // Optional
    "retry_after": 60                 // Optional, seconds to wait
}
```

## 🔐 Authentication Errors

| Error Type | HTTP Status | Description | Frontend Action |
|------------|-------------|-------------|-----------------|
| `authentication_failed` | 401 | Invalid email/password | Show error, allow retry |
| `invalid_credentials` | 401 | Wrong credentials | Show error, allow retry |
| `account_locked` | 401 | Too many failed attempts | Show lockout message |
| `tenant_not_found` | 401 | Invalid tenant code | Show error, check tenant code |
| `user_inactive` | 401 | User account disabled | Contact administrator |
| `email_not_verified` | 401 | Email verification required | Show verification prompt |
| `mfa_required` | 401 | MFA code needed | Prompt for MFA code |
| `invalid_mfa` | 401 | Wrong MFA code | Allow MFA retry |

## 🔄 Token Errors

| Error Type | HTTP Status | Description | Frontend Action |
|------------|-------------|-------------|-----------------|
| `invalid_token` | 401 | Token invalid/expired | Attempt refresh or login |
| `missing_token` | 401 | No authorization header | Redirect to login |
| `invalid_grant` | 401 | Refresh token invalid | Clear tokens, redirect to login |
| `expired_token` | 401 | Access token expired | Attempt token refresh |
| `revoked_token` | 401 | Token was revoked | Clear tokens, redirect to login |
| `malformed_token` | 400 | Token format invalid | Clear tokens, redirect to login |

## 📊 Validation Errors

| Error Type | HTTP Status | Description | Frontend Action |
|------------|-------------|-------------|-----------------|
| `validation_error` | 422 | Request validation failed | Show field-specific errors |
| `invalid_email` | 422 | Email format invalid | Highlight email field |
| `invalid_tenant_code` | 422 | Tenant code format invalid | Show format requirements |
| `password_too_weak` | 422 | Password doesn't meet policy | Show password requirements |
| `missing_required_field` | 422 | Required field empty | Highlight missing fields |

## 🚫 Rate Limiting Errors

| Error Type | HTTP Status | Description | Frontend Action |
|------------|-------------|-------------|-----------------|
| `rate_limit_exceeded` | 429 | Too many requests | Show wait message with timer |
| `login_attempts_exceeded` | 429 | Too many login attempts | Show lockout duration |

## 🔧 Service Errors

| Error Type | HTTP Status | Description | Frontend Action |
|------------|-------------|-------------|-----------------|
| `service_unavailable` | 503 | Auth service down | Show service unavailable message |
| `database_error` | 500 | Database connection failed | Show try again later |
| `internal_error` | 500 | Unexpected server error | Show generic error message |

## 📱 Client Errors

| Error Type | HTTP Status | Description | Frontend Action |
|------------|-------------|-------------|-----------------|
| `invalid_client` | 401 | Service account invalid | Check client credentials |
| `unsupported_grant_type` | 400 | Invalid grant type | Check request format |
| `invalid_scope` | 400 | Invalid scope requested | Check scope format |

## 🔍 Detailed Error Examples

### Login Failure
```json
{
    "error": "authentication_failed",
    "error_description": "Invalid email or password",
    "error_code": "AUTH_001"
}
```

### Account Locked
```json
{
    "error": "account_locked",
    "error_description": "Account locked due to too many failed login attempts",
    "error_code": "AUTH_002",
    "retry_after": 1800
}
```

### Rate Limited
```json
{
    "error": "rate_limit_exceeded",
    "error_description": "Too many login attempts. Try again later.",
    "error_code": "RATE_001",
    "retry_after": 60
}
```

### Validation Error
```json
{
    "error": "validation_error",
    "error_description": "Invalid request format",
    "error_code": "VAL_001",
    "details": {
        "email": ["Invalid email format"],
        "password": ["Password too short"],
        "tenant_code": ["Must be uppercase letters and numbers only"]
    }
}
```

### Token Expired
```json
{
    "error": "invalid_token",
    "error_description": "Access token has expired",
    "error_code": "TOKEN_001"
}
```

### Refresh Token Invalid
```json
{
    "error": "invalid_grant",
    "error_description": "Refresh token is invalid or expired",
    "error_code": "TOKEN_002"
}
```

## 🔧 Frontend Error Handling

### Error Handler Function

```javascript
const handleAuthError = (error, response) => {
    const { error: errorType, error_description, retry_after } = error;
    
    switch (errorType) {
        case 'authentication_failed':
        case 'invalid_credentials':
            return {
                message: 'Invalid email or password. Please try again.',
                field: null,
                retryable: true
            };
            
        case 'account_locked':
            return {
                message: `Account locked. Try again in ${retry_after / 60} minutes.`,
                field: null,
                retryable: false,
                retryAfter: retry_after
            };
            
        case 'tenant_not_found':
            return {
                message: 'Organization not found. Please check your organization code.',
                field: 'tenant_code',
                retryable: true
            };
            
        case 'rate_limit_exceeded':
            return {
                message: `Too many attempts. Please wait ${retry_after} seconds.`,
                field: null,
                retryable: false,
                retryAfter: retry_after
            };
            
        case 'validation_error':
            return {
                message: 'Please correct the highlighted fields.',
                field: null,
                retryable: true,
                fieldErrors: error.details || {}
            };
            
        case 'invalid_token':
        case 'expired_token':
            // Attempt token refresh
            return {
                message: 'Session expired. Refreshing...',
                field: null,
                retryable: false,
                shouldRefresh: true
            };
            
        case 'invalid_grant':
            // Refresh failed, redirect to login
            return {
                message: 'Please log in again.',
                field: null,
                retryable: false,
                shouldLogout: true
            };
            
        default:
            return {
                message: error_description || 'An error occurred. Please try again.',
                field: null,
                retryable: true
            };
    }
};
```

### Rate Limiting Handler

```javascript
const handleRateLimit = (retryAfter) => {
    let countdown = retryAfter;
    
    const updateButton = () => {
        const button = document.getElementById('login-button');
        if (button) {
            button.disabled = true;
            button.textContent = `Try again in ${countdown}s`;
        }
    };
    
    const timer = setInterval(() => {
        countdown--;
        updateButton();
        
        if (countdown <= 0) {
            clearInterval(timer);
            const button = document.getElementById('login-button');
            if (button) {
                button.disabled = false;
                button.textContent = 'Sign In';
            }
        }
    }, 1000);
    
    updateButton();
};
```

### Retry Logic

```javascript
const loginWithRetry = async (credentials, maxRetries = 3) => {
    let attempt = 0;
    
    while (attempt < maxRetries) {
        try {
            return await authService.login(credentials);
        } catch (error) {
            attempt++;
            
            const errorInfo = handleAuthError(error);
            
            if (!errorInfo.retryable || attempt >= maxRetries) {
                throw error;
            }
            
            // Wait before retry (exponential backoff)
            const delay = Math.pow(2, attempt) * 1000;
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
};
```

## 📋 Error Code Quick Reference

### Common Status Codes
- **400**: Bad Request - Malformed request
- **401**: Unauthorized - Authentication required/failed
- **403**: Forbidden - Authentication successful but access denied
- **422**: Unprocessable Entity - Validation failed
- **429**: Too Many Requests - Rate limited
- **500**: Internal Server Error - Server error
- **503**: Service Unavailable - Service down

### Error Categories
- **AUTH_xxx**: Authentication errors
- **TOKEN_xxx**: Token-related errors  
- **VAL_xxx**: Validation errors
- **RATE_xxx**: Rate limiting errors
- **SRV_xxx**: Service errors

## 💡 Best Practices

1. **Always handle errors gracefully** - Show user-friendly messages
2. **Implement retry logic** - For transient errors only
3. **Respect rate limits** - Show countdown timers
4. **Clear tokens on auth failure** - Prevent infinite retry loops
5. **Log security events** - Track authentication failures
6. **Validate inputs client-side** - Reduce server-side validation errors
7. **Show progress indicators** - During authentication attempts
8. **Provide clear error messages** - Help users resolve issues

---

*Keep this reference handy for debugging authentication issues and implementing proper error handling in your frontend application.*