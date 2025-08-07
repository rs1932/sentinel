# LLM Prompt for Sentinel Backend Development - Dependency-Ordered Incremental Approach
## Version 2.0 - Aligned with Complete Database Schema

## Context
You are tasked with implementing the backend for Sentinel Access Platform, an enterprise-grade access control system for multi-tenant SaaS applications. This will be built as a modular monolith using FastAPI with Python 3.10, following an incremental, test-driven approach.

## Important Requirements
- **Python Version**: Use Python 3.10 (not 3.11 or 3.12 due to installation issues). Use a virtual environment to manage dependencies and also start the server using the virtual environment.
- **Redis**: Include Redis support in code but DISABLE it initially (use in-memory caching)
- **Development Approach**: Build one functional module at a time, fully test before moving to next
- **Database Schema**: All tables use the `sentinel` schema namespace in PostgreSQL. To be created in the sentinel_db database.

## Reference Documents
Please refer to the following uploaded documents in the docs directory for specifications:

1. **SaaS Platform Development Roadmap & Architecture v2** - Contains the complete directory structure, architecture overview, and implementation approach
2. **Product Requirements Document (PRD)** - Sections 3 (Personas), 4 (Core Features), and 5 (Technical Architecture) 
3. **Technical Design Document (TDD)** - Sections 2 (Component Design), 3 (Database Schema), and 4 (API Implementation Examples)
4. **Sentinel Platform - Complete PostgreSQL Database Schema with AI Tables** - Master SQL schema with all tables under `sentinel` schema
5. **Sentinel Access Platform - API Specifications** - Sections 1-14 for all API endpoints

## Development Approach: Dependency-Ordered Modules

We will build modules in dependency order to ensure each module can be fully functional and tested before moving to the next.

## Module Development Order (Revised By Dependencies)

### Dependency Tree:
```
Foundation (Database, Config, Base Models)
    └── Module 1: Tenants (API Section 10)
            └── Module 2: Authentication (API Section 1)
                    └── Module 3: Users & Service Accounts (API Section 2 & 11)
                            ├── Module 4: Roles (API Section 3)
                            └── Module 5: Groups (API Section 4)
                                    └── Module 6: Permissions (API Section 5)
                                            └── Module 7: Resources (API Section 6)
                                                    ├── Module 8: Field Definitions (API Section 7)
                                                    ├── Module 9: Navigation/Menu (API Section 8)
                                                    └── Module 10: Approval Chains (New)
                                                            └── Module 11: Permission Evaluation & Cache (API Section 5 & 12)
                                                                    ├── Module 12: Audit (API Section 9)
                                                                    ├── Module 13: Health & Monitoring (API Section 13)
                                                                    └── Module 14: AI Features & Biometrics (API Section 14)
```

## Phase 0: Foundation Setup

### Tasks:
1. Create directory structure from **SaaS Platform Development Roadmap & Architecture v2**
2. Set up Python 3.10 environment (critical: not 3.11 or 3.12)
3. Create base configuration with Redis DISABLED initially:
```python
# src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Core settings
    APP_NAME: str = "Sentinel Access Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DATABASE_SCHEMA: str = "sentinel"
    
    # Redis (disabled initially)
    REDIS_ENABLED: bool = False  # Set to False initially
    CACHE_BACKEND: str = "memory"  # Use in-memory cache initially
    
    # Approval chains
    APPROVAL_TIMEOUT_HOURS: int = 48
    AUTO_APPROVE_ENABLED: bool = False
    
    # Behavioral biometrics
    BIOMETRICS_ENABLED: bool = False
    KEYSTROKE_THRESHOLD: float = 0.7
    
    # ML Feature store
    FEATURE_STORE_TTL: int = 3600
    FEATURE_COMPUTE_BATCH_SIZE: int = 100
    
    # AI Agent communication
    AGENT_MESSAGE_TIMEOUT: int = 30
    AGENT_RETRY_COUNT: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```
