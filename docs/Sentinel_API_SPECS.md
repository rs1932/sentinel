# Sentinel Access Platform - API Specifications
## Version 2.0 - Complete API with All Features

## Base Configuration
- Base URL: `https://api.sentinel-platform.com/v1`
- Authentication: Bearer token (JWT)
- Content-Type: `application/json`
- Rate Limiting: 1000 requests/minute per tenant
- Python Version: 3.10 (Backend requirement)
- Database Schema: All tables in `sentinel` namespace
- Cache: In-memory by default, Redis optional

## API Categories

### 1. Authentication & Token Management APIs

#### 1.1 User Login
```http
POST /auth/login
```
**Note**: Regular users only. Service accounts must use `/auth/service-account/token`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "tenant_id": "11111111-1111-1111-1111-111111111111",
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
    "is_service_account": false,
    "roles": ["logistics_manager"],
    "tenant": {
      "id": "11111111-1111-1111-1111-111111111111",
      "name": "Test Company",
      "code": "TEST-001"
    }
  }
}
```

#### 1.2 Service Account Authentication
```http
POST /auth/service-account/token
```
**Note**: Service accounts are stored in users table with `is_service_account=true`

**Request:**
```json
{
  "api_key": "svc_key_64_character_string...",
  "tenant_id": "11111111-1111-1111-1111-111111111111"
}
```
**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 7200,
  "service_account": {
    "id": "svc-uuid",
    "email": "svc-port-sync@system.local",
    "is_service_account": true,
    "tenant_id": "11111111-1111-1111-1111-111111111111"
  }
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
  "token_type": "access_token", // or "refresh_token"
  "jti": "token-id-for-blacklisting"
}
```

#### 1.5 Logout
```http
POST /auth/logout
```
**Headers:** `Authorization: Bearer {token}`

**Note**: Adds token to blacklist in `sentinel.token_blacklist` table

### 2. User Management APIs (Including Service Accounts)

#### 2.1 Create User
```http
POST /users
```
**Request (Regular User):**
```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "initial_password",
  "is_service_account": false,
  "roles": ["viewer", "vessel_operator"],
  "groups": ["apac-team", "operations"],
  "attributes": {
    "department": "Operations",
    "location": "Singapore",
    "employee_id": "EMP001"
  },
  "preferences": {
    "theme": "dark",
    "notifications": true
  },
  "send_invitation": true
}
```

**Request (Service Account):**
```json
{
  "email": "svc-integration@system.local",
  "username": "svc-integration",
  "is_service_account": true,
  "service_account_key": null, // Auto-generated if null
  "roles": ["api_reader"],
  "attributes": {
    "service_type": "integration",
    "allowed_ips": ["192.168.1.0/24"]
  }
}
```

**Response (201):**
```json
{
  "id": "user-uuid",
  "email": "svc-integration@system.local",
  "is_service_account": true,
  "service_account_key": "svc_key_generated_64_chars...", // Only for service accounts
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "created_at": "2024-03-15T10:00:00Z"
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
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "is_service_account": false,
  "roles": [
    {
      "id": "role-uuid",
      "name": "logistics_manager",
      "display_name": "Logistics Manager",
      "type": "custom",
      "priority": 500
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
  "preferences": {},
  "is_active": true,
  "last_login": "2024-03-15T10:30:00Z",
  "login_count": 42,
  "failed_login_count": 0,
  "locked_until": null,
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
- `is_service_account`: Filter service accounts (true/false)
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
  "exclude_service_accounts": true, // Optional safety flag
  "data": {
    "role_id": "role-uuid" // For assign_role operation
  }
}
```

#### 2.6 Rotate Service Account Credentials
```http
POST /users/{user_id}/rotate-credentials
```
**Note**: Only for users with `is_service_account=true`

