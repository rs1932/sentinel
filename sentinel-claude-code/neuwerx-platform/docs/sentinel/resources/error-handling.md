# Resources API Error Handling

## Overview

The Resources API returns consistent error responses with appropriate HTTP status codes and detailed error information to help frontend developers handle errors gracefully.

## Error Response Format

All errors follow this consistent format:

```json
{
  "error": {
    "message": "Human-readable error description",
    "status_code": 400,
    "path": "/api/v1/resources",
    "method": "POST",
    "details": {
      // Optional additional error details
    }
  }
}
```

## HTTP Status Codes

| Code | Status | Description | When it occurs |
|------|--------|-------------|----------------|
| 400 | Bad Request | Invalid request data | Malformed JSON, missing required fields, invalid values |
| 401 | Unauthorized | Authentication required | Missing or invalid JWT token |
| 403 | Forbidden | Insufficient permissions | User lacks required scopes |
| 404 | Not Found | Resource not found | Resource ID doesn't exist or user can't access it |
| 409 | Conflict | Resource conflict | Duplicate code, hierarchy violations |
| 422 | Unprocessable Entity | Validation errors | Business rule violations |
| 500 | Internal Server Error | Server error | Unexpected server issues |

## Common Error Scenarios

### 1. Authentication Errors (401)

#### Missing Authorization Header
```bash
curl "http://localhost:8000/api/v1/resources/tree"
```

**Response:**
```json
{
  "error": {
    "message": "Missing authorization header",
    "status_code": 401,
    "path": "/api/v1/resources/tree",
    "method": "GET"
  }
}
```

#### Invalid/Expired Token
```bash
curl -H "Authorization: Bearer invalid_token" \
  "http://localhost:8000/api/v1/resources/tree"
```

**Response:**
```json
{
  "error": {
    "message": {
      "error": "invalid_token",
      "error_description": "Token is invalid or expired"
    },
    "status_code": 401,
    "path": "/api/v1/resources/tree",
    "method": "GET"
  }
}
```

### 2. Permission Errors (403)

#### Insufficient Scopes
```bash
# User without resource:read scope
curl -H "Authorization: Bearer $USER_TOKEN" \
  "http://localhost:8000/api/v1/resources/tree"
```

**Response:**
```json
{
  "error": {
    "message": "Insufficient permissions. Required scope: resource:read",
    "status_code": 403,
    "path": "/api/v1/resources/tree",
    "method": "GET"
  }
}
```

### 3. Resource Not Found (404)

#### Invalid Resource ID
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/invalid-uuid-format"
```

**Response:**
```json
{
  "error": {
    "message": "Resource with ID invalid-uuid-format not found",
    "status_code": 404,
    "path": "/api/v1/resources/invalid-uuid-format",
    "method": "GET"
  }
}
```

#### Resource Exists But No Access (Tenant Isolation)
```bash
# User from MARITIME tenant trying to access PLATFORM resource
curl -H "Authorization: Bearer $MARITIME_USER_TOKEN" \
  "http://localhost:8000/api/v1/resources/platform-resource-id"
```

**Response:**
```json
{
  "error": {
    "message": "Resource with ID platform-resource-id not found",
    "status_code": 404,
    "path": "/api/v1/resources/platform-resource-id",
    "method": "GET"
  }
}
```

### 4. Validation Errors (400)

#### Missing Required Fields
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Resource"
  }' \
  "http://localhost:8000/api/v1/resources"
```

**Response:**
```json
{
  "error": {
    "message": "Validation error",
    "status_code": 422,
    "details": [
      {
        "field": "type",
        "message": "Field required",
        "type": "missing"
      },
      {
        "field": "code", 
        "message": "Field required",
        "type": "missing"
      }
    ],
    "path": "/api/v1/resources",
    "method": "POST"
  }
}
```

#### Invalid Field Values
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "invalid_type",
    "name": "Test Resource",
    "code": "test-resource"
  }' \
  "http://localhost:8000/api/v1/resources"
```

**Response:**
```json
{
  "error": {
    "message": "Invalid resource type: invalid_type",
    "status_code": 400,
    "path": "/api/v1/resources",
    "method": "POST"
  }
}
```

#### Invalid Query Parameters
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources?page=-1&limit=1000"
```

**Response:**
```json
{
  "error": {
    "message": "Validation error",
    "status_code": 422,
    "details": [
      {
        "field": "page",
        "message": "Input should be greater than or equal to 1",
        "type": "greater_than_equal"
      },
      {
        "field": "limit",
        "message": "Input should be less than or equal to 100",
        "type": "less_than_equal"
      }
    ],
    "path": "/api/v1/resources",
    "method": "GET"
  }
}
```

