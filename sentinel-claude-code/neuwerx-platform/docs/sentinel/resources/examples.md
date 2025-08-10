# Resources API Examples

## Authentication Setup

All examples assume you have a valid JWT token. Here's how to get one:

```bash
# Login to get JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@sentinel.com",
    "password": "admin123",
    "tenant_code": "PLATFORM"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

---

## 1. Getting Resource Hierarchy

### Get Complete Resource Tree

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/tree" | jq
```

**Response:**
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
          "children": [
            {
              "id": "ab98f486-1983-4fcc-8778-2070c0010e8b",
              "type": "capability",
              "name": "Vessel Management",
              "code": "vessel-mgmt",
              "attributes": {
                "description": "Manage vessel arrivals, departures, and berth allocation"
              },
              "is_active": true,
              "children": []
            }
          ]
        }
      ]
    }
  ],
  "total_nodes": 7,
  "max_depth": 4
}
```

### Get Subtree from Specific Root

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/tree?root_id=ce3153e6-45e7-4f80-ae93-77fc72eae8cf" | jq
```

### Limit Tree Depth

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/tree?max_depth=2" | jq
```

---

## 2. Resource Statistics

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/statistics" | jq
```

**Response:**
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

## 3. Listing Resources

### List All Resources

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources" | jq
```

### Filter by Resource Type

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources?type=service" | jq
```

### Search Resources

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources?search=vessel" | jq
```

### Paginated Results

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources?page=1&limit=5&sort_by=name&sort_order=asc" | jq
```

### Filter by Parent

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources?parent_id=f4656a18-cf27-472e-addb-769141a754f5" | jq
```

---

## 4. Creating Resources

### Create Product Family (Root Level)

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "product_family",
    "name": "Financial Services Platform",
    "code": "financial-services",
    "attributes": {
      "description": "Complete financial services management platform",
      "version": "1.0",
      "owner": "Finance Team"
    },
    "is_active": true
  }' \
  "http://localhost:8000/api/v1/resources" | jq
```

### Create Application under Product Family

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "app",
    "name": "Trading Platform",
    "code": "trading-platform",
    "parent_id": "87fd2b4c-7a62-4f44-b025-6574b4968630",
    "attributes": {
      "description": "Real-time trading application",
      "technology": "React + Node.js",
      "environment": "production"
    },
    "workflow_enabled": true,
    "workflow_config": {
      "approval_required": true,
      "approvers": ["trading-manager", "risk-manager"]
    },
    "is_active": true
  }' \
  "http://localhost:8000/api/v1/resources" | jq
```

### Create Service with Complex Attributes

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "service",
    "name": "Order Processing Service",
    "code": "order-processing",
    "parent_id": "ab98f486-1983-4fcc-8778-2070c0010e8b",
    "attributes": {
      "description": "Handles trade order processing and validation",
      "service_type": "microservice",
      "deployment": {
        "replicas": 3,
        "cpu": "500m",
        "memory": "1Gi"
      },
      "dependencies": ["pricing-service", "risk-service"],
      "endpoints": [
        "/api/orders",
        "/api/orders/{id}",
        "/api/orders/{id}/status"
      ],
      "sla": {
        "availability": "99.9%",
        "response_time": "< 100ms"
      }
    },
    "workflow_enabled": false,
    "is_active": true
  }' \
  "http://localhost:8000/api/v1/resources" | jq
```

### Create API Endpoint

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "api",
    "name": "Trade Orders API",
    "code": "trade-orders-api",
    "parent_id": "f4656a18-cf27-472e-addb-769141a754f5",
    "attributes": {
      "description": "REST API for managing trade orders",
      "path": "/api/v1/orders",
      "methods": ["GET", "POST", "PUT", "DELETE"],
      "authentication": "JWT",
      "rate_limiting": {
        "requests_per_minute": 1000,
        "burst": 100
      },
      "documentation": "https://docs.example.com/api/orders",
      "version": "1.2.0"
    },
    "is_active": true
  }' \
  "http://localhost:8000/api/v1/resources" | jq
```

### Create Page/UI Component

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "page",
    "name": "Trading Dashboard",
    "code": "trading-dashboard",
    "parent_id": "f4656a18-cf27-472e-addb-769141a754f5",
    "attributes": {
      "description": "Real-time trading dashboard",
      "route": "/dashboard/trading",
      "components": [
        "OrderBook",
        "PriceChart", 
        "PositionSummary",
        "TradeHistory"
      ],
      "permissions_required": ["trading:read", "positions:read"],
      "refresh_interval": 1000,
      "layout": "grid-2x2"
    },
    "is_active": true
  }' \
  "http://localhost:8000/api/v1/resources" | jq
```

