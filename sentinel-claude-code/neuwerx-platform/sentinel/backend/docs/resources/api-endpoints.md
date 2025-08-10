# Resources API Endpoints

## Authentication

All endpoints require JWT authentication via the `Authorization: Bearer {token}` header.

## Base URL

```
{API_BASE_URL}/api/v1/resources
```

---

## GET /tree

Get the complete resource hierarchy as a tree structure.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `root_id` | UUID | No | Return subtree starting from this resource ID |
| `max_depth` | integer | No | Maximum depth to traverse (1-10) |

### Response Format

```typescript
interface ResourceTreeResponse {
  tree: ResourceTreeNode | ResourceTreeNode[];
  total_nodes: number;
  max_depth: number;
}

interface ResourceTreeNode {
  id: string;
  type: 'product_family' | 'app' | 'capability' | 'service' | 'entity' | 'page' | 'api';
  name: string;
  code: string;
  attributes: Record<string, any>;
  is_active: boolean;
  children: ResourceTreeNode[];
}
```

### Example Request

```bash
curl -H "Authorization: Bearer {token}" \
  "https://api.example.com/api/v1/resources/tree"
```

### Example Response

```json
{
  "tree": [
    {
      "id": "87fd2b4c-7a62-4f44-b025-6574b4968630",
      "type": "product_family",
      "name": "Maritime Logistics Platform",
      "code": "maritime-logistics",
      "attributes": {
        "description": "Complete maritime operations management platform"
      },
      "is_active": true,
      "children": [
        {
          "id": "ce3153e6-45e7-4f80-ae93-77fc72eae8cf",
          "type": "app",
          "name": "Port Operations",
          "code": "port-ops",
          "attributes": {
            "description": "Port operations management application"
          },
          "is_active": true,
          "children": []
        }
      ]
    }
  ],
  "total_nodes": 7,
  "max_depth": 4
}
```

---

## GET /statistics

Get resource statistics for the current tenant (or all tenants for global admins).

### Response Format

```typescript
interface ResourceStatistics {
  total_resources: number;
  by_type: Record<string, number>;
  active_resources: number;
  inactive_resources: number;
  max_hierarchy_depth: number;
  total_root_resources: number;
}
```

### Example Response

```json
{
  "total_resources": 7,
  "by_type": {
    "ResourceType.API": 1,
    "ResourceType.CAPABILITY": 1,
    "ResourceType.PAGE": 1,
    "ResourceType.ENTITY": 1,
    "ResourceType.SERVICE": 1,
    "ResourceType.APP": 1,
    "ResourceType.PRODUCT_FAMILY": 1
  },
  "active_resources": 7,
  "inactive_resources": 0,
  "max_hierarchy_depth": 5,
  "total_root_resources": 1
}
```

---

## GET /

List resources with filtering, search, and pagination.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by resource type |
| `parent_id` | UUID | No | Filter by parent resource ID |
| `is_active` | boolean | No | Filter by active status |
| `search` | string | No | Search in name and code |
| `page` | integer | No | Page number (default: 1) |
| `limit` | integer | No | Items per page (1-100, default: 50) |
| `sort_by` | string | No | Field to sort by (name, code, type, created_at) |
| `sort_order` | string | No | Sort order (asc, desc) |

### Response Format

```typescript
interface ResourceListResponse {
  items: ResourceResponse[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

interface ResourceResponse {
  id: string;
  tenant_id: string;
  type: string;
  name: string;
  code: string;
  parent_id?: string;
  path: string;
  attributes: Record<string, any>;
  workflow_enabled: boolean;
  workflow_config: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

### Example Request

```bash
curl -H "Authorization: Bearer {token}" \
  "https://api.example.com/api/v1/resources?type=service&page=1&limit=10"
