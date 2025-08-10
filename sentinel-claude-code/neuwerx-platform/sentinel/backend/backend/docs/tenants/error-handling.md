# 🚨 Error Handling Guide - Tenant Management API

## HTTP Status Codes

### Success Responses
| Status Code | Description | When Used |
|-------------|-------------|-----------|
| `200 OK` | Request successful | GET, PATCH operations |
| `201 Created` | Resource created successfully | POST operations |
| `204 No Content` | Request successful, no response body | DELETE operations, activation/deactivation |

### Client Error Responses
| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| `400 Bad Request` | Invalid request format | Malformed JSON, missing required fields |
| `401 Unauthorized` | Authentication required | Missing or invalid JWT token |
| `403 Forbidden` | Insufficient permissions | Missing required scopes |
| `404 Not Found` | Resource not found | Invalid tenant ID, no access to tenant |
| `409 Conflict` | Resource conflict | Duplicate tenant code |
| `422 Unprocessable Entity` | Validation failed | Invalid data format, business rule violations |
| `429 Too Many Requests` | Rate limit exceeded | Too many API calls |

### Server Error Responses
| Status Code | Description | When to Retry |
|-------------|-------------|---------------|
| `500 Internal Server Error` | Server error | Yes, with exponential backoff |
| `502 Bad Gateway` | Gateway error | Yes, after brief delay |
| `503 Service Unavailable` | Service temporarily unavailable | Yes, with longer delay |

---

## Error Response Format

All error responses follow a consistent format:

```json
{
    "error": {
        "message": "Human-readable error message",
        "status_code": 422,
        "details": [
            {
                "field": "code",
                "message": "Code must contain only uppercase letters, numbers, and hyphens",
                "type": "validation_error"
            }
        ],
        "path": "/api/v1/tenants/",
        "method": "POST",
        "timestamp": "2025-08-07T19:30:00Z"
    }
}
```

### Error Object Fields
| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Primary error message for display |
| `status_code` | integer | HTTP status code |
| `details` | array | Detailed validation errors (optional) |
| `path` | string | API endpoint that failed |
| `method` | string | HTTP method used |
| `timestamp` | string | ISO timestamp of error |

---

## Common Error Scenarios

### 1. Authentication Errors

#### Missing Authorization Header
```http
401 Unauthorized
```
```json
{
    "error": {
        "message": "Authorization header is required",
        "status_code": 401,
        "path": "/api/v1/tenants/",
        "method": "GET"
    }
}
```

**Frontend Handling:**
```typescript
if (error.status === 401) {
    // Redirect to login page
    window.location.href = '/login';
}
```

#### Invalid JWT Token
```http
401 Unauthorized
```
```json
{
    "error": {
        "message": "Invalid or expired token",
        "status_code": 401,
        "path": "/api/v1/tenants/",
        "method": "GET"
    }
}
```

**Frontend Handling:**
```typescript
if (error.status === 401 && error.message.includes('expired')) {
    // Attempt token refresh
    await refreshToken();
    // Retry original request
}
```

---

### 2. Permission Errors

#### Insufficient Scopes
```http
403 Forbidden
```
```json
{
    "error": {
        "message": "Insufficient permissions. Required scope: tenant:admin",
        "status_code": 403,
        "details": [
            {
                "required_scope": "tenant:admin",
                "user_scopes": ["tenant:read", "tenant:write"],
                "type": "permission_error"
            }
        ],
        "path": "/api/v1/tenants/",
        "method": "POST"
    }
}
```

**Frontend Handling:**
```typescript
const handlePermissionError = (error: APIError) => {
    if (error.status_code === 403) {
        const requiredScope = error.details?.[0]?.required_scope;
        showNotification({
            type: 'error',
            message: `This action requires ${requiredScope} permission. Contact your administrator.`
        });
    }
};
```

---

### 3. Validation Errors

#### Tenant Code Validation
```http
422 Unprocessable Entity
```
```json
{
    "error": {
        "message": "Validation error",
        "status_code": 422,
        "details": [
            {
                "field": "code",
                "message": "Code must contain only uppercase letters, numbers, and hyphens, and start with a letter or number",
                "type": "pattern_validation",
                "provided_value": "tenant-code-123",
                "expected_pattern": "^[A-Z0-9][A-Z0-9-]*$"
            }
        ],
        "path": "/api/v1/tenants/",
        "method": "POST"
    }
}
```