### Create Entity/Data Model

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "entity",
    "name": "Trade Order Entity",
    "code": "trade-order-entity",
    "parent_id": "f4656a18-cf27-472e-addb-769141a754f5",
    "attributes": {
      "description": "Trade order data model",
      "table_name": "trade_orders",
      "schema": {
        "id": {"type": "uuid", "primary_key": true},
        "symbol": {"type": "string", "required": true},
        "quantity": {"type": "decimal", "required": true},
        "price": {"type": "decimal", "required": true},
        "side": {"type": "enum", "values": ["buy", "sell"]},
        "status": {"type": "enum", "values": ["pending", "filled", "cancelled"]},
        "created_at": {"type": "timestamp", "default": "now()"},
        "updated_at": {"type": "timestamp", "auto_update": true}
      },
      "indexes": [
        {"fields": ["symbol", "status"]},
        {"fields": ["created_at"]}
      ],
      "relationships": [
        {"type": "belongs_to", "model": "User", "foreign_key": "user_id"},
        {"type": "has_many", "model": "TradeExecution", "foreign_key": "order_id"}
      ]
    },
    "is_active": true
  }' \
  "http://localhost:8000/api/v1/resources" | jq
```

---

## 5. Updating Resources

### Update Resource Name and Attributes

```bash
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Advanced Vessel Tracking Service",
    "attributes": {
      "description": "Enhanced vessel tracking with AI-powered analytics",
      "version": "2.0",
      "features": ["real-time-tracking", "predictive-analytics", "route-optimization"]
    }
  }' \
  "http://localhost:8000/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5" | jq
```

### Deactivate Resource

```bash
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }' \
  "http://localhost:8000/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5" | jq
```

### Enable Workflow

```bash
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_enabled": true,
    "workflow_config": {
      "approval_required": true,
      "approvers": ["service-owner", "architect"],
      "auto_deploy": false,
      "notifications": {
        "slack": "#deployments",
        "email": ["devops@company.com"]
      }
    }
  }' \
  "http://localhost:8000/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5" | jq
```

---

## 6. Moving Resources in Hierarchy

### Move Resource to Different Parent

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_parent_id": "ce3153e6-45e7-4f80-ae93-77fc72eae8cf"
  }' \
  "http://localhost:8000/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5/move" | jq
```

### Move Resource to Root Level

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_parent_id": null
  }' \
  "http://localhost:8000/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5/move" | jq
```

---

## 7. Getting Resource Details

### Get Single Resource with Full Details

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5" | jq
```

**Response:**
```json
{
  "id": "f4656a18-cf27-472e-addb-769141a754f5",
  "tenant_id": "e788a9e5-5898-45d6-9d64-a856f9bf3471",
  "type": "service",
  "name": "Vessel Tracking Service",
  "code": "vessel-tracking",
  "parent_id": "ab98f486-1983-4fcc-8778-2070c0010e8b",
  "path": "/87fd2b4c-7a62-4f44-b025-6574b4968630/ce3153e6-45e7-4f80-ae93-77fc72eae8cf/ab98f486-1983-4fcc-8778-2070c0010e8b/f4656a18-cf27-472e-addb-769141a754f5/",
  "attributes": {
    "description": "Track vessel positions and movements"
  },
  "workflow_enabled": false,
  "workflow_config": {},
  "is_active": true,
  "created_at": "2025-01-08T10:30:45.123Z",
  "updated_at": "2025-01-08T10:30:45.123Z",
  "depth": 3,
  "hierarchy_level_name": "Service",
  "ancestor_ids": [
    "87fd2b4c-7a62-4f44-b025-6574b4968630",
    "ce3153e6-45e7-4f80-ae93-77fc72eae8cf", 
    "ab98f486-1983-4fcc-8778-2070c0010e8b"
  ],
  "child_count": 3
}
```

### Get Child Resources

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5/children" | jq
```

### Get Resource Permissions

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/832d7613-f061-4da4-b78d-240a7125d50a/permissions" | jq
```

**Response:**
```json
{
  "resource_id": "832d7613-f061-4da4-b78d-240a7125d50a",
  "resource_name": "Vessel Entity",
  "resource_type": "entity",
  "permissions": [
    {
      "id": "409b0a66-d69a-4902-a177-ba93ee2974b8",
      "name": "entity_read_access",
      "actions": ["read"],
      "conditions": {},
      "field_permissions": {},
      "is_active": true
    },
    {
      "id": "f76ece6d-8fd0-4faa-bed9-bb9b2d1cefdb",
      "name": "entity_update_access",
      "actions": ["update"],
      "conditions": {},
      "field_permissions": {},
      "is_active": true
    }
  ]
}
```

---

## 8. Deleting Resources

### Soft Delete Single Resource

```bash
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5"
```

### Cascade Delete (Delete with Children)

```bash
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/f4656a18-cf27-472e-addb-769141a754f5?cascade=true"
```

---

## 9. Complex Query Examples

### Get All Services Under a Specific App

```bash
# First get the app ID, then filter services by parent hierarchy
APP_ID="ce3153e6-45e7-4f80-ae93-77fc72eae8cf"

curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources?type=service&search=vessel" | jq
```

