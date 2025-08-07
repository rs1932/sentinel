# Sentinel Access Platform - API Specifications

## Base Configuration
- Base URL: `https://api.sentinel-platform.com/v1`
- Authentication: Bearer token (JWT)
- Content-Type: `application/json`
- Rate Limiting: 1000 requests/minute per tenant

## API Categories

### 1. Authentication & Token Management APIs

#### 1.1 User Login
```http
POST /auth/login
```
**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "tenant_id": "GSC-001",
  "mfa_code": "123456" // Optional
}
```
**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "roles": ["logistics_manager"],
    "tenant": {
      "id": "GSC-001",
      "name": "Global Shipping Co."
    }
  }
}
```

#### 1.2 Service Account Authentication
```http
POST /auth/service-account/token
```
**Request:**
```json
{
  "client_id": "svc-port-sync",
  "client_secret": "encrypted_secret",
  "tenant_id": "GSC-001",
  "scope": "vessels:read vessels:update" // Optional
}
```

#### 1.3 Token Refresh
```http
POST /auth/refresh
```
**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 1.4 Token Revocation
```http
POST /auth/revoke
```
**Request:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "access_token" // or "refresh_token"
}
```

#### 1.5 Logout
```http
POST /auth/logout
```
**Headers:** `Authorization: Bearer {token}`

### 2. User Management APIs

#### 2.1 Create User
```http
POST /users
```
**Request:**
```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "initial_password", // Optional, can use invite flow
  "roles": ["viewer", "vessel_operator"],
  "groups": ["apac-team", "operations"],
  "attributes": {
    "department": "Operations",
    "location": "Singapore",
    "employee_id": "EMP001"
  },
  "send_invitation": true
}
```

#### 2.2 Get User Details
```http
GET /users/{user_id}
```
**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "tenant_id": "GSC-001",
  "roles": [
    {
      "id": "role-uuid",
      "name": "logistics_manager",
      "display_name": "Logistics Manager"
    }
  ],
  "groups": [
    {
      "id": "group-uuid",
      "name": "apac-team",
      "display_name": "Asia-Pacific Team"
    }
  ],
  "attributes": {
    "department": "Operations",
    "location": "Singapore"
  },
  "is_active": true,
  "last_login": "2024-03-15T10:30:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 2.3 Update User
```http
PATCH /users/{user_id}
```
**Request:**
```json
{
  "email": "newemail@example.com",
  "attributes": {
    "department": "Management"
  },
  "is_active": true
}
```

#### 2.4 List Users
```http
GET /users
```
**Query Parameters:**
- `tenant_id`: Filter by tenant
- `role`: Filter by role name
- `group`: Filter by group name
- `is_active`: Filter active/inactive
- `search`: Search by email/username
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)
- `sort`: Sort field (email, created_at, last_login)
- `order`: Sort order (asc, desc)

#### 2.5 Bulk User Operations
```http
POST /users/bulk
```
**Request:**
```json
{
  "operation": "activate", // activate, deactivate, delete, assign_role
  "user_ids": ["uuid1", "uuid2", "uuid3"],
  "data": {
    "role_id": "role-uuid" // For assign_role operation
  }
}
```

### 3. Role Management APIs

#### 3.1 Create Role
```http
POST /roles
```
**Request:**
```json
{
  "name": "port_inspector",
  "display_name": "Port Inspector",
  "description": "Inspector with vessel access at ports",
  "type": "custom",
  "parent_role_id": "viewer-role-uuid",
  "priority": 500,
  "is_assignable": true
}
```

#### 3.2 Get Role Details
```http
GET /roles/{role_id}
```
**Response includes inherited permissions**

#### 3.3 Update Role
```http
PATCH /roles/{role_id}
```

#### 3.4 List Roles
```http
GET /roles
```
**Query Parameters:**
- `tenant_id`: Filter by tenant
- `type`: Filter by role type (system, custom)
- `is_assignable`: Filter assignable roles
- `include_permissions`: Include permission details (default: false)

#### 3.5 Assign Permissions to Role
```http
POST /roles/{role_id}/permissions
```
**Request:**
```json
{
  "permissions": [
    {
      "resource_type": "vessel",
      "resource_id": "*", // Wildcard for all vessels
      "actions": ["read", "update"],
      "conditions": {
        "vessel_status": ["In Port", "Docked"],
        "attributes.region": "APAC"
      },
      "field_permissions": {
        "vessel_name": ["read"],
        "imo_number": ["read"],
        "custom_attributes.hazardousMaterialCode": ["read", "write"],
        "tenant_attributes.portInspectionNotes": ["read", "write"]
      }
    }
  ]
}
```

#### 3.6 Remove Permission from Role
```http
DELETE /roles/{role_id}/permissions/{permission_id}
```

#### 3.7 Get Role Permissions
```http
GET /roles/{role_id}/permissions
```
**Response:**
```json
{
  "direct_permissions": [...],
  "inherited_permissions": [...],
  "effective_permissions": [...]
}
```

### 4. Group Management APIs

#### 4.1 Create Group
```http
POST /groups
```
**Request:**
```json
{
  "name": "apac-operations",
  "display_name": "APAC Operations Team",
  "description": "Operations team for Asia-Pacific region",
  "parent_group_id": "operations-group-uuid",
  "metadata": {
    "region": "APAC",
    "cost_center": "CC-001"
  }
}
```

#### 4.2 Add Users to Group
```http
POST /groups/{group_id}/users
```
**Request:**
```json
{
  "user_ids": ["user-uuid-1", "user-uuid-2"]
}
```

#### 4.3 Remove User from Group
```http
DELETE /groups/{group_id}/users/{user_id}
```

#### 4.4 Assign Roles to Group
```http
POST /groups/{group_id}/roles
```
**Request:**
```json
{
  "role_ids": ["role-uuid-1", "role-uuid-2"]
}
```

#### 4.5 List Group Members
```http
GET /groups/{group_id}/users
```

#### 4.6 List Group Roles
```http
GET /groups/{group_id}/roles
```

### 5. Permission Evaluation APIs

#### 5.1 Check Single Permission
```http
POST /permissions/check
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "resource": {
    "type": "vessel",
    "id": "vessel-001",
    "attributes": {
      "status": "In Port",
      "region": "APAC"
    }
  },
  "action": "update",
  "context": {
    "workflow_state": "docked",
    "time": "2024-03-15T10:00:00Z"
  }
}
```
**Response:**
```json
{
  "allowed": true,
  "reason": "Permission granted through role: port_inspector",
  "matched_conditions": {
    "vessel_status": "In Port",
    "region": "APAC"
  },
  "field_permissions": {
    "vessel_name": ["read"],
    "imo_number": ["read"],
    "custom_attributes.hazardousMaterialCode": ["read", "write"]
  },
  "ttl": 300 // Cache time in seconds
}
```

#### 5.2 Batch Permission Check
```http
POST /permissions/batch-check
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "checks": [
    {
      "resource": {
        "type": "vessel",
        "id": "vessel-001"
      },
      "action": "read"
    },
    {
      "resource": {
        "type": "app",
        "id": "fleet-management"
      },
      "action": "execute"
    }
  ]
}
```
**Response:**
```json
{
  "results": [
    {
      "resource": "vessel:vessel-001",
      "action": "read",
      "allowed": true
    },
    {
      "resource": "app:fleet-management",
      "action": "execute",
      "allowed": false
    }
  ]
}
```

#### 5.3 Get User Effective Permissions
```http
GET /users/{user_id}/permissions
```
**Query Parameters:**
- `resource_type`: Filter by resource type
- `include_inherited`: Include inherited permissions (default: true)
- `include_conditions`: Include ABAC conditions (default: false)

### 6. Resource Management APIs

#### 6.1 Create Resource
```http
POST /resources
```
**Request:**
```json
{
  "type": "app",
  "name": "Vessel Operations",
  "code": "vessel-ops",
  "parent_id": "fleet-mgmt-uuid", // Product family ID
  "attributes": {
    "version": "2.0",
    "modules": ["tracking", "maintenance"]
  },
  "workflow_enabled": true,
  "workflow_config": {
    "states": ["planning", "active", "maintenance", "decommissioned"],
    "initial_state": "planning"
  }
}
```

#### 6.2 Get Resource Hierarchy
```http
GET /resources/tree
```
**Query Parameters:**
- `root_id`: Start from specific resource (optional)
- `depth`: Maximum depth to traverse
- `type`: Filter by resource type

**Response:**
```json
{
  "tree": {
    "id": "fleet-mgmt-uuid",
    "type": "product_family",
    "name": "Fleet Management",
    "children": [
      {
        "id": "vessel-ops-uuid",
        "type": "app",
        "name": "Vessel Operations",
        "children": [...]
      }
    ]
  }
}
```

#### 6.3 Update Resource
```http
PATCH /resources/{resource_id}
```

#### 6.4 Get Resource Permissions
```http
GET /resources/{resource_id}/permissions
```
**Get all permissions defined for a resource**

### 7. Field Definition APIs

#### 7.1 Create Field Definition
```http
POST /field-definitions
```
**Request:**
```json
{
  "entity_type": "vessel",
  "field_name": "hazardousMaterialCode",
  "field_type": "platform_dynamic",
  "data_type": "string",
  "storage_path": "custom_attributes.hazardousMaterialCode",
  "display_name": "Hazmat Code",
  "description": "UN hazardous material classification",
  "validation_rules": {
    "pattern": "^UN[0-9]{4}$",
    "required": false
  },
  "default_visibility": "read",
  "is_indexed": true
}
```

#### 7.2 List Field Definitions
```http
GET /field-definitions
```
**Query Parameters:**
- `entity_type`: Filter by entity (vessel, container, etc.)
- `field_type`: Filter by tier (core, platform_dynamic, tenant_specific)
- `tenant_id`: For tenant-specific fields

#### 7.3 Update Field Definition
```http
PATCH /field-definitions/{field_id}
```

#### 7.4 Get Field Permissions for User
```http
GET /field-permissions
```
**Query Parameters:**
- `user_id`: User to check
- `entity_type`: Entity type
- `entity_id`: Specific entity instance
- `fields`: Comma-separated field names

**Response:**
```json
{
  "field_permissions": {
    "vessel_name": ["read"],
    "imo_number": ["read"],
    "custom_attributes.hazardousMaterialCode": ["read", "write"],
    "tenant_attributes.internalAuditID": []
  }
}
```

### 8. Navigation/Menu APIs

#### 8.1 Get User Menu
```http
GET /navigation/menu
```
**Query Parameters:**
- `user_id`: User ID (defaults to current user)
- `include_hidden`: Include hidden items (default: false)

**Response:**
```json
{
  "menu_items": [
    {
      "id": "fleet-mgmt",
      "name": "fleet_management",
      "display_name": "Fleet Management",
      "icon": "ship",
      "url": null,
      "visible": true,
      "children": [
        {
          "id": "vessel-ops",
          "name": "vessel_operations",
          "display_name": "Vessel Operations",
          "icon": "anchor",
          "url": "/fleet/vessels",
          "visible": true,
          "required_permission": "vessel:read",
          "children": []
        }
      ]
    }
  ]
}
```

#### 8.2 Customize User Menu
```http
POST /navigation/customize
```
**Request:**
```json
{
  "customizations": [
    {
      "menu_item_id": "vessel-ops",
      "is_hidden": false,
      "custom_order": 1
    }
  ]
}
```

### 9. Audit & Compliance APIs

#### 9.1 Query Audit Logs
```http
GET /audit/logs
```
**Query Parameters:**
- `tenant_id`: Filter by tenant
- `actor_id`: Filter by user
- `action`: Filter by action type
- `resource_type`: Filter by resource type
- `resource_id`: Filter by specific resource
- `from_date`: Start date (ISO 8601)
- `to_date`: End date (ISO 8601)
- `result`: Filter by result (success, failure, denied)
- `page`: Page number
- `limit`: Items per page

**Response:**
```json
{
  "logs": [
    {
      "id": "audit-uuid",
      "tenant_id": "GSC-001",
      "actor_id": "user-uuid",
      "actor_type": "user",
      "action": "permission.check",
      "resource_type": "vessel",
      "resource_id": "vessel-001",
      "changes": {
        "fields_accessed": ["vessel_name", "imo_number"]
      },
      "result": "success",
      "created_at": "2024-03-15T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 1250,
    "page": 1,
    "limit": 50,
    "pages": 25
  }
}
```

#### 9.2 Export Audit Report
```http
POST /audit/export
```
**Request:**
```json
{
  "format": "csv", // csv, json, pdf
  "filters": {
    "from_date": "2024-01-01T00:00:00Z",
    "to_date": "2024-03-31T23:59:59Z",
    "actions": ["user.create", "role.assign", "permission.grant"]
  },
  "email": "admin@example.com" // Optional, for async delivery
}
```

### 10. Tenant Management APIs (Admin Only)

#### 10.1 Create Tenant
```http
POST /tenants
```
**Request:**
```json
{
  "name": "Pacific Shipping Lines",
  "code": "PSL-001",
  "type": "root",
  "isolation_mode": "shared",
  "settings": {
    "max_users": 500,
    "features": ["vessel_tracking", "crew_management"]
  }
}
```

#### 10.2 Create Sub-Tenant
```http
POST /tenants/{parent_tenant_id}/sub-tenants
```

#### 10.3 Update Tenant Settings
```http
PATCH /tenants/{tenant_id}
```

#### 10.4 List Tenants
```http
GET /tenants
```
**Only available to super admins**

### 11. Service Account Management APIs

#### 11.1 Create Service Account
```http
POST /service-accounts
```
**Request:**
```json
{
  "name": "Port Integration Service",
  "description": "Automated port data synchronization",
  "roles": ["vessel_updater"],
  "attributes": {
    "service_type": "integration",
    "allowed_ips": ["192.168.1.0/24"]
  }
}
```
**Response:**
```json
{
  "id": "svc-account-uuid",
  "client_id": "svc-port-integration",
  "client_secret": "generated-secret-key",
  "created_at": "2024-03-15T10:00:00Z"
}
```

#### 11.2 Rotate Service Account Credentials
```http
POST /service-accounts/{account_id}/rotate-credentials
```

### 12. Cache Management APIs

#### 12.1 Clear Permission Cache
```http
POST /cache/clear
```
**Request:**
```json
{
  "type": "permissions", // permissions, roles, menus, all
  "scope": "user", // user, role, tenant, all
  "target_id": "user-uuid" // Optional, depending on scope
}
```

#### 12.2 Get Cache Statistics
```http
GET /cache/stats
```
**Response:**
```json
{
  "cache_type": "permissions",
  "hit_rate": 0.92,
  "miss_rate": 0.08,
  "total_requests": 150000,
  "cache_size_mb": 45.2,
  "avg_response_time_ms": {
    "cached": 12,
    "uncached": 187
  }
}
```

### 13. Health & Monitoring APIs

#### 13.1 Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "version": "1.2.0",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "auth": "healthy",
    "ai_engine": "healthy"
  },
  "timestamp": "2024-03-15T10:00:00Z"
}
```

#### 13.2 Metrics Endpoint
```http
GET /metrics
```
**Prometheus-compatible metrics**

## 14. AI & Intelligence APIs

### 14.1 Anomaly Detection APIs

#### 14.1.1 Check Access Anomaly
```http
POST /ai/anomaly/check
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "access_request": {
    "resource_type": "vessel",
    "resource_id": "vessel-001",
    "action": "export",
    "context": {
      "ip_address": "192.168.1.1",
      "location": "Singapore",
      "time": "2024-03-15T03:00:00Z",
      "session_id": "session-uuid"
    }
  }
}
```
**Response:**
```json
{
  "anomaly_detected": true,
  "risk_score": 0.85,
  "anomaly_types": [
    {
      "type": "unusual_time",
      "confidence": 0.92,
      "baseline": "User typically accesses 09:00-18:00"
    },
    {
      "type": "unusual_action",
      "confidence": 0.78,
      "baseline": "User has never performed 'export' action"
    }
  ],
  "recommended_actions": [
    "require_mfa",
    "alert_security",
    "log_detailed_audit"
  ],
  "explanation": "Access pattern deviates significantly from user's historical behavior"
}
```

#### 14.1.2 Get User Behavior Profile
```http
GET /ai/anomaly/profile/{user_id}
```
**Response:**
```json
{
  "user_id": "user-uuid",
  "behavior_profile": {
    "typical_hours": "09:00-18:00",
    "common_resources": ["vessels", "terminals", "reports"],
    "access_frequency": {
      "daily_average": 45,
      "peak_hour": "10:00"
    },
    "location_pattern": ["Singapore", "Malaysia"],
    "risk_baseline": 0.15
  },
  "last_updated": "2024-03-15T00:00:00Z"
}
```

#### 14.1.3 Report False Positive
```http
POST /ai/anomaly/feedback
```
**Request:**
```json
{
  "detection_id": "anomaly-uuid",
  "feedback": "false_positive",
  "reason": "Scheduled maintenance window",
  "reported_by": "admin-uuid"
}
```

### 14.2 Permission Optimization APIs

#### 14.2.1 Analyze User Permissions
```http
POST /ai/optimizer/analyze-user
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "analysis_period_days": 90,
  "include_predictions": true
}
```
**Response:**
```json
{
  "user_id": "user-uuid",
  "analysis": {
    "unused_permissions": [
      {
        "permission": "vessel:delete",
        "last_used": null,
        "recommendation": "remove",
        "confidence": 0.95
      }
    ],
    "over_privileged_score": 0.67,
    "role_efficiency": 0.45,
    "suggested_changes": [
      {
        "action": "remove_role",
        "role": "admin",
        "reason": "Only 2% of permissions used"
      },
      {
        "action": "add_role",
        "role": "vessel_viewer",
        "reason": "Covers 95% of actual usage"
      }
    ],
    "predicted_future_needs": [
      {
        "permission": "terminal:singapore:read",
        "probability": 0.78,
        "based_on": "team_pattern"
      }
    ]
  }
}
```

#### 14.2.2 Optimize Tenant Roles
```http
POST /ai/optimizer/analyze-tenant
```
**Request:**
```json
{
  "tenant_id": "tenant-uuid",
  "optimization_goals": ["reduce_roles", "improve_security", "simplify_management"]
}
```
**Response:**
```json
{
  "tenant_id": "tenant-uuid",
  "recommendations": {
    "role_consolidation": [
      {
        "merge_roles": ["viewer", "reporter", "analyst"],
        "into_role": "read_only_user",
        "affected_users": 45,
        "complexity_reduction": "32%"
      }
    ],
    "permission_cleanup": {
      "unused_permissions": 124,
      "redundant_assignments": 67,
      "conflicting_permissions": 3
    },
    "security_improvements": [
      {
        "issue": "excessive_admin_users",
        "current": 15,
        "recommended": 3,
        "risk_reduction": "78%"
      }
    ]
  },
  "implementation_plan": {
    "phases": 3,
    "estimated_hours": 12,
    "risk_level": "low"
  }
}
```

### 14.3 Natural Language Interface APIs

#### 14.3.1 Natural Language Query
```http
POST /ai/nlp/query
```
**Request:**
```json
{
  "query": "Who has access to vessel MSC-MOONLIGHT in Singapore port?",
  "context": {
    "user_id": "current-user-uuid",
    "include_details": true
  }
}
```
**Response:**
```json
{
  "interpretation": {
    "intent": "list_resource_access",
    "entities": {
      "resource_type": "vessel",
      "resource_id": "MSC-MOONLIGHT",
      "location": "Singapore port"
    }
  },
  "answer": {
    "text": "5 users have access to vessel MSC-MOONLIGHT in Singapore port",
    "data": [
      {
        "user": "Sarah Chen",
        "role": "Shipping Agent",
        "access_level": "full",
        "valid_until": "2024-12-31"
      },
      {
        "user": "Port Authority Team",
        "role": "Port Authority",
        "access_level": "read",
        "valid_until": null
      }
    ]
  },
  "confidence": 0.94
}
```

#### 14.3.2 Natural Language Command
```http
POST /ai/nlp/command
```
**Request:**
```json
{
  "command": "Grant John temporary access to all vessels arriving tomorrow",
  "confirmation_required": true
}
```
**Response:**
```json
{
  "interpretation": {
    "action": "grant_permission",
    "target_user": "john.doe@example.com",
    "permissions": {
      "resource_type": "vessel",
      "filter": "arriving_date = 2024-03-16",
      "access_type": "temporary",
      "duration": "24_hours"
    }
  },
  "confirmation": {
    "message": "Grant John Doe (john.doe@example.com) temporary read access to 7 vessels arriving on March 16, 2024 for 24 hours?",
    "affected_resources": [
      "MSC-MOONLIGHT",
      "EVERGREEN-STAR",
      "MAERSK-TRIUMPH"
    ],
    "confirmation_token": "confirm-uuid-token"
  },
  "warnings": []
}
```

#### 14.3.3 Execute NLP Command
```http
POST /ai/nlp/execute
```
**Request:**
```json
{
  "confirmation_token": "confirm-uuid-token",
  "confirmed": true
}
```

### 14.4 Predictive Access APIs

#### 14.4.1 Predict Access Needs
```http
POST /ai/predictive/predict
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "prediction_window_hours": 24,
  "context": {
    "upcoming_vessels": ["vessel-001", "vessel-002"],
    "scheduled_tasks": ["inspection", "clearance"]
  }
}
```
**Response:**
```json
{
  "predictions": [
    {
      "resource": "vessel:vessel-001",
      "probability": 0.92,
      "predicted_time": "2024-03-16T09:00:00Z",
      "reason": "Historical pattern: accesses vessels 3 hours before arrival",
      "suggested_action": "pre_grant_access",
      "suggested_duration": "24_hours"
    },
    {
      "resource": "document:manifest-001",
      "probability": 0.85,
      "predicted_time": "2024-03-16T10:00:00Z",
      "reason": "Related to vessel-001 inspection task"
    }
  ]
}
```

#### 14.4.2 Auto-Provision Predicted Access
```http
POST /ai/predictive/auto-provision
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "threshold": 0.80,
  "max_duration_hours": 48,
  "require_approval": false
}
```

### 14.5 Compliance Monitoring APIs

#### 14.5.1 Check Compliance Status
```http
GET /ai/compliance/status
```
**Query Parameters:**
- `tenant_id`: Specific tenant
- `regulation`: GDPR, SOX, ISPS, etc.

**Response:**
```json
{
  "compliance_status": {
    "overall": "warning",
    "regulations": {
      "GDPR": {
        "status": "compliant",
        "score": 0.95,
        "last_audit": "2024-03-01T00:00:00Z"
      },
      "ISPS": {
        "status": "warning",
        "score": 0.72,
        "issues": [
          {
            "severity": "medium",
            "description": "Crew list access not properly restricted",
            "affected_users": 12,
            "remediation": "Apply crew_list_viewer role restriction"
          }
        ]
      }
    }
  },
  "recommendations": [
    {
      "priority": "high",
      "regulation": "ISPS",
      "action": "restrict_crew_data_access",
      "estimated_effort": "2_hours"
    }
  ]
}
```

#### 14.5.2 Generate Compliance Report
```http
POST /ai/compliance/report
```
**Request:**
```json
{
  "tenant_id": "tenant-uuid",
  "regulations": ["GDPR", "SOX", "ISPS"],
  "period": {
    "from": "2024-01-01",
    "to": "2024-03-31"
  },
  "format": "pdf",
  "include_recommendations": true
}
```

### 14.6 AI Training & Management APIs

#### 14.6.1 Train AI Model
```http
POST /ai/training/start
```
**Request:**
```json
{
  "model_type": "anomaly_detection",
  "training_data": {
    "source": "audit_logs",
    "date_range": {
      "from": "2024-01-01",
      "to": "2024-03-01"
    }
  },
  "parameters": {
    "algorithm": "isolation_forest",
    "contamination": 0.01
  }
}
```
**Response:**
```json
{
  "training_job_id": "job-uuid",
  "status": "started",
  "estimated_completion": "2024-03-15T12:00:00Z"
}
```

#### 14.6.2 Get AI Model Status
```http
GET /ai/models
```
**Response:**
```json
{
  "models": [
    {
      "model_id": "anomaly-detector-v2",
      "type": "anomaly_detection",
      "status": "active",
      "accuracy": 0.94,
      "last_trained": "2024-03-10T00:00:00Z",
      "training_samples": 1000000
    },
    {
      "model_id": "permission-predictor-v1",
      "type": "predictive_access",
      "status": "training",
      "progress": 67,
      "eta": "2024-03-15T14:00:00Z"
    }
  ]
}
```

#### 14.6.3 Configure AI Agent
```http
PUT /ai/agents/{agent_type}/config
```
**Request:**
```json
{
  "agent_type": "anomaly_detector",
  "configuration": {
    "sensitivity": 0.7,
    "auto_block_threshold": 0.95,
    "alert_channels": ["email", "slack"],
    "learning_mode": "continuous"
  }
}
```

### 14.7 AI Explanation & Transparency APIs

#### 14.7.1 Explain AI Decision
```http
GET /ai/explain/{decision_id}
```
**Response:**
```json
{
  "decision_id": "decision-uuid",
  "decision_type": "access_denied",
  "timestamp": "2024-03-15T10:00:00Z",
  "explanation": {
    "primary_factors": [
      {
        "factor": "anomaly_score",
        "value": 0.89,
        "weight": 0.4,
        "description": "Access pattern highly unusual"
      },
      {
        "factor": "resource_sensitivity",
        "value": "high",
        "weight": 0.3,
        "description": "Accessing financial data"
      }
    ],
    "model_confidence": 0.87,
    "alternative_decision": {
      "action": "require_mfa",
      "probability": 0.13
    }
  },
  "override_available": true,
  "override_reason_required": true
}
```

#### 14.7.2 Override AI Decision
```http
POST /ai/override
```
**Request:**
```json
{
  "decision_id": "decision-uuid",
  "override_action": "allow_access",
  "reason": "Scheduled maintenance window",
  "override_by": "admin-uuid"
}
```

## Standard Response Formats

### Success Response
```json
{
  "data": {}, // The actual response data
  "meta": {
    "request_id": "req-uuid",
    "timestamp": "2024-03-15T10:00:00Z"
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "You do not have permission to perform this action",
    "details": {
      "required_permission": "vessel:update",
      "user_permissions": ["vessel:read"]
    }
  },
  "meta": {
    "request_id": "req-uuid",
    "timestamp": "2024-03-15T10:00:00Z"
  }
}
```

### Standard Error Codes
- `AUTHENTICATION_REQUIRED`: 401
- `PERMISSION_DENIED`: 403
- `RESOURCE_NOT_FOUND`: 404
- `VALIDATION_ERROR`: 400
- `CONFLICT`: 409
- `RATE_LIMIT_EXCEEDED`: 429
- `INTERNAL_ERROR`: 500

## Rate Limiting Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1458892800
X-RateLimit-Retry-After: 60
```

## Pagination Headers
```
X-Total-Count: 250
X-Page-Count: 5
X-Current-Page: 1
X-Per-Page: 50
```