#### Invalid Feature
```http
422 Unprocessable Entity
```
```json
{
    "error": {
        "message": "Validation error",
        "status_code": 422,
        "details": [
            {
                "field": "features",
                "message": "Unknown feature: invalid_feature",
                "type": "value_error",
                "provided_value": ["api_access", "invalid_feature"],
                "allowed_values": ["multi_factor_auth", "advanced_audit", "ai_insights", "custom_workflows", "api_access", "sso", "field_encryption", "compliance_reporting"]
            }
        ],
        "path": "/api/v1/tenants/",
        "method": "POST"
    }
}
```

**Frontend Handling:**
```typescript
const handleValidationErrors = (error: APIError) => {
    if (error.status_code === 422 && error.details) {
        error.details.forEach(detail => {
            const fieldElement = document.querySelector(`[name="${detail.field}"]`);
            if (fieldElement) {
                // Show inline validation error
                showFieldError(fieldElement, detail.message);
            }
        });
    }
};
```

---

### 4. Business Logic Errors

#### Tenant Code Already Exists
```http
409 Conflict
```
```json
{
    "error": {
        "message": "Tenant with code 'ACME-CORP' already exists",
        "status_code": 409,
        "details": [
            {
                "field": "code",
                "message": "A tenant with this code already exists",
                "type": "uniqueness_violation",
                "existing_tenant_id": "12345678-1234-1234-1234-123456789012"
            }
        ],
        "path": "/api/v1/tenants/",
        "method": "POST"
    }
}
```

#### Invalid Parent Tenant
```http
422 Unprocessable Entity
```
```json
{
    "error": {
        "message": "Validation error",
        "status_code": 422,
        "details": [
            {
                "field": "parent_tenant_id",
                "message": "Root tenants cannot have a parent",
                "type": "business_rule_violation"
            }
        ],
        "path": "/api/v1/tenants/",
        "method": "POST"
    }
}
```

---

### 5. Resource Not Found Errors

#### Tenant Not Found
```http
404 Not Found
```
```json
{
    "error": {
        "message": "Tenant not found or access denied",
        "status_code": 404,
        "details": [
            {
                "resource": "tenant",
                "resource_id": "invalid-uuid-here",
                "type": "not_found"
            }
        ],
        "path": "/api/v1/tenants/invalid-uuid-here",
        "method": "GET"
    }
}
```

#### Tenant by Code Not Found
```http
404 Not Found
```
```json
{
    "error": {
        "message": "Tenant with code 'NONEXISTENT' not found",
        "status_code": 404,
        "details": [
            {
                "resource": "tenant",
                "search_field": "code",
                "search_value": "NONEXISTENT",
                "type": "not_found"
            }
        ],
        "path": "/api/v1/tenants/code/NONEXISTENT",
        "method": "GET"
    }
}
```

---

## Frontend Error Handling Patterns

### 1. Comprehensive Error Handler