**Response:**
```json
{
  "id": "user-uuid",
  "new_api_key": "svc_key_new_64_character_string...",
  "expires_at": "2024-06-15T00:00:00Z"
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
  "is_assignable": true,
  "metadata": {
    "category": "operations",
    "risk_level": "medium"
  }
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

#### 3.5 Assign Permissions to Role (With Three-Tier Fields)
```http
POST /roles/{role_id}/permissions
```
**Request:**
```json
{
  "permissions": [
    {
      "resource_type": "vessel",
      "resource_id": null,
      "resource_path": "vessel/*", // Wildcard for all vessels
      "actions": ["read", "update"],
      "conditions": {
        "vessel_status": ["In Port", "Docked"],
        "attributes.region": "APAC"
      },
      "field_permissions": {
        "core": {
          "vessel_name": ["read", "write"],
          "imo_number": ["read"]
        },
        "platform_dynamic": {
          "hazardousMaterialCode": ["read", "write"],
          "lastInspectionDate": ["read"]
        },
        "tenant_specific": {
          "portInspectionNotes": ["read", "write"],
          "internalAuditID": ["read"]
        }
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
  "user_ids": ["user-uuid-1", "user-uuid-2"],
  "exclude_service_accounts": true // Optional, prevents adding service accounts
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

#### 5.1 Check Single Permission (With Approval Chain Integration)
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
  },
  "justification": "Routine maintenance update" // For approval requests
}
```
**Response (Permission Granted):**
```json
{
  "allowed": true,
  "reason": "Permission granted through role: port_inspector",
  "matched_conditions": {
    "vessel_status": "In Port",
    "region": "APAC"
  },
  "field_permissions": {
    "core": {
      "vessel_name": ["read", "write"],
      "imo_number": ["read"]
    },
    "platform_dynamic": {
      "hazardousMaterialCode": ["read", "write"]
    },
    "tenant_specific": {
      "portInspectionNotes": ["read", "write"]
    }
  },
  "ttl": 300 // Cache time in seconds
}
```

**Response (Approval Required):**
```json
{
  "allowed": false,
  "requires_approval": true,
  "approval_chain_id": "chain-uuid",
  "approval_request_id": "request-uuid",
  "reason": "This action requires approval",
  "approval_levels": [
    {
      "level": 1,
      "approver_role": "manager",
      "timeout_hours": 24
    }
  ]
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
      "allowed": true,
      "requires_approval": false
    },
    {
      "resource": "app:fleet-management",
      "action": "execute",
      "allowed": false,
      "requires_approval": true,
      "approval_chain_id": "chain-uuid"
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
- `include_field_permissions`: Include field-level permissions (default: true)

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
  "path": null, // Auto-generated from hierarchy
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
    "path": "/fleet-mgmt-uuid/",
    "children": [
      {
        "id": "vessel-ops-uuid",
        "type": "app",
        "name": "Vessel Operations",
        "path": "/fleet-mgmt-uuid/vessel-ops-uuid/",
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

### 7. Field Definition APIs (Three-Tier Model)

#### 7.1 Create Field Definition
```http
POST /field-definitions
```
**Request:**
```json
{
  "tenant_id": null, // null for platform-wide, UUID for tenant-specific
  "entity_type": "vessel",
  "field_name": "hazardousMaterialCode",
  "field_type": "platform_dynamic", // core, platform_dynamic, or tenant_specific
  "data_type": "string",
  "storage_column": null, // Only for core fields
  "storage_path": "custom_attributes.hazardousMaterialCode", // For dynamic fields
  "display_name": "Hazmat Code",
  "description": "UN hazardous material classification",
  "validation_rules": {
    "pattern": "^UN[0-9]{4}$",
    "required": false
  },
  "default_visibility": "read",
  "is_indexed": true,
  "is_required": false
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
    "core": {
      "vessel_name": ["read", "write"],
      "imo_number": ["read"]
    },
    "platform_dynamic": {
      "hazardousMaterialCode": ["read", "write"],
      "lastInspectionDate": ["read"]
    },
    "tenant_specific": {
      "internalAuditID": ["hidden"],
      "customNote": ["read", "write"]
    }
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
      "parent_id": null,
      "name": "fleet_management",
      "display_name": "Fleet Management",
      "icon": "ship",
      "url": null,
      "resource_id": "fleet-mgmt-uuid",
      "required_permission": null,
      "display_order": 1,
      "is_visible": true,
      "children": [
        {
          "id": "vessel-ops",
          "parent_id": "fleet-mgmt",
          "name": "vessel_operations",
          "display_name": "Vessel Operations",
          "icon": "anchor",
          "url": "/fleet/vessels",
          "resource_id": "vessel-ops-uuid",
          "required_permission": "vessel:read",
          "display_order": 1,
          "is_visible": true,
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
- `actor_type`: Filter by actor type (user, service_account, system)
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
      "tenant_id": "11111111-1111-1111-1111-111111111111",
      "actor_id": "user-uuid",
      "actor_type": "user",
      "action": "permission.check",
      "resource_type": "vessel",
      "resource_id": "vessel-001",
      "resource_details": {},
      "changes": {
        "fields_accessed": ["vessel_name", "imo_number"]
      },
      "result": "success",
      "error_details": null,
      "metadata": {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
      },
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
  "parent_tenant_id": null,
  "isolation_mode": "shared",
  "settings": {
    "max_users": 500,
    "features": ["vessel_tracking", "crew_management"]
  },
  "features": ["approval_chains", "biometrics", "ai_features"],
  "metadata": {
    "industry": "maritime",
    "size": "enterprise"
  }
}
```

#### 10.2 Create Sub-Tenant
```http
POST /tenants/{parent_tenant_id}/sub-tenants
```
**Request:**
```json
{
  "name": "PSL Singapore Branch",
  "code": "PSL-SG-001",
  "type": "sub_tenant",
  "isolation_mode": "shared",
  "settings": {
    "inherit_permissions": true
  }
}
```

#### 10.3 Update Tenant Settings
```http
PATCH /tenants/{tenant_id}
```

#### 10.4 List Tenants
```http
GET /tenants
```
**Only available to super admins with platform tenant access**

### 11. Approval Chain Management APIs (NEW)

#### 11.1 Create Approval Chain
```http
POST /approval-chains
```
**Request:**
```json
{
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "name": "Sensitive Data Access",
  "resource_type": "sensitive_data",
  "resource_pattern": "sensitive_data:*",
  "approval_levels": [
    {
      "level": 1,
      "approver_role": "manager",
      "timeout_hours": 24,
      "escalate_to_level": 2
    },
    {
      "level": 2,
      "approver_role": "director",
      "timeout_hours": 48,
      "final": true
    }
  ],
  "auto_approve_conditions": {
    "user_attributes.clearance_level": ["top_secret"],
    "time_range": ["09:00", "17:00"]
  },
  "is_active": true
}
```

#### 11.2 Create Access Request
```http
POST /access-requests
```
**Request:**
```json
{
  "requester_id": "user-uuid",
  "request_type": "permission",
  "request_details": {
    "resource_type": "sensitive_data",
    "resource_id": "doc-001",
    "action": "read",
    "duration_hours": 24
  },
  "justification": "Need access for quarterly audit",
  "expires_at": "2024-03-16T10:00:00Z"
}
```

#### 11.3 Approve/Deny Access Request
```http
POST /access-requests/{request_id}/approve
```
**Request:**
```json
{
  "approver_id": "manager-uuid",
  "decision": "approved", // or "denied"
  "comments": "Approved for audit purposes",
  "approval_level": 1
}
```

#### 11.4 Get Pending Approvals
```http
GET /access-requests/pending
```
**Query Parameters:**
- `approver_id`: Get approvals for specific approver
- `include_escalated`: Include escalated requests

#### 11.5 Get Approval Chain Status
```http
GET /approval-chains/{chain_id}/status
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
  "target_id": "user-uuid", // Optional, depending on scope
  "cache_backend": "memory" // Current cache backend being used
}
```

#### 12.2 Get Cache Statistics
```http
GET /cache/stats
```
**Response:**
```json
{
  "cache_backend": "memory", // or "redis"
  "cache_type": "permissions",
  "hit_rate": 0.92,
  "miss_rate": 0.08,
  "total_requests": 150000,
  "cache_entries": 2500,
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
  "version": "2.0.0",
  "python_version": "3.10",
  "cache_backend": "memory",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "auth": "healthy",
    "ai_engine": "healthy",
    "biometrics": "disabled"
  },
  "timestamp": "2024-03-15T10:00:00Z"
}
```

#### 13.2 Metrics Endpoint
```http
GET /metrics
```
**Prometheus-compatible metrics including:**
- Authentication attempts by account type
- Permission checks with approval requirements
- Cache operations by backend type
- Biometric deviation scores

### 14. AI & Intelligence APIs

#### 14.1 Anomaly Detection APIs

##### 14.1.1 Check Access Anomaly
```http
POST /ai/anomaly/check
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "session_id": "session-uuid", // For biometric correlation
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
  "confidence": 0.92,
  "anomaly_types": [
    {
      "type": "unusual_time",
      "confidence": 0.92,
      "baseline": "User typically accesses 09:00-18:00"
    },
    {
      "type": "behavioral_deviation",
      "confidence": 0.78,
      "baseline": "Keystroke pattern mismatch"
    }
  ],
  "recommended_actions": [
    "require_mfa",
    "alert_security",
    "log_detailed_audit",
    "force_re_authentication"
  ],
  "explanation": "Access pattern deviates significantly from user's historical behavior",
  "require_approval": true
}
```

##### 14.1.2 Get User Behavior Profile
```http
GET /ai/anomaly/profile/{user_id}
```
**Response:**
```json
{
  "user_id": "user-uuid",
  "behavior_profile": {
    "typical_access_hours": {
      "weekday": ["09:00", "18:00"],
      "weekend": []
    },
    "common_resources": ["vessels", "terminals", "reports"],
    "access_frequency": {
      "daily_average": 45,
      "peak_hour": "10:00",
      "weekly_average": 225
    },
    "location_patterns": ["Singapore", "Malaysia"],
    "device_fingerprints": ["device-001", "device-002"],
    "typing_cadence": 0.125,
    "mouse_movement_pattern": "smooth_acceleration",
    "avg_session_duration": 3600,
    "risk_baseline": 0.15
  },
  "last_updated": "2024-03-15T00:00:00Z"
}
```

##### 14.1.3 Report False Positive
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

#### 14.2 Permission Optimization APIs

##### 14.2.1 Analyze User Permissions
```http
POST /ai/optimizer/analyze-user
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "analysis_period_days": 90,
  "include_predictions": true,
  "include_service_accounts": false
}
```
**Response:**
```json
{
  "user_id": "user-uuid",
  "is_service_account": false,
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

##### 14.2.2 Optimize Tenant Roles
```http
POST /ai/optimizer/analyze-tenant
```
**Request:**
```json
{
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "optimization_goals": ["reduce_roles", "improve_security", "simplify_management"],
  "include_sub_tenants": true
}
```

#### 14.3 Natural Language Interface APIs

##### 14.3.1 Natural Language Query
```http
POST /ai/nlp/query
```
**Request:**
```json
{
  "query": "Who has access to vessel MSC-MOONLIGHT in Singapore port?",
  "context": {
    "user_id": "current-user-uuid",
    "include_details": true,
    "check_service_accounts": true
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
    },
    "confidence": 0.94
  },
  "answer": {
    "text": "5 users have access to vessel MSC-MOONLIGHT in Singapore port (3 regular users, 2 service accounts)",
    "data": [
      {
        "user": "Sarah Chen",
        "is_service_account": false,
        "role": "Shipping Agent",
        "access_level": "full",
        "valid_until": "2024-12-31"
      },
      {
        "user": "svc-port-sync",
        "is_service_account": true,
        "role": "API Reader",
        "access_level": "read",
        "valid_until": null
      }
    ]
  }
}
```

##### 14.3.2 Natural Language Command
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

##### 14.3.3 Execute NLP Command
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

#### 14.4 Predictive Access APIs

##### 14.4.1 Predict Access Needs
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

##### 14.4.2 Auto-Provision Predicted Access
```http
POST /ai/predictive/auto-provision
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "threshold": 0.80,
  "max_duration_hours": 48,
  "require_approval": false,
  "exclude_service_accounts": true
}
```

#### 14.5 Compliance Monitoring APIs

##### 14.5.1 Check Compliance Status
```http
GET /ai/compliance/status
```
**Query Parameters:**
- `tenant_id`: Specific tenant
- `regulation`: GDPR, SOX, ISPS, etc.
- `include_sub_tenants`: Include sub-tenant compliance

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
            "description": "Service accounts have excessive permissions",
            "affected_users": 3,
            "remediation": "Review service account permissions"
          }
        ]
      }
    }
  }
}
```

##### 14.5.2 Generate Compliance Report
```http
POST /ai/compliance/report
```

#### 14.6 AI Training & Management APIs

##### 14.6.1 Train AI Model
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
    },
    "exclude_service_accounts": false
  },
  "parameters": {
    "algorithm": "isolation_forest",
    "contamination": 0.01
  }
}
```

##### 14.6.2 Get AI Model Status
```http
GET /ai/models
```
**Response:**
```json
{
  "models": [
    {
      "model_id": "anomaly-detector-v2",
      "model_name": "UserBehaviorAnomaly",
      "type": "anomaly_detection",
      "version": "2.0.1",
      "algorithm": "isolation_forest",
      "status": "active",
      "accuracy": 0.94,
      "precision_score": 0.92,
      "recall_score": 0.89,
      "f1_score": 0.905,
      "training_samples": 1000000,
      "model_size_mb": 125,
      "last_trained_at": "2024-03-10T00:00:00Z",
      "deployed_at": "2024-03-10T12:00:00Z"
    }
  ]
}
```

##### 14.6.3 Configure AI Agent
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
    "learning_mode": "continuous",
    "include_biometrics": true
  }
}
```