### 5. Conflict Errors (409)

#### Duplicate Resource Code
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "service",
    "name": "Duplicate Service",
    "code": "vessel-tracking",
    "parent_id": "ab98f486-1983-4fcc-8778-2070c0010e8b"
  }' \
  "http://localhost:8000/api/v1/resources"
```

**Response:**
```json
{
  "error": {
    "message": "Resource code 'vessel-tracking' already exists for type 'service'",
    "status_code": 409,
    "path": "/api/v1/resources",
    "method": "POST"
  }
}
```

### 6. Business Rule Violations (422)

#### Invalid Hierarchy
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "app",
    "name": "Invalid App",
    "code": "invalid-app",
    "parent_id": "f4656a18-cf27-472e-addb-769141a754f5"
  }' \
  "http://localhost:8000/api/v1/resources"
```

**Response:**
```json
{
  "error": {
    "message": "Invalid hierarchy: app cannot be a child of service. Valid parents: [product_family]",
    "status_code": 400,
    "path": "/api/v1/resources",
    "method": "POST"
  }
}
```

#### Circular Dependency
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_parent_id": "child-resource-id"
  }' \
  "http://localhost:8000/api/v1/resources/parent-resource-id/move"
```

**Response:**
```json
{
  "error": {
    "message": "Moving resource would create circular dependency",
    "status_code": 400,
    "path": "/api/v1/resources/parent-resource-id/move",
    "method": "POST"
  }
}
```

#### Delete Resource with Children
```bash
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/service-with-children-id"
```

**Response:**
```json
{
  "error": {
    "message": "Cannot delete resource with 3 active children. Use cascade=true to delete children.",
    "status_code": 400,
    "path": "/api/v1/resources/service-with-children-id",
    "method": "DELETE"
  }
}
```

## Frontend Error Handling

### React Error Handling with React Query

```typescript
// hooks/useResourceTree.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useResourceTree() {
  return useQuery({
    queryKey: ['resources', 'tree'],
    queryFn: () => apiClient.resources.getTree(),
    retry: (failureCount, error: any) => {
      // Don't retry on 4xx errors (client errors)
      if (error?.status >= 400 && error?.status < 500) {
        return false;
      }
      // Retry up to 3 times for 5xx errors
      return failureCount < 3;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}
```

### Error Boundary Component

```typescript
// components/ResourceErrorBoundary.tsx
import { QueryErrorResetBoundary } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';
import { AlertTriangle, RefreshCw, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorFallbackProps {
  error: any;
  resetErrorBoundary: () => void;
}

function ResourceErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  const getErrorMessage = (error: any) => {
    if (error?.status === 401) {
      return {
        title: 'Authentication Required',
        message: 'Please log in to access this resource.',
        icon: <Lock className="h-12 w-12 text-gray-400" />,
        action: 'Sign In',
        actionFn: () => window.location.href = '/auth/login'
      };
    }
    
    if (error?.status === 403) {
      return {
        title: 'Access Denied',
        message: 'You don\'t have permission to view this resource.',
        icon: <Lock className="h-12 w-12 text-gray-400" />,
        action: 'Contact Admin',
        actionFn: () => {}
      };
    }
    
    if (error?.status === 404) {
      return {
        title: 'Resource Not Found',
        message: 'The resource you\'re looking for doesn\'t exist or has been moved.',
        icon: <AlertTriangle className="h-12 w-12 text-gray-400" />,
        action: 'Go Back',
        actionFn: () => window.history.back()
      };
    }
    
    return {
      title: 'Something went wrong',
      message: error?.message || 'An unexpected error occurred.',
      icon: <AlertTriangle className="h-12 w-12 text-gray-400" />,
      action: 'Try Again',
      actionFn: resetErrorBoundary
    };
  };

  const errorInfo = getErrorMessage(error);

  return (
    <div className="text-center py-12">
      <div className="flex justify-center mb-4">
        {errorInfo.icon}
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {errorInfo.title}
      </h3>
      <p className="text-gray-600 mb-6 max-w-md mx-auto">
        {errorInfo.message}
      </p>
      <div className="flex justify-center gap-3">
        <Button onClick={errorInfo.actionFn}>
          {errorInfo.action}
        </Button>
        {errorInfo.action !== 'Try Again' && (
          <Button variant="outline" onClick={resetErrorBoundary}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Try Again
          </Button>
        )}
      </div>
    </div>
  );
}

export function ResourceErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          FallbackComponent={ResourceErrorFallback}
        >
          {children}
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
```

### Form Validation Error Handling

```typescript
// components/CreateResourceForm.tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function CreateResourceForm({ onSuccess }: { onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    type: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => apiClient.resources.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
      onSuccess();
      setErrors({});
    },
    onError: (error: any) => {
      // Handle validation errors
      if (error.status === 422 && error.details) {
        const fieldErrors: Record<string, string> = {};
        error.details.forEach((detail: any) => {
          fieldErrors[detail.field] = detail.message;
        });
        setErrors(fieldErrors);
      } else {
        // Handle other errors
        setErrors({ 
          _general: error.message || 'An unexpected error occurred' 
        });
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    createMutation.mutate(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {errors._general && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-800">{errors._general}</p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium mb-1">Resource Type</label>
        <select
          value={formData.type}
          onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
          className={`w-full p-2 border rounded-md ${
            errors.type ? 'border-red-300 bg-red-50' : 'border-gray-300'
          }`}
        >
          <option value="">Select type...</option>
          <option value="product_family">Product Family</option>
          <option value="app">Application</option>
          <option value="capability">Capability</option>
          <option value="service">Service</option>
          <option value="entity">Entity</option>
          <option value="page">Page</option>
          <option value="api">API</option>
        </select>
        {errors.type && (
          <p className="mt-1 text-sm text-red-600">{errors.type}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Name</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          className={`w-full p-2 border rounded-md ${
            errors.name ? 'border-red-300 bg-red-50' : 'border-gray-300'
          }`}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Code</label>
        <input
          type="text"
          value={formData.code}
          onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value }))}
          className={`w-full p-2 border rounded-md ${
            errors.code ? 'border-red-300 bg-red-50' : 'border-gray-300'
          }`}
        />
        {errors.code && (
          <p className="mt-1 text-sm text-red-600">{errors.code}</p>
        )}
      </div>

      <Button
        type="submit"
        disabled={createMutation.isPending}
        className="w-full"
      >
        {createMutation.isPending ? 'Creating...' : 'Create Resource'}
      </Button>
    </form>
  );
}
```

### Network Error Handling

```typescript
// lib/api/client.ts - Enhanced error handling
class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(this.token && { Authorization: `Bearer ${this.token}` }),
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw {
          status: response.status,
          message: errorData.error?.message || response.statusText,
          details: errorData.error?.details,
          ...errorData.error,
        };
      }

      return await response.json();
    } catch (error: any) {
      if (error.name === 'TypeError' || error.message?.includes('Failed to fetch')) {
        throw {
          status: 0,
          message: 'Network error. Please check your connection.',
          type: 'network_error',
        };
      }
      throw error;
    }
  }
}
```

### Toast Notifications for Errors

```typescript
// hooks/useResourceMutations.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api/client';