4. Set up database connection (`src/database.py`) with sentinel schema
5. Create base model with timestamps:
```python
# src/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, MetaData
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Use sentinel schema for all tables
metadata = MetaData(schema="sentinel")
Base = declarative_base(metadata=metadata)

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```
6. Set up Alembic with sentinel schema support
7. Create error handling framework
8. Set up Docker environment with Python 3.10
9. Create base test configuration

## Module Implementation Order with Complete Schemas and Services

### Module 1: Tenant Management (Foundation)
**Why First**: Everything else depends on multi-tenancy

**Database Tables**: 
- `sentinel.tenants`

**Pydantic Schemas Required**:
```python
# Request Schemas
- TenantCreate
- TenantUpdate
- TenantQuery

# Response Schemas
- TenantResponse
- TenantListResponse
- TenantDetailResponse
```

**Core Services Required**:
```python
- TenantService
  - create_tenant()
  - get_tenant()
  - list_tenants()
  - update_tenant()
  - delete_tenant()
  - get_tenant_by_code()
  - create_sub_tenant()
  - get_tenant_hierarchy()
```

**API Endpoints**:
- POST /api/v1/tenants
- GET /api/v1/tenants
- GET /api/v1/tenants/{tenant_id}
- PATCH /api/v1/tenants/{tenant_id}
- DELETE /api/v1/tenants/{tenant_id}
- POST /api/v1/tenants/{parent_tenant_id}/sub-tenants

**Sample Data**:
```python
# Platform tenant (already in SQL with specific UUID)
{
    "id": "00000000-0000-0000-0000-000000000000",
    "name": "Sentinel Platform",
    "code": "PLATFORM",
    "type": "root"
}
# Test tenant (use different UUID to avoid conflicts)
{
    "id": "11111111-1111-1111-1111-111111111111",
    "name": "Test Company",
    "code": "TEST-001",
    "type": "root"
}
```

### Module 2: Authentication & Token Management
**Dependencies**: Module 1 (need tenant context)

**Database Tables**:
- `sentinel.users` (partial - just for auth)
- `sentinel.refresh_tokens`
- `sentinel.token_blacklist`

**Note**: Service accounts are part of users table with `is_service_account` flag

### Module 3: User Management (INCLUDING Service Accounts)
**Dependencies**: Modules 1-2 (need auth and tenants)

**Database Tables**:
- `sentinel.users` (complete with service account support)

**Pydantic Schemas Required**:
```python
# Request Schemas
- UserCreate
- UserUpdate
- UserQuery
- ServiceAccountCreate  # Uses same users table
- ServiceAccountUpdate
- PasswordReset
- PasswordChange
- UserBulkOperation
- CredentialRotation

# Response Schemas
- UserResponse
- UserDetailResponse
- UserListResponse
- UserPermissionsResponse
- ServiceAccountResponse
- ServiceAccountDetailResponse
- CredentialResponse
```

**Core Services Required**:
```python
- UserService
  - create_user()
  - get_user()
  - list_users()
  - update_user()
  - delete_user()
  - change_password()
  - reset_password()
  - lock_user()
  - unlock_user()
  - bulk_operation()
  - get_user_by_email()
  
- ServiceAccountService
  - create_service_account()  # Creates user with is_service_account=true
  - get_service_account()
  - list_service_accounts()
  - update_service_account()
  - delete_service_account()
  - rotate_credentials()
  - validate_api_key()
```

**API Endpoints**:
- POST /api/v1/users
- GET /api/v1/users
- GET /api/v1/users/{user_id}
- PATCH /api/v1/users/{user_id}
- DELETE /api/v1/users/{user_id}
- POST /api/v1/users/bulk
- GET /api/v1/users/{user_id}/permissions
- POST /api/v1/service-accounts
- GET /api/v1/service-accounts
- GET /api/v1/service-accounts/{account_id}
- PATCH /api/v1/service-accounts/{account_id}
- DELETE /api/v1/service-accounts/{account_id}
- POST /api/v1/service-accounts/{account_id}/rotate-credentials