#### 14.7 AI Explanation & Transparency APIs

##### 14.7.1 Explain AI Decision
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
        "factor": "biometric_deviation",
        "value": 0.75,
        "weight": 0.3,
        "description": "Keystroke pattern doesn't match baseline"
      }
    ],
    "model_confidence": 0.87,
    "model_id": "anomaly-detector-v2",
    "alternative_decision": {
      "action": "require_mfa",
      "probability": 0.13
    }
  },
  "override_available": true,
  "override_reason_required": true
}
```

##### 14.7.2 Override AI Decision
```http
POST /ai/override
```
**Request:**
```json
{
  "decision_id": "decision-uuid",
  "override_action": "allow_access",
  "reason": "User confirmed identity via video call",
  "override_by": "admin-uuid"
}
```

### 15. Behavioral Biometrics APIs (NEW)

#### 15.1 Capture Biometric Data
```http
POST /biometrics/capture
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "session_id": "session-uuid",
  "keystroke_events": [
    {
      "key": "a",
      "timestamp": 1000,
      "duration": 50
    },
    {
      "key": "b",
      "timestamp": 1100,
      "duration": 45
    }
  ],
  "mouse_events": [
    {
      "x": 100,
      "y": 200,
      "timestamp": 1000,
      "type": "move",
      "velocity": 2.5,
      "acceleration": 0.1
    }
  ],
  "navigation_sequence": ["login", "dashboard", "vessels", "vessel-detail"]
}
```

#### 15.2 Get Biometric Profile
```http
GET /biometrics/profile/{user_id}
```
**Response:**
```json
{
  "user_id": "user-uuid",
  "keystroke_dynamics": {
    "typing_cadence": 0.125,
    "avg_dwell_time": 48,
    "avg_flight_time": 77,
    "pattern_consistency": 0.89
  },
  "mouse_patterns": {
    "avg_velocity": 2.3,
    "acceleration_pattern": "smooth",
    "click_precision": 0.92,
    "movement_curvature": 0.15
  },
  "navigation_patterns": {
    "common_sequences": [
      ["login", "dashboard", "vessels"],
      ["login", "reports", "export"]
    ],
    "avg_page_duration": {
      "dashboard": 45,
      "vessels": 120,
      "reports": 300
    }
  },
  "baseline_samples": 50,
  "last_updated": "2024-03-15T10:00:00Z"
}
```

#### 15.3 Calculate Deviation Score
```http
POST /biometrics/deviation
```
**Request:**
```json
{
  "user_id": "user-uuid",
  "session_id": "session-uuid"
}
```
**Response:**
```json
{
  "deviation_score": 0.23,
  "components": {
    "keystroke_deviation": 0.15,
    "mouse_deviation": 0.28,
    "navigation_deviation": 0.26
  },
  "authentication_status": "authenticated", // authenticated, suspicious, unauthorized
  "confidence": 0.87,
  "recommendation": "continue_session"
}
```

#### 15.4 Continuous Authentication Status
```http
GET /biometrics/continuous-auth/{session_id}
```
**Response:**
```json
{
  "session_id": "session-uuid",
  "user_id": "user-uuid",
  "status": "authenticated",
  "continuous_score": 0.92,
  "last_check": "2024-03-15T10:30:00Z",
  "next_check": "2024-03-15T10:35:00Z",
  "checks_passed": 12,
  "checks_failed": 0
}
```

### 16. Feature Store APIs (NEW)

#### 16.1 Compute Features
```http
POST /ai/feature-store/compute
```
**Request:**
```json
{
  "feature_set": "user_access_patterns",
  "entity_type": "user",
  "entity_id": "user-uuid",
  "force_refresh": false
}
```

#### 16.2 Get Features
```http
GET /ai/feature-store/{feature_set}/{entity_id}
```
**Response:**
```json
{
  "feature_set": "user_access_patterns",
  "entity_type": "user",
  "entity_id": "user-uuid",
  "features": {
    "access_count_7d": 245,
    "unique_resources_30d": 18,
    "peak_hour": 10,
    "weekend_access_ratio": 0.05,
    "failed_attempts_7d": 2,
    "approval_request_rate": 0.02
  },
  "computed_at": "2024-03-15T09:00:00Z",
  "expires_at": "2024-03-15T10:00:00Z"
}
```

#### 16.3 Refresh Feature Store
```http
POST /ai/feature-store/refresh
```
**Request:**
```json
{
  "feature_sets": ["user_access_patterns", "resource_usage"],
  "batch_size": 100
}
```

### 17. AI Agent Communication APIs (NEW)

#### 17.1 Send Agent Message
```http
POST /ai/agents/message
```
**Request:**
```json
{
  "from_agent": "anomaly_detector",
  "to_agent": "permission_optimizer",
  "message_type": "alert",
  "priority": "high",
  "content": {
    "user_id": "user-uuid",
    "anomaly_type": "permission_abuse",
    "risk_score": 0.92,
    "recommendation": "review_permissions"
  }
}
```

#### 17.2 Get Agent Messages
```http
GET /ai/agents/messages
```
**Query Parameters:**
- `agent`: Filter by agent name
- `processed`: Filter processed/unprocessed
- `priority`: Filter by priority level

**Response:**
```json
{
  "messages": [
    {
      "id": "message-uuid",
      "from_agent": "anomaly_detector",
      "to_agent": "coordinator",
      "message_type": "alert",
      "priority": "critical",
      "content": {...},
      "correlation_id": "correlation-uuid",
      "processed": false,
      "created_at": "2024-03-15T10:00:00Z"
    }
  ]
}
```

## Standard Response Formats

### Success Response
```json
{
  "data": {}, // The actual response data
  "meta": {
    "request_id": "req-uuid",
    "timestamp": "2024-03-15T10:00:00Z",
    "cache_hit": true,
    "cache_backend": "memory"
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
      "user_permissions": ["vessel:read"],
      "approval_available": true,
      "approval_chain_id": "chain-uuid"
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
- `APPROVAL_REQUIRED`: 403 (with approval details)
- `RESOURCE_NOT_FOUND`: 404
- `VALIDATION_ERROR`: 400
- `CONFLICT`: 409
- `RATE_LIMIT_EXCEEDED`: 429
- `BIOMETRIC_AUTH_FAILED`: 401
- `SERVICE_ACCOUNT_INVALID`: 401
- `INTERNAL_ERROR`: 500

## Rate Limiting Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1458892800
X-RateLimit-Retry-After: 60
X-RateLimit-Tenant: 11111111-1111-1111-1111-111111111111
```

## Pagination Headers
```
X-Total-Count: 250
X-Page-Count: 5
X-Current-Page: 1
X-Per-Page: 50
```

## Cache Headers
```
X-Cache-Hit: true
X-Cache-Backend: memory
X-Cache-TTL: 300
```

## Version History
- v1.0: Initial API specifications
- v2.0: Complete alignment with database schema, unified service accounts, three-tier field model, approval chains, behavioral biometrics, ML feature store, AI agent communication