```

---

## GET /{id}

Get detailed information about a specific resource.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | UUID | Yes | Resource ID |

### Response Format

```typescript
interface ResourceDetailResponse extends ResourceResponse {
  depth: number;
  hierarchy_level_name: string;
  ancestor_ids: string[];
  child_count: number;
}
```

### Example Response

```json
{
  "id": "87fd2b4c-7a62-4f44-b025-6574b4968630",
  "tenant_id": "e788a9e5-5898-45d6-9d64-a856f9bf3471",
  "type": "product_family",
  "name": "Maritime Logistics Platform",
  "code": "maritime-logistics",
  "parent_id": null,
  "path": "/87fd2b4c-7a62-4f44-b025-6574b4968630/",
  "attributes": {
    "description": "Complete maritime operations management platform"
  },
  "workflow_enabled": false,
  "workflow_config": {},
  "is_active": true,
  "created_at": "2025-01-08T10:30:45.123Z",
  "updated_at": "2025-01-08T10:30:45.123Z",
  "depth": 0,
  "hierarchy_level_name": "Product Family",
  "ancestor_ids": [],
  "child_count": 1
}
```

---

## POST /

Create a new resource.

### Request Body

```typescript
interface ResourceCreateRequest {
  type: 'product_family' | 'app' | 'capability' | 'service' | 'entity' | 'page' | 'api';
  name: string;
  code: string;
  parent_id?: string;
  attributes?: Record<string, any>;
  workflow_enabled?: boolean;
  workflow_config?: Record<string, any>;
  is_active?: boolean;
}
```

### Hierarchy Validation Rules

- `product_family`: No parent (root level)
- `app`: Parent must be `product_family`
- `capability`: Parent must be `app`
- `service`: Parent must be `capability`
- `entity`, `page`, `api`: Parent must be `service` (or `app` for entity/page)

### Example Request

```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "service",
    "name": "Vessel Tracking Service",
    "code": "vessel-tracking",
    "parent_id": "ab98f486-1983-4fcc-8778-2070c0010e8b",
    "attributes": {
      "description": "Track vessel positions and movements"
    },
    "is_active": true
  }' \
  "https://api.example.com/api/v1/resources"
```

---

## PATCH /{id}

Update an existing resource.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | UUID | Yes | Resource ID |

### Request Body

```typescript
interface ResourceUpdate {
  name?: string;
  parent_id?: string; // Moving in hierarchy
  attributes?: Record<string, any>;
  workflow_enabled?: boolean;
  workflow_config?: Record<string, any>;
  is_active?: boolean;
}
```

### Example Request

```bash
curl -X PATCH \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Service Name",
    "is_active": false
  }' \
  "https://api.example.com/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5"
```

---

## DELETE /{id}

Soft delete a resource.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | UUID | Yes | Resource ID |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cascade` | boolean | No | Delete child resources as well (default: false) |

### Example Request

```bash
curl -X DELETE \
  -H "Authorization: Bearer {token}" \
  "https://api.example.com/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5?cascade=true"
```

---

## GET /{id}/children

Get direct child resources of a specific resource.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | UUID | Yes | Parent resource ID |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `is_active` | boolean | No | Filter by active status |
| `page` | integer | No | Page number |
| `limit` | integer | No | Items per page |

### Response Format

Same as `GET /` - returns `ResourceListResponse` with child resources.

---

## GET /{id}/permissions

Get all permissions associated with a specific resource.

### Response Format

```typescript
interface ResourcePermissionResponse {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  permissions: Array<{
    id: string;
    name: string;
    actions: string[];
    conditions: Record<string, any>;
    field_permissions: Record<string, string[]>;
    is_active: boolean;
  }>;
}
```

---

## POST /{id}/move

Move a resource to a different parent in the hierarchy.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | UUID | Yes | Resource ID to move |

### Request Body

```typescript
interface ResourceMoveRequest {
  new_parent_id: string | null; // null moves to root level
}
```

### Example Request

```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "new_parent_id": "ce3153e6-45e7-4f80-ae93-77fc72eae8cf"
  }' \
  "https://api.example.com/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5/move"
```

---

## Error Responses

All endpoints may return these error status codes:

| Status | Description |
|--------|-------------|
| 400 | Bad Request - Invalid request data |
| 401 | Unauthorized - Missing or invalid JWT token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource code already exists or hierarchy violation |
| 422 | Unprocessable Entity - Validation errors |
| 500 | Internal Server Error - Server error |

### Error Response Format

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