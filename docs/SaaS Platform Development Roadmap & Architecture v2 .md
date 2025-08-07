# SaaS Platform Development Roadmap & Architecture v3
## Modular Monolith Approach with Complete Sentinel Implementation

## Platform Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SaaS Applications Layer                   │
│  (MSW App, Fleet Management, Port Operations, Custom Apps)   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│         SaaS Platform Core - Modular Monolith (Python 3.10)  │
│                        (Single FastAPI App)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Sentinel Access Control System             │    │
│  │                                                      │    │
│  │ • Authentication      • Role Management             │    │
│  │ • Authorization       • Permission Engine           │    │
│  │ • Multi-tenancy       • Three-tier Field Security   │    │
│  │ • User Management     • Audit Trail                 │    │
│  │ • Service Accounts    • Approval Chains             │    │
│  │ • Groups              • Behavioral Biometrics       │    │
│  │ • AI/ML Features      • Feature Store               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Core Platform Services                  │    │
│  │                                                      │    │
│  │ • Request Handling    • Middleware Stack           │    │
│  │ • Error Management    • Logging & Monitoring       │    │
│  │ • Cache Factory       • Background Tasks           │    │
│  │ • Event Bus           • API Documentation          │    │
│  │ • Agent Communication • Compliance Engine          │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                    Infrastructure Layer                       │
│     PostgreSQL (sentinel schema) | Redis (optional) | S3     │
│     Message Queue | ML Models Storage | Feature Store        │
└──────────────────────────────────────────────────────────────┘
```

## Development Approach - Modular Monolith

### Critical Requirements
- **Python Version**: 3.10 (NOT 3.11 or 3.12)
- **Database Schema**: All tables in `sentinel` namespace
- **Cache Strategy**: Start with in-memory, Redis optional
- **Service Accounts**: Integrated in users table with `is_service_account` flag

### Complete Project Structure with URL Versioning

```python
sentinel-platform/
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   ├── alembic.ini              # Alembic configuration
│   └── env.py                   # Migration environment
├── src/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration management
│   ├── database.py               # Database connection & session
│   ├── dependencies.py           # Shared dependencies
│   │
│   ├── api/                      # API layer with versioning
│   │   ├── __init__.py
│   │   ├── v1/                   # Version 1 APIs
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── users.py          # User & service account management
│   │   │   ├── roles.py          # Role management
│   │   │   ├── permissions.py    # Permission management
│   │   │   ├── groups.py         # Group management
│   │   │   ├── tenants.py        # Tenant management
│   │   │   ├── resources.py      # Resource hierarchy
│   │   │   ├── fields.py         # Field definitions (3-tier)
│   │   │   ├── navigation.py     # Menu/navigation
│   │   │   ├── approvals.py      # Approval chains & requests
│   │   │   ├── audit.py          # Audit endpoints
│   │   │   ├── ai.py             # AI-powered endpoints
│   │   │   ├── biometrics.py     # Behavioral biometrics
│   │   │   └── cache.py          # Cache management
│   │   │
│   │   └── v2/                   # Version 2 APIs (future)
│   │       └── __init__.py
│   │
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── jwt_handler.py   # JWT token management
│   │   │   ├── password.py      # Password hashing
│   │   │   ├── mfa.py           # Multi-factor auth
│   │   │   └── api_keys.py      # Service account keys
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── rbac.py          # Role-based access control
│   │   │   ├── abac.py          # Attribute-based access control
│   │   │   ├── field_security.py # Three-tier field model
│   │   │   └── permission_evaluator.py
│   │   ├── tenant/
│   │   │   ├── __init__.py
│   │   │   ├── isolation.py     # Tenant isolation logic
│   │   │   ├── context.py       # Tenant context management
│   │   │   └── sub_tenants.py   # Sub-tenant handling
│   │   ├── approval/
│   │   │   ├── __init__.py
│   │   │   ├── chain_evaluator.py # Approval chain logic
│   │   │   ├── auto_approver.py   # Auto-approval conditions
│   │   │   └── escalation.py      # Timeout escalation
│   │   ├── biometrics/
│   │   │   ├── __init__.py
│   │   │   ├── keystroke_analyzer.py
│   │   │   ├── mouse_tracker.py
│   │   │   ├── pattern_matcher.py
│   │   │   └── deviation_scorer.py
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── anomaly_detection.py
│   │       ├── permission_optimizer.py
│   │       ├── nlp_engine.py
│   │       ├── predictive_access.py
│   │       ├── compliance_monitor.py
│   │       ├── feature_store.py
│   │       ├── model_registry.py
│   │       └── agent_coordinator.py
│   │
│   ├── models/                   # SQLAlchemy models (sentinel schema)
│   │   ├── __init__.py
│   │   ├── base.py              # Base model class with sentinel schema
│   │   ├── tenant.py            # Tenant & sub-tenant models
│   │   ├── user.py              # User & service account model
│   │   ├── role.py              # Role hierarchy
│   │   ├── permission.py        # Permission model
│   │   ├── group.py             # Group model
│   │   ├── resource.py          # Resource hierarchy
│   │   ├── field_definition.py  # Three-tier fields
│   │   ├── approval.py          # Approval chains & requests
│   │   ├── audit.py             # Audit log model
│   │   ├── ai_models.py         # AI model registry
│   │   ├── biometrics.py        # Behavioral biometrics
│   │   └── feature_store.py     # ML feature store
│   │
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py              # Auth request/response
│   │   ├── user.py              # User schemas (includes service accounts)
│   │   ├── role.py              # Role schemas
│   │   ├── permission.py        # Permission schemas (3-tier)
│   │   ├── group.py             # Group schemas
│   │   ├── tenant.py            # Tenant schemas
│   │   ├── resource.py          # Resource schemas
│   │   ├── field.py             # Field definition schemas
│   │   ├── approval.py          # Approval schemas
│   │   ├── ai.py                # AI-related schemas
│   │   ├── biometrics.py        # Biometric schemas
│   │   └── responses.py         # Common response schemas
│   │
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication logic
│   │   ├── user_service.py      # User management (includes service accounts)
│   │   ├── role_service.py      # Role management
│   │   ├── permission_service.py # Permission evaluation
│   │   ├── group_service.py     # Group management
│   │   ├── tenant_service.py    # Tenant operations
│   │   ├── resource_service.py  # Resource management
│   │   ├── field_service.py     # Field definition service
│   │   ├── approval_service.py  # Approval chain service
│   │   ├── audit_service.py     # Audit logging
│   │   ├── cache_service.py     # Cache factory & implementations
│   │   ├── ai_service.py        # AI orchestration
│   │   ├── biometrics_service.py # Biometric analysis
│   │   ├── feature_store_service.py # ML feature management
│   │   └── compliance_service.py # Compliance monitoring
│   │
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py              # Base repository with tenant isolation
│   │   ├── user_repository.py   # User & service account queries
│   │   ├── role_repository.py   # Role queries
│   │   ├── permission_repository.py
│   │   ├── approval_repository.py
│   │   ├── ai_repository.py     # AI model & prediction storage
│   │   ├── biometrics_repository.py
│   │   └── feature_repository.py
│   │
│   ├── middleware/               # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── authentication.py    # JWT validation & biometric check
│   │   ├── tenant_context.py    # Tenant isolation enforcement
│   │   ├── rate_limiting.py     # Rate limiting per tenant
│   │   ├── correlation_id.py    # Request tracking
│   │   ├── error_handler.py     # Global error handling
│   │   ├── audit_logger.py      # Audit trail logging
│   │   └── metrics.py           # Prometheus metrics
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── cache_factory.py     # Cache service factory
│   │   ├── pagination.py        # Pagination helpers
│   │   ├── validators.py        # Custom validators
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── crypto.py            # Encryption utilities
│   │   └── datetime_utils.py    # Date/time helpers
│   │
│   └── background/              # Background tasks
│       ├── __init__.py
│       ├── tasks.py             # Celery tasks
│       ├── workers.py           # Worker processes
│       ├── approval_escalator.py # Approval timeout handler
│       ├── feature_computer.py  # ML feature computation
│       ├── model_trainer.py     # AI model training
│       └── compliance_checker.py # Compliance validation
│
├── tests/                       # Comprehensive test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/
│   │   ├── test_services/      # Service layer tests
│   │   ├── test_models/        # Model tests
│   │   ├── test_schemas/       # Schema validation tests
│   │   └── test_utils/         # Utility tests
│   ├── integration/
│   │   ├── test_auth_flow.py   # Auth integration tests
│   │   ├── test_permissions.py # Permission flow tests
│   │   ├── test_approvals.py   # Approval chain tests
│   │   └── test_biometrics.py  # Biometric tests
│   └── e2e/
│       ├── test_user_journey.py
│       └── test_api_endpoints.py
│
├── scripts/                     # Utility scripts
│   ├── seed_data.py            # Seed test data
│   ├── create_superuser.py     # Create admin user
│   ├── migrate_db.py           # Database migration helper
│   └── generate_api_key.py     # Service account key generator
│
├── docker/                      # Docker configurations
│   ├── Dockerfile              # Python 3.10 base image
│   ├── docker-compose.yml      # Full stack composition
│   └── docker-compose.dev.yml  # Development overrides
│
├── docs/                        # Documentation
│   ├── api/                    # API documentation
│   ├── architecture/           # Architecture diagrams
│   └── deployment/             # Deployment guides
│
├── ml_models/                   # Trained ML models
│   ├── anomaly_detection/
│   ├── permission_prediction/
│   └── biometric_baseline/
│
├── requirements/               # Dependency management
│   ├── base.txt               # Core dependencies
│   ├── dev.txt                # Development dependencies
│   ├── prod.txt               # Production dependencies
│   └── ml.txt                 # ML/AI dependencies
│
├── .env.example               # Environment variables template
├── .gitignore
├── .dockerignore
├── README.md                  # Project documentation
├── pyproject.toml            # Project configuration
└── setup.cfg                 # Setup configuration
```

### Main Application Structure (main.py)

```python
# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys

