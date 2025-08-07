# SaaS Platform Development Roadmap & Architecture v2
## Modular Monolith Approach with Sentinel Core

## Platform Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SaaS Applications Layer                   │
│  (MSW App, Fleet Management, Port Operations, Custom Apps)   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│              SaaS Platform Core - Modular Monolith           │
│                        (Single FastAPI App)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Sentinel Access Control System             │    │
│  │                                                      │    │
│  │ • Authentication      • Role Management             │    │
│  │ • Authorization       • Permission Engine           │    │
│  │ • Multi-tenancy       • Field-Level Security        │    │
│  │ • User Management     • Audit Trail                 │    │
│  │ • Groups              • AI/ML Features              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Core Platform Services                  │    │
│  │                                                      │    │
│  │ • Request Handling    • Middleware Stack           │    │
│  │ • Error Management    • Logging & Monitoring       │    │
│  │ • Cache Management    • Background Tasks           │    │
│  │ • Event Bus           • API Documentation          │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                    Infrastructure Layer                       │
│         PostgreSQL | Redis | S3 | Message Queue              │
└──────────────────────────────────────────────────────────────┘
```

## Development Approach - Modular Monolith

### Project Structure with URL Versioning

```python
sentinel-platform/
├── alembic/                      # Database migrations
│   ├── versions/
│   └── alembic.ini
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
│   │   │   ├── users.py          # User management
│   │   │   ├── roles.py          # Role management
│   │   │   ├── permissions.py    # Permission management
│   │   │   ├── groups.py         # Group management
│   │   │   ├── tenants.py        # Tenant management
│   │   │   ├── audit.py          # Audit endpoints
│   │   │   └── ai.py             # AI-powered endpoints
│   │   │
│   │   └── v2/                   # Version 2 APIs (future)
│   │       └── __init__.py
│   │
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── jwt_handler.py
│   │   │   ├── password.py
│   │   │   └── mfa.py
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── rbac.py          # Role-based access control
│   │   │   ├── abac.py          # Attribute-based access control
│   │   │   └── field_security.py
│   │   ├── tenant/
│   │   │   ├── __init__.py
│   │   │   ├── isolation.py
│   │   │   └── context.py
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── anomaly_detection.py
│   │       ├── permission_optimizer.py
│   │       └── nlp_engine.py
│   │
│   ├── models/                   # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py              # Base model class
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── permission.py
│   │   ├── group.py
│   │   ├── audit.py
│   │   └── ai_models.py
│   │
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── permission.py
│   │   ├── group.py
│   │   ├── tenant.py
│   │   └── responses.py         # Common response schemas
│   │
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── role_service.py
│   │   ├── permission_service.py
│   │   ├── group_service.py
│   │   ├── tenant_service.py
│   │   ├── audit_service.py
│   │   └── ai_service.py
│   │
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py              # Base repository
│   │   ├── user_repository.py
│   │   ├── role_repository.py
│   │   └── permission_repository.py
│   │
│   ├── middleware/               # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── authentication.py    # JWT validation
│   │   ├── tenant_context.py    # Tenant isolation
│   │   ├── rate_limiting.py
│   │   ├── correlation_id.py
│   │   ├── error_handler.py
│   │   └── audit_logger.py
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── cache.py             # Redis cache utilities
│   │   ├── pagination.py
│   │   ├── validators.py
│   │   └── exceptions.py        # Custom exceptions
│   │
│   └── background/              # Background tasks
│       ├── __init__.py
│       ├── tasks.py
│       └── workers.py
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/                     # Utility scripts
│   ├── seed_data.py
│   └── create_superuser.py
│
├── docker/                      # Docker configurations
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── requirements/               # Dependency management
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
│
├── .env.example
├── .gitignore
├── README.md
└── pyproject.toml             # Project configuration
```

### Main Application Structure (main.py)

```python
# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config import settings
from src.database import engine
from src.middleware import (
    AuthenticationMiddleware,
    TenantContextMiddleware,
    RateLimitingMiddleware,
    CorrelationIdMiddleware,
    AuditLoggerMiddleware
)