```typescript
// utils/tenantErrorHandler.ts
export interface TenantAPIError {
    message: string;
    status_code: number;
    details?: ErrorDetail[];
    path?: string;
    method?: string;
    timestamp?: string;
}

export interface ErrorDetail {
    field?: string;
    message: string;
    type: string;
    provided_value?: any;
    expected_pattern?: string;
    allowed_values?: any[];
}

export class TenantErrorHandler {
    static handle(error: TenantAPIError): UserFriendlyError {
        switch (error.status_code) {
            case 400:
                return this.handleBadRequest(error);
            case 401:
                return this.handleUnauthorized(error);
            case 403:
                return this.handleForbidden(error);
            case 404:
                return this.handleNotFound(error);
            case 409:
                return this.handleConflict(error);
            case 422:
                return this.handleValidation(error);
            case 429:
                return this.handleRateLimit(error);
            default:
                return this.handleServerError(error);
        }
    }

    private static handleValidation(error: TenantAPIError): UserFriendlyError {
        if (!error.details || error.details.length === 0) {
            return {
                title: 'Validation Error',
                message: 'Please check your input and try again.',
                type: 'validation'
            };
        }

        const fieldErrors: Record<string, string> = {};
        let primaryMessage = 'Please fix the following errors:';

        error.details.forEach(detail => {
            if (detail.field) {
                fieldErrors[detail.field] = detail.message;
            }

            // Special handling for common validation patterns
            if (detail.type === 'pattern_validation' && detail.field === 'code') {
                fieldErrors[detail.field] = 'Code must be uppercase alphanumeric with hyphens (e.g., ACME-CORP)';
            }
        });

        return {
            title: 'Validation Error',
            message: primaryMessage,
            type: 'validation',
            fieldErrors
        };
    }

    private static handleConflict(error: TenantAPIError): UserFriendlyError {
        if (error.message.includes('code')) {
            return {
                title: 'Duplicate Tenant Code',
                message: 'A tenant with this code already exists. Please choose a different code.',
                type: 'conflict',
                fieldErrors: { code: 'This code is already taken' }
            };
        }

        return {
            title: 'Conflict Error',
            message: error.message || 'The operation conflicts with existing data.',
            type: 'conflict'
        };
    }

    private static handleForbidden(error: TenantAPIError): UserFriendlyError {
        const requiredScope = error.details?.[0]?.required_scope;
        let message = 'You do not have permission to perform this action.';
        
        if (requiredScope) {
            message += ` Required permission: ${requiredScope}`;
        }

        return {
            title: 'Permission Denied',
            message,
            type: 'permission',
            actionable: 'Contact your administrator to request additional permissions.'
        };
    }

    private static handleNotFound(error: TenantAPIError): UserFriendlyError {
        if (error.path?.includes('/code/')) {
            return {
                title: 'Tenant Not Found',
                message: 'No tenant found with the specified code.',
                type: 'not_found'
            };
        }

        return {
            title: 'Tenant Not Found',
            message: 'The requested tenant was not found or you do not have access to it.',
            type: 'not_found'
        };
    }

    private static handleUnauthorized(error: TenantAPIError): UserFriendlyError {
        return {
            title: 'Authentication Required',
            message: 'Please log in to continue.',
            type: 'auth',
            actionable: 'You will be redirected to the login page.'
        };
    }

    private static handleBadRequest(error: TenantAPIError): UserFriendlyError {
        return {
            title: 'Invalid Request',
            message: 'The request was malformed. Please check your input.',
            type: 'validation'
        };
    }

    private static handleRateLimit(error: TenantAPIError): UserFriendlyError {
        return {
            title: 'Too Many Requests',
            message: 'You are making requests too quickly. Please wait a moment and try again.',
            type: 'rate_limit',
            retryAfter: 60 // seconds
        };
    }

    private static handleServerError(error: TenantAPIError): UserFriendlyError {
        return {
            title: 'Server Error',
            message: 'An unexpected error occurred. Please try again later.',
            type: 'server',
            retryable: true
        };
    }
}

export interface UserFriendlyError {
    title: string;
    message: string;
    type: 'validation' | 'conflict' | 'permission' | 'not_found' | 'auth' | 'rate_limit' | 'server';
    fieldErrors?: Record<string, string>;
    actionable?: string;
    retryable?: boolean;
    retryAfter?: number;
}
```

### 2. React Hook for Error Handling

```typescript
// hooks/useErrorHandler.ts
import { useState } from 'react';
import { TenantErrorHandler, UserFriendlyError, TenantAPIError } from '../utils/tenantErrorHandler';

export const useErrorHandler = () => {
    const [error, setError] = useState<UserFriendlyError | null>(null);
    const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

    const handleError = (apiError: TenantAPIError) => {
        const friendlyError = TenantErrorHandler.handle(apiError);
        
        setError(friendlyError);
        setFieldErrors(friendlyError.fieldErrors || {});

        // Handle auth errors automatically
        if (friendlyError.type === 'auth') {
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        }

        // Auto-clear errors after 5 seconds for non-critical errors
        if (!['auth', 'server'].includes(friendlyError.type)) {
            setTimeout(() => {
                clearError();
            }, 5000);
        }
    };

    const clearError = () => {
        setError(null);
        setFieldErrors({});
    };

    const clearFieldError = (field: string) => {
        setFieldErrors(prev => {
            const updated = { ...prev };
            delete updated[field];
            return updated;
        });
    };

    return {
        error,
        fieldErrors,
        handleError,
        clearError,
        clearFieldError,
        hasError: !!error,
        hasFieldErrors: Object.keys(fieldErrors).length > 0
    };
};
```

### 3. Error Display Components