### Module 4-9: Keep as originally specified
(Roles, Groups, Permissions, Resources, Field Definitions, Navigation)

### Module 10: Approval Chains (NEW)
**Dependencies**: Modules 1-9

**Database Tables**:
- `sentinel.access_requests`
- `sentinel.approval_chains`
- `sentinel.approvals`

**Pydantic Schemas Required**:
```python
# Request Schemas
- AccessRequestCreate
- ApprovalChainCreate
- ApprovalDecision
- ApprovalChainUpdate

# Response Schemas
- AccessRequestResponse
- ApprovalChainResponse
- ApprovalResponse
- PendingApprovalsResponse
```

**Core Services Required**:
```python
- ApprovalChainService
  - create_approval_chain()
  - get_approval_chain()
  - update_approval_chain()
  - evaluate_approval_needed()
  - get_next_approvers()
  
- AccessRequestService
  - create_access_request()
  - get_pending_approvals()
  - approve_request()
  - deny_request()
  - escalate_request()
  - check_auto_approval()
```

**API Endpoints**:
- POST /api/v1/access-requests
- GET /api/v1/access-requests
- GET /api/v1/access-requests/{request_id}
- POST /api/v1/access-requests/{request_id}/approve
- POST /api/v1/access-requests/{request_id}/deny
- POST /api/v1/approval-chains
- GET /api/v1/approval-chains
- PATCH /api/v1/approval-chains/{chain_id}

### Module 11: Permission Evaluation & Cache
**Dependencies**: Modules 1-10 (needs everything for evaluation)

**Database Tables**:
- `sentinel.permission_cache`

**Additional Considerations**:
- Integrate with approval chains for permission checks
- Use in-memory cache initially (Redis disabled)

### Module 12-13: Keep as originally specified
(Audit & Compliance, Health & Monitoring)

### Module 14: AI & Intelligence Features (EXPANDED)
**Dependencies**: All modules

**Database Tables**: 
- All AI tables from schema including:
  - `sentinel.ai_models`
  - `sentinel.user_behavior_profiles`
  - `sentinel.anomaly_detections`
  - `sentinel.permission_predictions`
  - `sentinel.permission_optimizations`
  - `sentinel.nlp_query_logs`
  - `sentinel.ai_training_jobs`
  - `sentinel.compliance_monitoring`
  - `sentinel.ai_decision_logs`
  - `sentinel.behavioral_biometrics`
  - `sentinel.ai_agent_messages`
  - `sentinel.ml_feature_store`

**Additional Services Required**:
```python
- BiometricsService
  - capture_keystroke_dynamics()
  - analyze_mouse_patterns()
  - calculate_deviation_score()
  - authenticate_biometrics()
  
- FeatureStoreService
  - compute_features()
  - store_features()
  - get_features()
  - refresh_features()
  
- AIAgentService
  - send_agent_message()
  - process_agent_messages()
  - coordinate_agents()
```

**API Endpoints**: 
- All from API Section 14 plus:
- POST /api/v1/ai/biometrics/capture
- GET /api/v1/ai/biometrics/profile/{user_id}
- POST /api/v1/ai/feature-store/compute
- GET /api/v1/ai/feature-store/{feature_set}
- POST /api/v1/ai/agents/message
- GET /api/v1/ai/agents/messages

## Module Development Process

For EACH module, follow these steps:

### Step 1: Database Migration
```bash
# Create migration for module
alembic revision -m "Add {module_name} tables"
# Edit migration file - ensure sentinel schema is used
# Run migration
alembic upgrade head
```

### Step 2: Create All Models
- Create SQLAlchemy models in `sentinel` schema
- Ensure proper relationships
- Test model creation

### Step 3: Create ALL Pydantic Schemas
- Request schemas with validation
- Response schemas
- Ensure datetime handling
- Test serialization
- Include three-tier field model where applicable

