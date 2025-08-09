# Resources API Documentation

## Overview

The Resources API provides endpoints for managing hierarchical resources in the Sentinel platform. Resources represent the structure of your applications, services, and data entities that can have permissions assigned to them.

## Resource Hierarchy

Resources follow a strict hierarchy that enables permission inheritance:

```
Product Family (product_family)
└── Application (app)
    └── Capability (capability)
        └── Service (service)
            ├── Page (page)
            ├── Entity (entity)
            └── API (api)
```

## Quick Reference

| Method | Endpoint | Description | Scopes Required |
|--------|----------|-------------|-----------------|
| GET | `/api/v1/resources/tree` | Get resource hierarchy | `resource:read` |
| GET | `/api/v1/resources/statistics` | Get resource statistics | `resource:read` |
| GET | `/api/v1/resources` | List resources with filtering | `resource:read` |
| GET | `/api/v1/resources/{id}` | Get resource details | `resource:read` |
| POST | `/api/v1/resources` | Create new resource | `resource:write` |
| PATCH | `/api/v1/resources/{id}` | Update resource | `resource:write` |
| DELETE | `/api/v1/resources/{id}` | Delete resource | `resource:admin` |
| GET | `/api/v1/resources/{id}/children` | Get child resources | `resource:read` |
| GET | `/api/v1/resources/{id}/permissions` | Get resource permissions | `resource:read` |
| POST | `/api/v1/resources/{id}/move` | Move resource in hierarchy | `resource:write` |

## Global Admin Access

Users with `resource:global` scope can access resources across all tenants. Regular users are restricted to their own tenant's resources.

## Next Steps

- [API Endpoints](./api-endpoints.md) - Detailed endpoint documentation
- [Examples](./examples.md) - Code examples and usage patterns
- [Frontend Integration](./frontend-integration.md) - React/TypeScript integration guide
- [Error Handling](./error-handling.md) - Common errors and solutions