```tsx
// components/ErrorDisplay.tsx
import React from 'react';
import { UserFriendlyError } from '../utils/tenantErrorHandler';

interface ErrorDisplayProps {
    error: UserFriendlyError;
    onDismiss?: () => void;
    onRetry?: () => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onDismiss, onRetry }) => {
    const getErrorIcon = () => {
        switch (error.type) {
            case 'validation':
            case 'conflict':
                return '⚠️';
            case 'permission':
                return '🔒';
            case 'not_found':
                return '🔍';
            case 'auth':
                return '🔐';
            case 'rate_limit':
                return '🚫';
            case 'server':
                return '💥';
            default:
                return 'ℹ️';
        }
    };

    const getErrorColor = () => {
        switch (error.type) {
            case 'validation':
            case 'conflict':
                return 'border-yellow-200 bg-yellow-50 text-yellow-800';
            case 'permission':
            case 'not_found':
                return 'border-orange-200 bg-orange-50 text-orange-800';
            case 'auth':
            case 'server':
                return 'border-red-200 bg-red-50 text-red-800';
            case 'rate_limit':
                return 'border-purple-200 bg-purple-50 text-purple-800';
            default:
                return 'border-blue-200 bg-blue-50 text-blue-800';
        }
    };

    return (
        <div className={`border rounded-lg p-4 mb-4 ${getErrorColor()}`}>
            <div className="flex items-start">
                <span className="text-xl mr-3">{getErrorIcon()}</span>
                <div className="flex-1">
                    <h3 className="font-medium mb-1">{error.title}</h3>
                    <p className="text-sm">{error.message}</p>
                    {error.actionable && (
                        <p className="text-sm mt-2 opacity-75">{error.actionable}</p>
                    )}
                </div>
                <div className="flex gap-2 ml-4">
                    {error.retryable && onRetry && (
                        <button
                            onClick={onRetry}
                            className="px-3 py-1 text-xs bg-white border border-current rounded hover:bg-opacity-10"
                        >
                            Retry
                        </button>
                    )}
                    {onDismiss && (
                        <button
                            onClick={onDismiss}
                            className="px-3 py-1 text-xs bg-white border border-current rounded hover:bg-opacity-10"
                        >
                            Dismiss
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};
```

### 4. Form Field Error Display

```tsx
// components/FormFieldError.tsx
import React from 'react';

interface FormFieldErrorProps {
    error?: string;
    className?: string;
}

export const FormFieldError: React.FC<FormFieldErrorProps> = ({ error, className = '' }) => {
    if (!error) return null;

    return (
        <div className={`text-red-600 text-sm mt-1 ${className}`}>
            <span className="inline-flex items-center">
                <span className="mr-1">⚠️</span>
                {error}
            </span>
        </div>
    );
};

// Usage in forms:
export const TenantForm: React.FC = () => {
    const { fieldErrors } = useErrorHandler();

    return (
        <form>
            <div>
                <label>Tenant Code</label>
                <input name="code" type="text" />
                <FormFieldError error={fieldErrors.code} />
            </div>
        </form>
    );
};
```

## Retry Strategies

### Exponential Backoff Implementation

```typescript
// utils/retryHandler.ts
export class RetryHandler {
    static async withRetry<T>(
        fn: () => Promise<T>,
        options: {
            maxAttempts?: number;
            baseDelay?: number;
            maxDelay?: number;
            retryableStatuses?: number[];
        } = {}
    ): Promise<T> {
        const {
            maxAttempts = 3,
            baseDelay = 1000,
            maxDelay = 10000,
            retryableStatuses = [500, 502, 503, 504]
        } = options;

        let lastError: any;

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return await fn();
            } catch (error: any) {
                lastError = error;

                // Don't retry if it's not a retryable error
                if (!retryableStatuses.includes(error.status)) {
                    throw error;
                }

                // Don't retry on last attempt
                if (attempt === maxAttempts) {
                    break;
                }

                // Calculate delay with exponential backoff and jitter
                const delay = Math.min(
                    baseDelay * Math.pow(2, attempt - 1) + Math.random() * 1000,
                    maxDelay
                );

                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }

        throw lastError;
    }
}

// Usage example:
const tenantService = {
    async createTenant(data: any) {
        return RetryHandler.withRetry(async () => {
            const response = await fetch('/api/v1/tenants/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw { status: response.status, ...error };
            }

            return response.json();
        });
    }
};
```

---

*Last updated: 2025-08-07*  
*Error Handling Version: 1.0.0*