# Import API routers
from src.api.v1 import (
    auth_router,
    users_router,
    roles_router,
    permissions_router,
    groups_router,
    tenants_router,
    audit_router,
    ai_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_tasks()
    yield
    # Shutdown
    await shutdown_tasks()

# Create FastAPI app
app = FastAPI(
    title="Sentinel Access Platform",
    description="Enterprise-grade access control system for multi-tenant SaaS",
    version="1.0.0",
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
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(AuditLoggerMiddleware)

# Include API routers with versioning
API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{API_V1_PREFIX}/users", tags=["Users"])
app.include_router(roles_router, prefix=f"{API_V1_PREFIX}/roles", tags=["Roles"])
app.include_router(permissions_router, prefix=f"{API_V1_PREFIX}/permissions", tags=["Permissions"])
app.include_router(groups_router, prefix=f"{API_V1_PREFIX}/groups", tags=["Groups"])
app.include_router(tenants_router, prefix=f"{API_V1_PREFIX}/tenants", tags=["Tenants"])
app.include_router(audit_router, prefix=f"{API_V1_PREFIX}/audit", tags=["Audit"])
app.include_router(ai_router, prefix=f"{API_V1_PREFIX}/ai", tags=["AI"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Sentinel Access Platform",
        "version": "1.0.0",
        "status": "operational"
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

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login_v1(
    credentials: LoginRequest,
    auth_service: AuthService = Depends()
):
    """V1 Login endpoint"""
    return await auth_service.authenticate(credentials)

# Future V2 implementation
# src/api/v2/auth.py
@router.post("/login", response_model=TokenResponseV2)
async def login_v2(
    credentials: LoginRequestV2,
    auth_service: AuthService = Depends()
):
    """V2 Login with enhanced features"""
    # V2 might include device fingerprinting, location, etc.
    return await auth_service.authenticate_v2(credentials)
```

### Version Migration Strategy

```python
# Deprecation headers for old versions
from fastapi import Header

@router.post("/login")
async def login_v1(
    credentials: LoginRequest,
    auth_service: AuthService = Depends()
):
    # Add deprecation warning
    headers = {
        "X-API-Deprecation-Date": "2025-01-01",
        "X-API-Deprecation-Info": "Please migrate to v2",
        "Link": '</api/v2/auth/login>; rel="successor-version"'
    }
    
    result = await auth_service.authenticate(credentials)
    return JSONResponse(content=result, headers=headers)
```

## Development Phases

### Phase 1: Foundation (Weeks 1-4)
**Core Infrastructure Setup**

- [ ] Project structure setup
- [ ] Database schema creation (PostgreSQL)
- [ ] Redis cache configuration
- [ ] Base models and schemas
- [ ] Core middleware implementation
- [ ] Error handling framework
- [ ] Logging and monitoring setup
- [ ] Docker environment
- [ ] Basic CI/CD pipeline

### Phase 2: Authentication & Core Security (Weeks 5-8)
**Sentinel Core Features**

- [ ] JWT authentication implementation
- [ ] User registration and management
- [ ] Password management (hashing, reset)
- [ ] Session management
- [ ] Basic RBAC implementation
- [ ] Tenant creation and isolation
- [ ] API key management for service accounts
- [ ] Rate limiting per tenant

### Phase 3: Advanced Access Control (Weeks 9-12)
**Permission Engine & Groups**

- [ ] Permission evaluation engine
- [ ] Role inheritance system
- [ ] Group management
- [ ] ABAC implementation
- [ ] Field-level permissions
- [ ] Resource hierarchy
- [ ] Permission caching strategy
- [ ] Audit trail implementation

### Phase 4: AI Integration (Weeks 13-16)
**Intelligent Features**

- [ ] Anomaly detection service
- [ ] Permission optimization engine
- [ ] Natural language interface
- [ ] Predictive access management
- [ ] Behavioral analysis
- [ ] AI model training pipeline
- [ ] Decision explanation API

### Phase 5: Production Readiness (Weeks 17-20)
**Optimization & Deployment**

- [ ] Performance optimization
- [ ] Security hardening
- [ ] Comprehensive testing
- [ ] API documentation (OpenAPI)
- [ ] Admin dashboard
- [ ] Monitoring dashboards
- [ ] Production deployment scripts
- [ ] Disaster recovery procedures

## Modular Monolith Benefits

### 1. **Clear Module Boundaries**
```python
# Each module has its own service layer
class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        permission_service: PermissionService,  # Injected dependency
        audit_service: AuditService
    ):
        self.user_repo = user_repo
        self.permission_service = permission_service
        self.audit_service = audit_service
    
    async def create_user(self, user_data: UserCreate, current_user: User):
        # Check permission using injected service
        if not await self.permission_service.can_create_user(current_user):
            raise PermissionDeniedError()
        
        # Create user
        user = await self.user_repo.create(user_data)
        
        # Audit log
        await self.audit_service.log_user_created(user, current_user)
        
        return user
```

### 2. **Shared Transaction Management**
```python
# Single database transaction across modules
from src.database import get_db

async def create_user_with_role(user_data: dict, role_id: UUID):
    async with get_db() as db:
        async with db.begin():  # Single transaction
            # Create user
            user = await user_service.create_user(user_data, db)
            
            # Assign role
            await role_service.assign_role(user.id, role_id, db)
            
            # Set initial permissions
            await permission_service.set_defaults(user.id, db)
            
            # All succeed or all fail
```

### 3. **Easy Testing**
```python
# Easy to test modules in isolation
async def test_user_creation():
    # Mock dependencies
    mock_permission_service = Mock()
    mock_permission_service.can_create_user.return_value = True
    
    # Test user service
    user_service = UserService(
        user_repo=InMemoryUserRepository(),
        permission_service=mock_permission_service,
        audit_service=Mock()
    )
    
    user = await user_service.create_user(test_user_data, admin_user)
    assert user.email == test_user_data.email
```

## Configuration Management

```python
# src/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Sentinel Access Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    API_V2_PREFIX: str = "/api/v2"
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str
    CACHE_TTL: int = 300
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Tenant
    MAX_TENANTS: int = 1000
    MAX_USERS_PER_TENANT: int = 10000
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # AI Features
    ENABLE_AI_FEATURES: bool = True
    AI_MODEL_PATH: str = "./models"
    
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
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/sentinel_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
      - ./models:/app/models
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: sentinel_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
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

volumes:
  postgres_data:
  redis_data:
```

## Monitoring & Observability

### 1. **Structured Logging**
```python
# src/utils/logger.py
import structlog

logger = structlog.get_logger()

# Usage in services
async def authenticate_user(self, credentials: LoginRequest):
    logger.info(
        "authentication_attempt",
        email=credentials.email,
        tenant_id=self.tenant_id,
        ip_address=self.request.client.host
    )
    
    try:
        user = await self._verify_credentials(credentials)
        logger.info(
            "authentication_success",
            user_id=user.id,
            tenant_id=user.tenant_id
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
from prometheus_client import Counter, Histogram

# Define metrics
login_attempts = Counter(
    'sentinel_login_attempts_total',
    'Total login attempts',
    ['tenant_id', 'status']
)

api_request_duration = Histogram(
    'sentinel_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status']
)

permission_checks = Counter(
    'sentinel_permission_checks_total',
    'Total permission checks',
    ['resource_type', 'action', 'result']
)
```

## Success Criteria

### Technical Metrics
- API response time < 200ms (p95)
- 99.9% uptime
- < 0.1% error rate
- Successful authentication < 100ms
- Permission check < 50ms

### Business Metrics
- Support 1000+ tenants
- 10,000+ concurrent users
- 1M+ permission checks/hour
- < 5 minute onboarding time

### Security Metrics
- Zero security breaches
- 100% audit trail coverage
- < 1% false positive rate (AI anomaly detection)

This modular monolith approach provides a solid foundation that:
1. Maintains clear boundaries between modules
2. Allows for future microservices migration if needed
3. Simplifies deployment and operations
4. Enables shared transactions and data consistency
5. Reduces complexity while maintaining modularity

The URL versioning strategy ensures backward compatibility and smooth API evolution as your platform grows.