### Get All Pages and APIs for a Frontend Developer

```bash
# Get pages
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources?type=page&is_active=true&limit=100" | jq '.items[] | {id, name, code, attributes}'

echo "---"

# Get APIs  
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources?type=api&is_active=true&limit=100" | jq '.items[] | {id, name, code, attributes}'
```

### Audit Trail: Get Recently Modified Resources

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources?sort_by=updated_at&sort_order=desc&limit=10" | jq '.items[] | {name, code, type, updated_at}'
```

---

## 10. Error Examples

### Hierarchy Validation Error

```bash
# Try to create an app under a service (invalid hierarchy)
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "app",
    "name": "Invalid App",
    "code": "invalid-app",
    "parent_id": "f4656a18-cf27-472e-addb-769141a754f5"
  }' \
  "http://localhost:8000/api/v1/resources" | jq
```

**Error Response:**
```json
{
  "error": {
    "message": "Invalid hierarchy: app cannot be a child of service. Valid parents: ['product_family']",
    "status_code": 400,
    "path": "/api/v1/resources",
    "method": "POST"
  }
}
```

### Duplicate Code Error

```bash
# Try to create resource with existing code
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "service",
    "name": "Another Vessel Service",
    "code": "vessel-tracking",
    "parent_id": "ab98f486-1983-4fcc-8778-2070c0010e8b"
  }' \
  "http://localhost:8000/api/v1/resources" | jq
```

**Error Response:**
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

### Permission Denied (Regular User)

```bash
# Login as regular user without global access
USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vessel.coord@maritime.com",
    "password": "password123",
    "tenant_code": "MARITIME"
  }' | jq -r '.access_token')

# Try to access resources from different tenant
curl -H "Authorization: Bearer $USER_TOKEN" \
  "http://localhost:8000/api/v1/resources/tree" | jq
```

This will only return resources from the user's tenant (MARITIME), not global resources.

---

## 11. Batch Operations Script

Here's a complete script to set up a sample resource hierarchy:

```bash
#!/bin/bash

# Get admin token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@sentinel.com",
    "password": "admin123", 
    "tenant_code": "PLATFORM"
  }' | jq -r '.access_token')

echo "Creating sample resource hierarchy..."

# 1. Create Product Family
PRODUCT_FAMILY=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "product_family",
    "name": "E-Commerce Platform",
    "code": "ecommerce-platform",
    "attributes": {"description": "Complete e-commerce solution"}
  }' \
  "http://localhost:8000/api/v1/resources" | jq -r '.id')

echo "Created Product Family: $PRODUCT_FAMILY"

# 2. Create Application
APP=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"app\",
    \"name\": \"Customer Portal\",
    \"code\": \"customer-portal\",
    \"parent_id\": \"$PRODUCT_FAMILY\",
    \"attributes\": {\"description\": \"Customer-facing web application\"}
  }" \
  "http://localhost:8000/api/v1/resources" | jq -r '.id')

echo "Created Application: $APP"

# 3. Create Capability
CAPABILITY=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"capability\",
    \"name\": \"Order Management\",
    \"code\": \"order-management\",
    \"parent_id\": \"$APP\",
    \"attributes\": {\"description\": \"Handle customer orders\"}
  }" \
  "http://localhost:8000/api/v1/resources" | jq -r '.id')

echo "Created Capability: $CAPABILITY"

# 4. Create Service
SERVICE=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"service\",
    \"name\": \"Order Processing Service\",
    \"code\": \"order-processing-service\",
    \"parent_id\": \"$CAPABILITY\",
    \"attributes\": {\"description\": \"Process and validate orders\"}
  }" \
  "http://localhost:8000/api/v1/resources" | jq -r '.id')

echo "Created Service: $SERVICE"

# 5. Create Page, Entity, API
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"page\",
    \"name\": \"Order Management Dashboard\",
    \"code\": \"order-dashboard\",
    \"parent_id\": \"$SERVICE\",
    \"attributes\": {\"route\": \"/orders/dashboard\"}
  }" \
  "http://localhost:8000/api/v1/resources" > /dev/null

curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"entity\",
    \"name\": \"Order Entity\",
    \"code\": \"order-entity\",
    \"parent_id\": \"$SERVICE\",
    \"attributes\": {\"table\": \"orders\"}
  }" \
  "http://localhost:8000/api/v1/resources" > /dev/null

curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"api\",
    \"name\": \"Orders API\",
    \"code\": \"orders-api\",
    \"parent_id\": \"$SERVICE\",
    \"attributes\": {\"path\": \"/api/v1/orders\"}
  }" \
  "http://localhost:8000/api/v1/resources" > /dev/null

echo "Created Page, Entity, and API"
echo "Resource hierarchy setup complete!"

# Show the final tree
echo ""
echo "Final resource tree:"
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/resources/tree" | jq '.tree'
```

These examples cover all the major use cases for the Resources API, from basic CRUD operations to complex hierarchical queries and error handling.