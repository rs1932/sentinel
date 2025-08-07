# Sentinel API Endpoints Reference

## Base URL
```
http://localhost:8000
```

## System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint - returns app info |
| GET | `/health` | Health check endpoint |
| GET | `/api/docs` | Swagger UI Documentation |
| GET | `/api/redoc` | ReDoc Documentation |
| GET | `/api/openapi.json` | OpenAPI schema |

## Module 1: Tenant Management Endpoints

Base path: `/api/v1/tenants`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tenants/` | Create a new tenant |
| GET | `/api/v1/tenants/` | List all tenants |
| GET | `/api/v1/tenants/{tenant_id}` | Get tenant details |
| GET | `/api/v1/tenants/code/{tenant_code}` | Get tenant by code |
| PATCH | `/api/v1/tenants/{tenant_id}` | Update tenant |
| DELETE | `/api/v1/tenants/{tenant_id}` | Delete tenant |
| POST | `/api/v1/tenants/{parent_tenant_id}/sub-tenants` | Create sub-tenant |
| GET | `/api/v1/tenants/{tenant_id}/hierarchy` | Get tenant hierarchy |
| POST | `/api/v1/tenants/{tenant_id}/activate` | Activate tenant |
| POST | `/api/v1/tenants/{tenant_id}/deactivate` | Deactivate tenant |

## Quick Test Commands

### Check Server Status
```bash
curl http://localhost:8000/health
```

### Create a Tenant
```bash
curl -X POST http://localhost:8000/api/v1/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "code": "TEST-001",
    "type": "root",
    "isolation_mode": "shared",
    "settings": {},
    "features": ["api_access"],
    "metadata": {"industry": "Technology"}
  }'
```

### List All Tenants
```bash
curl http://localhost:8000/api/v1/tenants/
```

### Get Specific Tenant (replace {id} with actual UUID)
```bash
curl http://localhost:8000/api/v1/tenants/{id}
```

### Get Tenant by Code
```bash
curl http://localhost:8000/api/v1/tenants/code/TEST-001
```

### Update Tenant (replace {id} with actual UUID)
```bash
curl -X PATCH http://localhost:8000/api/v1/tenants/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Company Name",
    "settings": {"theme": "dark"}
  }'
```

### Create Sub-Tenant (replace {parent_id} with actual UUID)
```bash
curl -X POST http://localhost:8000/api/v1/tenants/{parent_id}/sub-tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sub Division",
    "code": "SUB-001",
    "isolation_mode": "shared",
    "settings": {},
    "features": [],
    "metadata": {}
  }'
```

### Activate/Deactivate Tenant (replace {id} with actual UUID)
```bash
# Deactivate
curl -X POST http://localhost:8000/api/v1/tenants/{id}/deactivate

# Activate
curl -X POST http://localhost:8000/api/v1/tenants/{id}/activate
```

### Delete Tenant (replace {id} with actual UUID)
```bash
curl -X DELETE http://localhost:8000/api/v1/tenants/{id}
```

## Query Parameters for List Endpoints

The GET `/api/v1/tenants/` endpoint supports the following query parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | string | Filter by tenant name (partial match) | `?name=Acme` |
| `code` | string | Filter by tenant code (partial match) | `?code=TEST` |
| `type` | string | Filter by tenant type | `?type=root` |
| `parent_tenant_id` | UUID | Filter by parent tenant | `?parent_tenant_id=...` |
| `is_active` | boolean | Filter by active status | `?is_active=true` |
| `limit` | integer | Maximum items to return (1-1000) | `?limit=50` |
| `offset` | integer | Number of items to skip | `?offset=10` |

### Example with Filters
```bash
# Get active root tenants with "Corp" in name, limit 10
curl "http://localhost:8000/api/v1/tenants/?name=Corp&type=root&is_active=true&limit=10"
```

## Response Format

### Success Response
```json
{
  "id": "uuid",
  "name": "Tenant Name",
  "code": "TENANT-CODE",
  "type": "root",
  "parent_tenant_id": null,
  "isolation_mode": "shared",
  "settings": {},
  "features": [],
  "metadata": {},
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Error Response
```json
{
  "error": {
    "message": "Error description",
    "status_code": 400,
    "path": "/api/v1/tenants/",
    "method": "POST"
  }
}
```

### List Response
```json
{
  "items": [...],
  "total": 100,
  "limit": 10,
  "offset": 0
}
```

## Testing with Python

```python
import requests

# Base URL
base_url = "http://localhost:8000"

# Check health
response = requests.get(f"{base_url}/health")
print(response.json())

# Create tenant
tenant_data = {
    "name": "Python Test Tenant",
    "code": "PY-TEST-001",
    "type": "root",
    "isolation_mode": "shared",
    "settings": {},
    "features": ["api_access"],
    "metadata": {"created_via": "python"}
}

response = requests.post(f"{base_url}/api/v1/tenants/", json=tenant_data)
if response.status_code == 201:
    tenant = response.json()
    print(f"Created tenant: {tenant['id']}")
```

## Notes

- All endpoints return JSON responses
- UUID fields should be valid UUID v4 format
- Tenant codes must be uppercase letters, numbers, and hyphens only
- The platform tenant (code: PLATFORM) cannot be modified or deleted
- Sub-tenants require an active parent tenant
- Tenants with sub-tenants cannot be deleted (must delete sub-tenants first)
- Feature flags are validated against allowed values