export function useCreateResource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => apiClient.resources.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
      toast({
        title: 'Success',
        description: `Resource "${data.name}" created successfully.`,
      });
    },
    onError: (error: any) => {
      let description = 'Failed to create resource.';
      
      if (error.status === 409) {
        description = 'A resource with this code already exists.';
      } else if (error.status === 400) {
        description = error.message || 'Invalid resource configuration.';
      } else if (error.status === 403) {
        description = 'You don\'t have permission to create resources.';
      }
      
      toast({
        title: 'Error',
        description,
        variant: 'destructive',
      });
    },
  });
}
```

## Best Practices

### 1. **Always Handle Network Errors**
```typescript
const { data, error, isLoading, isError } = useResourceTree();

if (isError && error?.status === 0) {
  // Network error - show retry option
  return <NetworkErrorComponent onRetry={refetch} />;
}
```

### 2. **Provide Contextual Error Messages**
```typescript
const getErrorMessage = (error: any, context: string) => {
  const messages = {
    create: {
      409: 'This resource name is already taken. Please choose a different name.',
      400: 'Please check your resource configuration and try again.',
    },
    delete: {
      400: 'This resource has child resources. Use cascade delete if you want to remove them all.',
    },
  };
  
  return messages[context]?.[error.status] || error.message;
};
```

### 3. **Implement Retry Logic**
```typescript
const retryMutation = useMutation({
  mutationFn: apiClient.resources.create,
  retry: (failureCount, error: any) => {
    // Retry transient errors
    return error.status >= 500 && failureCount < 3;
  },
});
```

### 4. **Cache Error States**
```typescript
const { data, error } = useQuery({
  queryKey: ['resources', 'tree'],
  queryFn: () => apiClient.resources.getTree(),
  staleTime: 5 * 60 * 1000,
  // Keep error state in cache to prevent flashing
  cacheTime: 10 * 60 * 1000,
});
```

By implementing these error handling patterns, your frontend will provide a much better user experience when things go wrong.