### Step 4: Implement ALL Core Services
- Business logic implementation
- Transaction management
- Error handling
- Tenant isolation
- Cache factory pattern (memory vs Redis)

### Step 5: Create ALL API Endpoints
- Implement all endpoints for the module
- Proper error responses
- Input validation
- Authentication/authorization
- Consistent with API specifications

### Step 6: Create Sample Data Script
```python
# scripts/seed_{module_name}.py
# Use consistent UUIDs that don't conflict with system data
```

### Step 7: Write Comprehensive Tests
```python
# tests/unit/test_{module_name}_service.py
# tests/integration/test_{module_name}_api.py
# tests/test_{module_name}_models.py
```

### Step 8: Integration Testing
- Test with previous modules
- Run regression tests
- Verify no breaking changes
- Test approval chains integration (Module 10+)

### Step 9: Documentation
- API documentation
- Usage examples
- Any deviations from spec
- Update version tracking

## Cache Service Factory Implementation

```python
# src/services/cache_service.py
from typing import Optional, Any
from datetime import datetime, timedelta
import json
from abc import ABC, abstractmethod

class CacheServiceInterface(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300):
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        pass
    
    @abstractmethod
    async def clear(self):
        pass

class InMemoryCacheService(CacheServiceInterface):
    """Temporary in-memory cache until Redis is enabled"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if key in self._expiry and datetime.now() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return None
            return self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = value
        self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    async def delete(self, key: str):
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    async def clear(self):
        self._cache.clear()
        self._expiry.clear()

class RedisCacheService(CacheServiceInterface):
    """Redis-based cache service"""
    # Implementation for when Redis is enabled
    pass

# Factory function
class CacheServiceFactory:
    @staticmethod
    def get_cache_service(settings=None):
        if settings is None:
            from src.config import settings
        
        if settings.REDIS_ENABLED:
            return RedisCacheService()
        else:
            return InMemoryCacheService()
```

## Testing Requirements

### For Each Module:
1. **Model Tests**: Test all database operations with sentinel schema
2. **Schema Tests**: Test validation and serialization
3. **Service Tests**: Test all business logic
4. **API Tests**: Test all endpoints
5. **Integration Tests**: Test with dependent modules
6. **Approval Chain Tests** (Module 10+): Test workflow integration
7. **Biometric Tests** (Module 14): Test behavioral capture

### Test Coverage Requirements:
- Minimum 80% coverage per module
- All error cases tested
- All validation rules tested
- Tenant isolation tested
- Approval workflows tested (where applicable)
- AI predictions tested with mock models

## Success Criteria Per Module

Before moving to next module:
- [ ] All database tables created in sentinel schema
- [ ] All models working with relationships
- [ ] All schemas validate correctly
- [ ] All services implement business logic
- [ ] All API endpoints return correct responses
- [ ] Sample data loads successfully (no UUID conflicts)
- [ ] All tests pass (unit + integration)
- [ ] No regression in previous modules
- [ ] Module documented
- [ ] Cache service working (memory or Redis)

## Important Notes

1. **Python 3.10**: Use `python:3.10-slim` in Docker (NOT 3.11 or 3.12)
2. **Redis Disabled**: Use in-memory cache initially via factory pattern
3. **Complete Module**: Each module must be 100% functional before proceeding
4. **Test Everything**: Every function, endpoint, and edge case
5. **Sample Data**: Consistent UUIDs across modules, avoid conflicts with system data
6. **Error Handling**: Clear, consistent error messages
7. **Tenant Isolation**: Enforce in every query
8. **Schema Namespace**: All tables use `sentinel` schema
9. **Service Accounts**: Part of users table with `is_service_account` flag
10. **Approval Chains**: Integrate with permission evaluation in Module 11

## Version Control

- v1.0: Initial instructions
- v2.0: Aligned with complete database schema, added approval chains, integrated service accounts

Begin with Module 1 (Tenants) after completing Phase 0 (Foundation). Do not proceed to Module 2 until Module 1 is fully implemented, tested, and documented.