# Verify Python version
assert sys.version_info[:2] == (3, 10), "Python 3.10 is required"

from src.config import settings
from src.database import engine
from src.services.cache_service import CacheServiceFactory
from src.middleware import (
    AuthenticationMiddleware,
    TenantContextMiddleware,
    RateLimitingMiddleware,
    CorrelationIdMiddleware,
    AuditLoggerMiddleware,
    MetricsMiddleware
)

# Import API routers
from src.api.v1 import (
    auth_router,
    users_router,
    roles_router,
    permissions_router,
    groups_router,
    tenants_router,
    resources_router,
    fields_router,
    navigation_router,
    approvals_router,
    audit_router,
    ai_router,
    biometrics_router,
    cache_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting Sentinel Platform with Python {sys.version}")
    await initialize_database()
    
    # Initialize cache with factory pattern
    cache = CacheServiceFactory.get_cache_service(settings)
    await cache.clear()  # Clear cache on startup
    
    # Load AI models if enabled
    if settings.AI_ENABLED:
        await load_ai_models()
    
    yield
    
    # Shutdown
    await shutdown_tasks()
    CacheServiceFactory.reset()

# Create FastAPI app
app = FastAPI(
    title="Sentinel Access Platform",
    description="Enterprise-grade access control system for multi-tenant SaaS",
    version="3.0.0",
    lifespan=lifespan
)

# Add middleware (order matters!)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(AuditLoggerMiddleware)

# Include API routers with versioning
API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{API_V1_PREFIX}/users", tags=["Users & Service Accounts"])
app.include_router(roles_router, prefix=f"{API_V1_PREFIX}/roles", tags=["Roles"])
app.include_router(permissions_router, prefix=f"{API_V1_PREFIX}/permissions", tags=["Permissions"])
app.include_router(groups_router, prefix=f"{API_V1_PREFIX}/groups", tags=["Groups"])
app.include_router(tenants_router, prefix=f"{API_V1_PREFIX}/tenants", tags=["Tenants"])
app.include_router(resources_router, prefix=f"{API_V1_PREFIX}/resources", tags=["Resources"])
app.include_router(fields_router, prefix=f"{API_V1_PREFIX}/field-definitions", tags=["Field Definitions"])
app.include_router(navigation_router, prefix=f"{API_V1_PREFIX}/navigation", tags=["Navigation"])
app.include_router(approvals_router, prefix=f"{API_V1_PREFIX}/approvals", tags=["Approval Chains"])
app.include_router(audit_router, prefix=f"{API_V1_PREFIX}/audit", tags=["Audit"])
app.include_router(ai_router, prefix=f"{API_V1_PREFIX}/ai", tags=["AI Features"])
app.include_router(biometrics_router, prefix=f"{API_V1_PREFIX}/biometrics", tags=["Behavioral Biometrics"])
app.include_router(cache_router, prefix=f"{API_V1_PREFIX}/cache", tags=["Cache Management"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Sentinel Access Platform",
        "version": "3.0.0",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "status": "operational",
        "cache_backend": settings.CACHE_BACKEND,
        "ai_enabled": settings.AI_ENABLED,
        "biometrics_enabled": settings.BIOMETRICS_ENABLED
    }

# Health check
@app.get("/health")
async def health_check():
    return await check_system_health()
```

## API Versioning Strategy

### URL Versioning Implementation

```python
# src/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from src.schemas.auth import LoginRequest, TokenResponse
from src.services.auth_service import AuthService
from src.services.biometrics_service import BiometricsService

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login_v1(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(),
    biometrics_service: BiometricsService = Depends()
):
    """
    V1 Login endpoint with optional biometric validation
    
    Service accounts use API keys through service-account/token endpoint
    """
    # Check if user is a service account
    user = await auth_service.get_user_by_email(credentials.email)
    if user and user.is_service_account:
        raise HTTPException(400, "Service accounts must use /auth/service-account/token endpoint")
    
    result = await auth_service.authenticate(credentials)
    
    # Initialize biometric baseline for new users
    if settings.BIOMETRICS_ENABLED and result.first_login:
        await biometrics_service.initialize_baseline(result.user_id)
    
    return result

@router.post("/service-account/token", response_model=TokenResponse)
async def service_account_login(
    api_key: str,
    auth_service: AuthService = Depends()
):
    """Authenticate service account using API key"""
    return await auth_service.authenticate_service_account(api_key)
```

## Development Phases

### Phase 1: Foundation (Weeks 1-4)
**Core Infrastructure Setup**

- [x] Python 3.10 environment setup
- [ ] Project structure creation
- [ ] Database schema with `sentinel` namespace
- [ ] Base models with sentinel schema
- [ ] Cache factory implementation (memory first)
- [ ] Core middleware stack
- [ ] Error handling framework
- [ ] Docker environment (Python 3.10)
- [ ] Basic CI/CD pipeline

### Phase 2: Authentication & Core Security (Weeks 5-8)
**Sentinel Core Features**

- [ ] JWT authentication implementation
- [ ] User registration (regular users)
- [ ] Service account management (same table)
- [ ] Password management
- [ ] Session management
- [ ] Token blacklisting
- [ ] API key generation for service accounts
- [ ] Basic RBAC implementation
- [ ] Tenant creation and isolation

### Phase 3: Advanced Access Control (Weeks 9-12)
**Permission Engine & Groups**

- [ ] Permission evaluation engine
- [ ] Three-tier field model implementation
- [ ] Role inheritance system
- [ ] Group management
- [ ] ABAC implementation
- [ ] Resource hierarchy
- [ ] Permission caching (factory pattern)
- [ ] Audit trail implementation

### Phase 4: Approval Workflows (Weeks 13-14)
**Approval Chain Implementation**

- [ ] Approval chain configuration
- [ ] Access request management
- [ ] Multi-level approval processing
- [ ] Automatic escalation
- [ ] Auto-approval conditions
- [ ] Approval notifications
- [ ] Delegation support

### Phase 5: AI Integration (Weeks 15-18)
**Intelligent Features**

- [ ] Anomaly detection service
- [ ] Permission optimization engine
- [ ] Natural language interface
- [ ] Predictive access management
- [ ] ML feature store
- [ ] Model registry
- [ ] AI agent communication
- [ ] Decision explanation API

### Phase 6: Behavioral Biometrics (Weeks 19-20)
**Continuous Authentication**

- [ ] Keystroke dynamics capture
- [ ] Mouse pattern analysis
- [ ] Deviation scoring
- [ ] Baseline profile management
- [ ] Continuous authentication
- [ ] Risk-based authentication

### Phase 7: Production Readiness (Weeks 21-24)
**Optimization & Deployment**

- [ ] Performance optimization
- [ ] Security hardening
- [ ] Comprehensive testing (80% coverage)
- [ ] API documentation (OpenAPI)
- [ ] Admin dashboard
- [ ] Monitoring dashboards
- [ ] Production deployment
- [ ] Disaster recovery
- [ ] Compliance validation

## Modular Monolith Benefits

### 1. **Clear Module Boundaries with Dependency Injection**
```python
# Each module has clear interfaces
class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        permission_service: PermissionService,
        approval_service: ApprovalService,
        audit_service: AuditService,
        cache_factory: CacheServiceFactory
    ):
        self.user_repo = user_repo
        self.permission_service = permission_service
        self.approval_service = approval_service
        self.audit_service = audit_service
        self.cache = cache_factory.get_cache_service()
    
    async def create_user(self, user_data: UserCreate, current_user: User):
        # Check permission
        if not await self.permission_service.can_create_user(current_user):
            # Check if approval is available
            if await self.approval_service.can_request_approval("user:create"):
                raise ApprovalRequiredError()
            raise PermissionDeniedError()
        
        # Create user (handles both regular and service accounts)
        if user_data.is_service_account:
            user = await self._create_service_account(user_data)
        else:
            user = await self._create_regular_user(user_data)
        
        # Invalidate cache
        await self.cache.delete(f"users:{current_user.tenant_id}")
        
        # Audit log
        await self.audit_service.log_user_created(user, current_user)
        
        return user
```

### 2. **Shared Transaction Management**
```python
# Single database transaction across modules
from src.database import get_db

async def create_user_with_role_and_approval(user_data: dict, role_id: UUID):
    async with get_db() as db:
        async with db.begin():  # Single transaction
            # Create user (regular or service account)
            user = await user_service.create_user(user_data, db)
            
            # Assign role
            await role_service.assign_role(user.id, role_id, db)
            
            # Set initial permissions
            await permission_service.set_defaults(user.id, db)
            
            # Create approval chain if needed
            if user_data.get("requires_approval"):
                await approval_service.create_chain_for_user(user.id, db)
            
            # Initialize biometric profile
            if not user.is_service_account:
                await biometrics_service.create_baseline(user.id, db)
            
            # All succeed or all fail
```

### 3. **Easy Testing with Factory Pattern**
```python
# Easy to test with cache factory
async def test_user_creation_with_cache():
    # Force in-memory cache for testing
    CacheServiceFactory.reset()
    mock_settings = Mock(REDIS_ENABLED=False)
    
    # Mock dependencies
    mock_permission_service = Mock()
    mock_permission_service.can_create_user.return_value = True
    
    # Test user service
    user_service = UserService(
        user_repo=InMemoryUserRepository(),
        permission_service=mock_permission_service,
        approval_service=Mock(),
        audit_service=Mock(),
        cache_factory=CacheServiceFactory
    )
    
    # Test regular user
    user = await user_service.create_user(test_user_data, admin_user)
    assert user.email == test_user_data.email
    assert not user.is_service_account
    
    # Test service account
    service_account_data = {**test_user_data, "is_service_account": True}
    service_account = await user_service.create_user(service_account_data, admin_user)
    assert service_account.is_service_account
    assert service_account.service_account_key is not None
```

## Configuration Management (Complete)

```python
# src/config.py
from pydantic_settings import BaseSettings
from typing import List
import sys

# Verify Python version at import
assert sys.version_info[:2] == (3, 10), "Python 3.10 is required"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Sentinel Access Platform"
    VERSION: str = "3.0.0"
    DEBUG: bool = False
    PYTHON_VERSION: str = "3.10"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    API_V2_PREFIX: str = "/api/v2"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Database (PostgreSQL with sentinel schema)
    DATABASE_URL: str
    DATABASE_SCHEMA: str = "sentinel"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_ECHO: bool = False
    
    # Redis (Initially disabled)
    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_BACKEND: str = "memory"  # "memory" or "redis"
    CACHE_TTL: int = 300
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    
    # Service Accounts
    SERVICE_ACCOUNT_KEY_LENGTH: int = 64
    SERVICE_ACCOUNT_ROTATION_DAYS: int = 90
    MAX_SERVICE_ACCOUNTS_PER_TENANT: int = 100
    
    # Tenant
    MAX_TENANTS: int = 1000
    MAX_USERS_PER_TENANT: int = 10000
    ENABLE_SUB_TENANTS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Approval Chains
    APPROVAL_TIMEOUT_HOURS: int = 48
    AUTO_APPROVE_ENABLED: bool = False
    APPROVAL_ESCALATION_ENABLED: bool = True
    MAX_APPROVAL_LEVELS: int = 5
    
    # Behavioral Biometrics
    BIOMETRICS_ENABLED: bool = False
    KEYSTROKE_THRESHOLD: float = 0.7
    MOUSE_PATTERN_THRESHOLD: float = 0.6
    CONTINUOUS_AUTH_INTERVAL: int = 300
    BIOMETRIC_BASELINE_SAMPLES: int = 10
    
    # AI Features
    AI_ENABLED: bool = True
    AI_MODEL_PATH: str = "./ml_models"
    ANOMALY_DETECTION_THRESHOLD: float = 0.7
    PREDICTION_CONFIDENCE_THRESHOLD: float = 0.8
    
    # ML Feature Store
    FEATURE_STORE_TTL: int = 3600
    FEATURE_COMPUTE_BATCH_SIZE: int = 100
    FEATURE_REFRESH_INTERVAL: int = 900
    
    # AI Agent Communication
    AGENT_MESSAGE_TIMEOUT: int = 30
    AGENT_RETRY_COUNT: int = 3
    AGENT_PRIORITY_LEVELS: List[str] = ["low", "normal", "high", "critical"]
    
    # Background Tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"
    
    # Compliance
    COMPLIANCE_CHECKS_ENABLED: bool = True
    COMPLIANCE_REGULATIONS: List[str] = ["GDPR", "SOX", "HIPAA", "ISPS"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Deployment Architecture

```yaml
# docker-compose.yml
version: '3.8'

services:
  sentinel-platform:
    build:
      context: .
      dockerfile: docker/Dockerfile
      args:
        PYTHON_VERSION: "3.10"
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/sentinel_db
      - DATABASE_SCHEMA=sentinel
      - REDIS_ENABLED=false
      - CACHE_BACKEND=memory
      - AI_ENABLED=true
      - BIOMETRICS_ENABLED=false
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
      - ./ml_models:/app/ml_models
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: sentinel_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - sentinel-platform

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

## Monitoring & Observability

### 1. **Structured Logging**
```python
# src/utils/logger.py
import structlog
import sys

# Verify Python version
assert sys.version_info[:2] == (3, 10), "Python 3.10 required"

logger = structlog.get_logger()

# Usage in services
async def authenticate_user(self, credentials: LoginRequest):
    logger.info(
        "authentication_attempt",
        email=credentials.email,
        tenant_id=self.tenant_id,
        ip_address=self.request.client.host,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    
    try:
        user = await self._verify_credentials(credentials)
        
        # Check if service account
        if user.is_service_account:
            logger.warning(
                "service_account_password_attempt",
                user_id=user.id,
                message="Service account attempted password login"
            )
            raise AuthenticationError("Service accounts must use API keys")
        
        logger.info(
            "authentication_success",
            user_id=user.id,
            tenant_id=user.tenant_id,
            is_service_account=user.is_service_account
        )
        return user
    except Exception as e:
        logger.error(
            "authentication_failed",
            email=credentials.email,
            error=str(e)
        )
        raise
```

### 2. **Metrics Collection**
```python
# src/utils/metrics.py
from prometheus_client import Counter, Histogram, Info

# System info
system_info = Info('sentinel_system', 'System information')
system_info.info({
    'version': '3.0.0',
    'python_version': '3.10',
    'cache_backend': settings.CACHE_BACKEND
})

# Define metrics
login_attempts = Counter(
    'sentinel_login_attempts_total',
    'Total login attempts',
    ['tenant_id', 'status', 'account_type']
)

api_request_duration = Histogram(
    'sentinel_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status']
)

permission_checks = Counter(
    'sentinel_permission_checks_total',
    'Total permission checks',
    ['resource_type', 'action', 'result', 'requires_approval']
)

cache_operations = Counter(
    'sentinel_cache_operations_total',
    'Cache operations by type',
    ['operation', 'cache_type', 'result']
)

approval_chain_metrics = Counter(
    'sentinel_approval_chains_total',
    'Approval chain metrics',
    ['action', 'status', 'auto_approved']
)

biometric_authentications = Histogram(
    'sentinel_biometric_deviation_score',
    'Biometric deviation scores',
    ['user_type', 'auth_result']
)
```

## Success Criteria

### Technical Metrics
- Python 3.10 environment ✓
- API response time < 200ms (p95)
- 99.9% uptime
- < 0.1% error rate
- Successful authentication < 100ms
- Permission check < 50ms (cached)
- Cache hit ratio > 90%

### Business Metrics
- Support 1000+ tenants
- 10,000+ concurrent users
- 1M+ permission checks/hour
- < 5 minute onboarding time
- < 2 hour approval cycle time

### Security Metrics
- Zero security breaches
- 100% audit trail coverage
- < 1% false positive rate (AI anomaly detection)
- < 5% biometric false rejection rate

## Version History
- v1.0: Initial architecture
- v2.0: Added modular structure
- v3.0: Complete alignment with database schema, Python 3.10, unified service accounts, approval chains, biometrics, cache factory pattern

This modular monolith approach provides:
1. Clear boundaries between modules with dependency injection
2. Unified service account management in users table
3. Cache flexibility with factory pattern (memory → Redis)
4. Complete feature set including approval chains and biometrics
5. Python 3.10 compatibility throughout
6. All database operations in `sentinel` schema
7. Future microservices migration path if needed