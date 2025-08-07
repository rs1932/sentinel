# Technical Design Document (TDD)
## Sentinel Access Platform

## 1. System Overview

The Sentinel Access Platform is designed as a modular monolith architecture with clear separation of concerns between authentication, authorization, resource management, and AI-powered features. The system uses PostgreSQL with a dedicated `sentinel` schema for all database objects.

## 2. Component Design

### 2.1 Auth Service
**Responsibilities:**
- JWT token generation and validation
- User authentication
- Service account management
- Token refresh logic
- Token blacklisting

**Key Classes:**
```python
class AuthService:
    def __init__(self, user_repo: UserRepository, token_manager: TokenManager):
        self.user_repo = user_repo
        self.token_manager = token_manager
    
    async def authenticate_user(self, email: str, password: str, tenant_id: UUID) -> TokenPair:
        user = await self.user_repo.get_by_email(email, tenant_id)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")
        
        access_token = self.token_manager.create_access_token(user)
        refresh_token = self.token_manager.create_refresh_token(user)
        
        return TokenPair(access_token, refresh_token)
    
    async def authenticate_service_account(self, client_id: str, client_secret: str) -> Token:
        account = await self.user_repo.get_service_account(client_id)
        if not account or not verify_secret(client_secret, account.secret_hash):
            raise AuthenticationError("Invalid service account credentials")
        
        return self.token_manager.create_service_token(account)

class TokenManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(self, user: User) -> str:
        payload = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "roles": [str(role.id) for role in user.roles],
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError:
            raise InvalidTokenError()
```

### 2.2 Permission Service
**Responsibilities:**
- Permission evaluation
- Policy engine implementation
- Field-level access control
- Dynamic attribute evaluation
- Permission caching

**Key Classes:**
```python
class PermissionEvaluator:
    def __init__(self, role_service: RoleService, cache: RedisCache):
        self.role_service = role_service
        self.cache = cache
    
    async def check_permission(
        self,
        user_id: UUID,
        resource: Resource,
        action: str,
        context: dict = None
    ) -> PermissionResult:
        # Check cache first
        cache_key = f"perm:{user_id}:{resource.type}:{resource.id}:{action}"
        cached = await self.cache.get(cache_key)
        if cached:
            return PermissionResult.from_dict(cached)
        
        # Get user's effective permissions
        permissions = await self._get_user_permissions(user_id)
        
        # Evaluate permission
        result = await self._evaluate_permission(
            permissions, resource, action, context
        )
        
        # Cache result
        await self.cache.set(cache_key, result.to_dict(), ttl=300)
        
        return result
    
    async def get_field_permissions(
        self,
        user_id: UUID,
        resource: Resource
    ) -> Dict[str, List[str]]:
        permissions = await self._get_user_permissions(user_id)
        field_perms = {}
        
        for perm in permissions:
            if self._matches_resource(perm, resource):
                for field, actions in perm.field_permissions.items():
                    if field not in field_perms:
                        field_perms[field] = []
                    field_perms[field].extend(actions)
        
        return field_perms
    
    async def _evaluate_permission(
        self,
        permissions: List[Permission],
        resource: Resource,
        action: str,
        context: dict
    ) -> PermissionResult:
        for perm in permissions:
            if self._matches_resource(perm, resource) and action in perm.actions:
                if perm.conditions:
                    if not self._evaluate_conditions(perm.conditions, context):
                        continue
                
                return PermissionResult(
                    allowed=True,
                    permission_id=perm.id,
                    matched_conditions=perm.conditions
                )
        
        return PermissionResult(allowed=False, reason="No matching permission")

class PolicyEngine:
    def __init__(self):
        self.policies = []
    
    def add_policy(self, policy: Policy):
        self.policies.append(policy)
    
    async def evaluate(self, subject: dict, resource: dict, action: str) -> bool:
        for policy in self.policies:
            if await policy.evaluate(subject, resource, action):
                return True
        return False
```

### 2.3 Role Service
**Responsibilities:**
- Role CRUD operations
- Permission assignment
- Role inheritance management
- Role template management

**Key Classes:**
```python
class RoleService:
    def __init__(self, role_repo: RoleRepository, cache: RedisCache):
        self.role_repo = role_repo
        self.cache = cache
    
    async def create_role(self, tenant_id: UUID, role_data: RoleCreate) -> Role:
        # Check for duplicate role name
        existing = await self.role_repo.get_by_name(tenant_id, role_data.name)
        if existing:
            raise DuplicateRoleError(f"Role {role_data.name} already exists")
        
        # Create role
        role = await self.role_repo.create(tenant_id, role_data)
        
        # Invalidate cache
        await self._invalidate_role_cache(tenant_id)
        
        return role
    
    async def assign_permissions(self, role_id: UUID, permissions: List[Permission]) -> None:
        role = await self.role_repo.get(role_id)
        if not role:
            raise RoleNotFoundError()
        
        await self.role_repo.assign_permissions(role_id, permissions)
        await self._invalidate_role_cache(role.tenant_id)
    
    async def get_effective_permissions(self, role_id: UUID) -> List[Permission]:
        # Get direct permissions
        direct_perms = await self.role_repo.get_permissions(role_id)
        
        # Get inherited permissions
        role = await self.role_repo.get(role_id)
        if role.parent_role_id:
            parent_perms = await self.get_effective_permissions(role.parent_role_id)
            direct_perms.extend(parent_perms)
        
        # Remove duplicates
        return list({perm.id: perm for perm in direct_perms}.values())

class RoleInheritanceResolver:
    async def resolve_inheritance_chain(self, role_id: UUID) -> List[Role]:
        chain = []
        current_id = role_id
        seen = set()
        
        while current_id:
            if current_id in seen:
                raise CircularInheritanceError()
            
            role = await self.role_repo.get(current_id)
            if not role:
                break
                
            chain.append(role)
            seen.add(current_id)
            current_id = role.parent_role_id
        
        return chain
```

### 2.4 Group Service
**Responsibilities:**
- Group management
- User-group associations
- Group-role assignments
- Nested group support

**Key Classes:**
```python
class GroupService:
    def __init__(self, group_repo: GroupRepository, cache: RedisCache):
        self.group_repo = group_repo
        self.cache = cache
    
    async def create_group(self, tenant_id: UUID, group_data: GroupCreate) -> Group:
        # Validate parent group if specified
        if group_data.parent_group_id:
            parent = await self.group_repo.get(group_data.parent_group_id)
            if not parent or parent.tenant_id != tenant_id:
                raise InvalidParentGroupError()
        
        return await self.group_repo.create(tenant_id, group_data)
    
    async def add_users_to_group(self, group_id: UUID, user_ids: List[UUID]) -> None:
        group = await self.group_repo.get(group_id)
        if not group:
            raise GroupNotFoundError()
        
        # Validate all users belong to same tenant
        for user_id in user_ids:
            user = await self.user_repo.get(user_id)
            if not user or user.tenant_id != group.tenant_id:
                raise InvalidUserError(f"User {user_id} not valid for group")
        
        await self.group_repo.add_users(group_id, user_ids)
        
        # Invalidate permission cache for affected users
        for user_id in user_ids:
            await self._invalidate_user_permissions(user_id)
    
    async def assign_roles_to_group(self, group_id: UUID, role_ids: List[UUID]) -> None:
        await self.group_repo.assign_roles(group_id, role_ids)
        
        # Invalidate cache for all group members
        members = await self.group_repo.get_members(group_id)
        for member in members:
            await self._invalidate_user_permissions(member.id)
```

### 2.5 AI Service Components
**Responsibilities:**
- Anomaly detection
- Permission optimization
- Natural language processing
- Predictive access
- Compliance monitoring

**Key Classes:**
```python
class AnomalyDetectionService:
    def __init__(self, ml_model: IsolationForest, user_behavior_repo: UserBehaviorRepository):
        self.ml_model = ml_model
        self.user_behavior_repo = user_behavior_repo
    
    async def check_anomaly(
        self,
        user_id: UUID,
        access_request: AccessRequest
    ) -> AnomalyResult:
        # Get user's behavior profile
        profile = await self.user_behavior_repo.get_profile(user_id)
        
        # Extract features
        features = self._extract_features(access_request, profile)
        
        # Predict anomaly
        anomaly_score = self.ml_model.predict_proba([features])[0]
        
        if anomaly_score > 0.7:
            anomaly_types = self._identify_anomaly_types(features, profile)
            
            return AnomalyResult(
                detected=True,
                risk_score=anomaly_score,
                anomaly_types=anomaly_types,
                recommended_actions=self._get_recommended_actions(anomaly_score)
            )
        
        return AnomalyResult(detected=False, risk_score=anomaly_score)

class PermissionOptimizerService:
    def __init__(self, permission_analyzer: PermissionAnalyzer):
        self.analyzer = permission_analyzer
    
    async def analyze_user_permissions(
        self,
        user_id: UUID,
        analysis_period_days: int = 90
    ) -> OptimizationResult:
        # Get user's permission usage history
        usage_data = await self.analyzer.get_usage_data(user_id, analysis_period_days)
        
        # Identify unused permissions
        unused = self.analyzer.find_unused_permissions(usage_data)
        
        # Suggest role optimizations
        role_suggestions = self.analyzer.suggest_role_changes(usage_data)
        
        # Calculate over-privilege score
        over_privilege_score = self.analyzer.calculate_over_privilege_score(usage_data)
        
        return OptimizationResult(
            unused_permissions=unused,
            role_suggestions=role_suggestions,
            over_privilege_score=over_privilege_score
        )

class NaturalLanguageService:
    def __init__(self, nlp_model: LanguageModel, intent_classifier: IntentClassifier):
        self.nlp_model = nlp_model
        self.intent_classifier = intent_classifier
    
    async def process_query(self, query: str, context: dict) -> NLPResult:
        # Classify intent
        intent = await self.intent_classifier.classify(query)
        
        # Extract entities
        entities = await self.nlp_model.extract_entities(query)
        
        # Process based on intent
        if intent == "check_access":
            return await self._handle_access_check(entities, context)
        elif intent == "grant_permission":
            return await self._handle_permission_grant(entities, context)
        else:
            return NLPResult(
                intent=intent,
                entities=entities,
                response="I didn't understand that query. Please try again."
            )
```

## 3. Database Schema

All tables use the `sentinel` schema in PostgreSQL:

```sql
CREATE SCHEMA IF NOT EXISTS sentinel;

-- Example table creation
CREATE TABLE sentinel.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    type sentinel.tenant_type NOT NULL DEFAULT 'root',
    parent_tenant_id UUID REFERENCES sentinel.tenants(id),
    isolation_mode sentinel.isolation_mode NOT NULL DEFAULT 'shared',
    settings JSONB DEFAULT '{}',
    features TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

Refer to the complete PostgreSQL Database Schema document for all table definitions.

## 4. API Implementation Examples

### 4.1 Permission Check Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import asyncio

router = APIRouter()

@router.post("/api/v1/permissions/check")
async def check_permission(
    request: PermissionCheckRequest,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    cache: RedisCache = Depends(get_cache)
):
    # Validate user has permission to check permissions
    if not await can_check_permissions(current_user, request.user_id):
        raise HTTPException(403, "Insufficient permissions")
    
    # Try cache first
    cache_key = f"perm:{request.user_id}:{request.resource.type}:{request.resource.id}:{request.action}"
    cached_result = await cache.get(cache_key)
    
    if cached_result:
        return PermissionCheckResponse.parse_raw(cached_result)
    
    # Evaluate permission
    result = await permission_service.check_permission(
        user_id=request.user_id,
        resource=request.resource,
        action=request.action,
        context=request.context
    )
    
    # Get field permissions
    field_perms = await permission_service.get_field_permissions(
        request.user_id,
        request.resource
    )
    
    response = PermissionCheckResponse(
        allowed=result.allowed,
        reason=result.reason,
        field_permissions=field_perms
    )
    
    # Cache result
    await cache.setex(cache_key, 300, response.json())
    
    # Audit log
    await audit_service.log_permission_check(
        user_id=request.user_id,
        resource=request.resource,
        action=request.action,
        result=result.allowed
    )
    
    return response
```

### 4.2 Role Permission Assignment

```python
@router.post("/api/v1/roles/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: UUID,
    permissions: List[PermissionAssignment],
    current_user: User = Depends(get_current_user),
    role_service: RoleService = Depends(get_role_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    # Check if user can modify roles
    if not await permission_service.check_permission(
        user=current_user,
        resource=Resource(type="role", id=str(role_id)),
        action="update"
    ):
        raise HTTPException(403, "Insufficient permissions")
    
    # Validate role exists and belongs to user's tenant
    role = await role_service.get_role(role_id)
    if not role or role.tenant_id != current_user.tenant_id:
        raise HTTPException(404, "Role not found")
    
    # Validate permissions
    for perm in permissions:
        if not await permission_service.can_grant_permission(
            current_user, perm.resource_type, perm.actions
        ):
            raise HTTPException(
                403, 
                f"Cannot grant {perm.actions} on {perm.resource_type}"
            )
    
    # Assign permissions
    await role_service.assign_permissions(role_id, permissions)
    
    # Invalidate cache for all users with this role
    await invalidate_role_cache(role_id)
    
    # Audit log
    await audit_service.log_role_permission_change(
        user=current_user,
        role_id=role_id,
        permissions=permissions,
        action="assign"
    )
    
    return {"status": "success", "permissions_assigned": len(permissions)}
```

### 4.3 AI-Powered Anomaly Detection

```python
@router.post("/api/v1/ai/anomaly/check")
async def check_access_anomaly(
    request: AnomalyCheckRequest,
    current_user: User = Depends(get_current_user),
    anomaly_service: AnomalyDetectionService = Depends(get_anomaly_service),
    notification_service: NotificationService = Depends(get_notification_service)
):
    # Check anomaly
    result = await anomaly_service.check_anomaly(
        user_id=request.user_id,
        access_request=request.access_request
    )
    
    # If high risk, take action
    if result.risk_score > 0.85:
        # Send alert
        await notification_service.send_security_alert(
            user_id=request.user_id,
            anomaly=result
        )
        
        # Log to audit
        await audit_service.log_anomaly_detected(
            user_id=request.user_id,
            anomaly=result
        )
    
    return result
```

## 5. Caching Strategy Implementation

```python
class PermissionCache:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
    
    async def get_user_permissions(self, user_id: UUID, tenant_id: UUID) -> Optional[List[Permission]]:
        key = f"perms:{tenant_id}:{user_id}"
        data = await self.redis.get(key)
        if data:
            return [Permission.parse_raw(p) for p in json.loads(data)]
        return None
    
    async def set_user_permissions(
        self, 
        user_id: UUID, 
        tenant_id: UUID, 
        permissions: List[Permission]
    ):
        key = f"perms:{tenant_id}:{user_id}"
        data = json.dumps([p.json() for p in permissions])
        await self.redis.setex(key, self.default_ttl, data)
    
    async def invalidate_user(self, user_id: UUID, tenant_id: UUID):
        pattern = f"perms:{tenant_id}:{user_id}*"
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)
    
    async def invalidate_role(self, role_id: UUID):
        # Get all users with this role
        users = await get_users_by_role(role_id)
        
        # Invalidate cache for each user
        for user in users:
            await self.invalidate_user(user.id, user.tenant_id)
```

## 6. Middleware Implementation

### 6.1 Authentication Middleware

```python
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class AuthenticationMiddleware:
    def __init__(self, token_service: TokenService):
        self.token_service = token_service
        self.bearer = HTTPBearer()
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in PUBLIC_ENDPOINTS:
            return await call_next(request)
        
        # Extract token
        try:
            credentials: HTTPAuthorizationCredentials = await self.bearer(request)
            token = credentials.credentials
        except HTTPException:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing authentication token"}
            )
        
        # Validate token
        try:
            payload = await self.token_service.validate_token(token)
            request.state.user_id = payload["sub"]
            request.state.tenant_id = payload["tenant_id"]
            request.state.roles = payload.get("roles", [])
        except TokenExpiredError:
            return JSONResponse(
                status_code=401,
                content={"error": "Token expired"}
            )
        except InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid token"}
            )
        
        response = await call_next(request)
        return response
```

### 6.2 Tenant Isolation Middleware

```python
class TenantContextMiddleware:
    async def __call__(self, request: Request, call_next):
        # Set tenant context for all database queries
        if hasattr(request.state, "tenant_id"):
            tenant_id = request.state.tenant_id
            
            # Set tenant context in thread-local storage
            set_current_tenant(tenant_id)
            
            # Add tenant filter to SQLAlchemy queries
            with tenant_scope(tenant_id):
                response = await call_next(request)
        else:
            response = await call_next(request)
        
        return response
```

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/unit/test_permission_evaluator.py
import pytest
from unittest.mock import Mock, AsyncMock

class TestPermissionEvaluator:
    @pytest.fixture
    def evaluator(self):
        role_service = Mock()
        cache = AsyncMock()
        return PermissionEvaluator(role_service, cache)
    
    async def test_check_permission_with_cache_hit(self, evaluator):
        # Setup
        evaluator.cache.get.return_value = {
            "allowed": True,
            "reason": "Cached permission"
        }
        
        # Execute
        result = await evaluator.check_permission(
            user_id=UUID("123"),
            resource=Resource(type="document", id="456"),
            action="read"
        )
        
        # Assert
        assert result.allowed is True
        assert evaluator.cache.get.called
        assert not evaluator.role_service.get_user_permissions.called
    
    async def test_check_permission_with_conditions(self, evaluator):
        # Setup
        evaluator.cache.get.return_value = None
        evaluator._get_user_permissions = AsyncMock(return_value=[
            Permission(
                resource_type="document",
                resource_id="*",
                actions=["read", "write"],
                conditions={"department": "engineering"}
            )
        ])
        
        # Execute
        result = await evaluator.check_permission(
            user_id=UUID("123"),
            resource=Resource(type="document", id="456"),
            action="read",
            context={"department": "engineering"}
        )
        
        # Assert
        assert result.allowed is True
        assert evaluator.cache.set.called
```

### 7.2 Integration Tests

```python
# tests/integration/test_auth_flow.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

class TestAuthenticationFlow:
    @pytest.fixture
    async def client(self, app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.fixture
    async def test_user(self, db: AsyncSession):
        user = User(
            email="test@example.com",
            password_hash=hash_password("testpass"),
            tenant_id=UUID("test-tenant")
        )
        db.add(user)
        await db.commit()
        return user
    
    async def test_login_success(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpass",
                "tenant_id": "test-tenant"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    async def test_protected_endpoint_with_token(self, client: AsyncClient, test_user):
        # Login first
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpass",
                "tenant_id": "test-tenant"
            }
        )
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = await client.get(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
```

## 8. Performance Optimization

### 8.1 Database Query Optimization

```python
# Optimized permission query with joins
class PermissionRepository:
    async def get_user_permissions_optimized(self, user_id: UUID) -> List[Permission]:
        query = """
        WITH user_roles AS (
            -- Direct roles
            SELECT ur.role_id
            FROM sentinel.user_roles ur
            WHERE ur.user_id = :user_id AND ur.is_active = true
            
            UNION
            
            -- Roles from groups
            SELECT gr.role_id
            FROM sentinel.user_groups ug
            JOIN sentinel.group_roles gr ON ug.group_id = gr.group_id
            WHERE ug.user_id = :user_id
        ),
        role_hierarchy AS (
            -- Recursive CTE for role inheritance
            SELECT r.id, r.parent_role_id
            FROM sentinel.roles r
            WHERE r.id IN (SELECT role_id FROM user_roles)
            
            UNION ALL
            
            SELECT r.id, r.parent_role_id
            FROM sentinel.roles r
            JOIN role_hierarchy rh ON r.id = rh.parent_role_id
        )
        SELECT DISTINCT p.*
        FROM sentinel.permissions p
        JOIN sentinel.role_permissions rp ON p.id = rp.permission_id
        WHERE rp.role_id IN (SELECT id FROM role_hierarchy)
        AND p.is_active = true
        """
        
        result = await self.db.execute(query, {"user_id": user_id})
        return [Permission.from_orm(row) for row in result]
```

### 8.2 Connection Pooling

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

class DatabaseConfig:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=40,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session
```

## 9. Security Implementation

### 9.1 Input Validation

```python
from pydantic import BaseModel, validator, EmailStr
from typing import Optional, List
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None
    roles: Optional[List[UUID]] = []
    groups: Optional[List[UUID]] = []
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain digit')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_-]{3,32}, v):
            raise ValueError('Invalid username format')
        return v
```

### 9.2 SQL Injection Prevention

```python
# Using SQLAlchemy ORM with parameterized queries
class UserRepository:
    async def get_by_email(self, email: str, tenant_id: UUID) -> Optional[User]:
        # Safe: Uses parameterized query
        query = select(User).where(
            User.email == email,
            User.tenant_id == tenant_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_users(self, search_term: str, tenant_id: UUID) -> List[User]:
        # Safe: Properly escapes search term
        query = select(User).where(
            User.tenant_id == tenant_id,
            or_(
                User.email.ilike(f"%{search_term}%"),
                User.username.ilike(f"%{search_term}%")
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
```

## 10. Monitoring and Observability

### 10.1 Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
auth_attempts = Counter(
    'sentinel_auth_attempts_total',
    'Total authentication attempts',
    ['tenant_id', 'method', 'status']
)

permission_checks = Counter(
    'sentinel_permission_checks_total',
    'Total permission checks',
    ['tenant_id', 'resource_type', 'action', 'result']
)

api_request_duration = Histogram(
    'sentinel_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status']
)

active_users = Gauge(
    'sentinel_active_users',
    'Number of active users',
    ['tenant_id']
)

cache_operations = Counter(
    'sentinel_cache_operations_total',
    'Cache operations',
    ['operation', 'result']
)

# Usage in code
class MetricsMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise
        finally:
            duration = time.time() - start_time
            api_request_duration.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status
            ).observe(duration)
        
        return response
```

### 10.2 Structured Logging

```python
import structlog
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id')
tenant_id_var: ContextVar[str] = ContextVar('tenant_id')
user_id_var: ContextVar[str] = ContextVar('user_id')

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.contextvars.merge_contextvars,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in services
class AuthService:
    async def authenticate_user(self, email: str, tenant_id: str):
        logger.info(
            "authentication_attempt",
            email=email,
            tenant_id=tenant_id,
            ip_address=self.request.client.host
        )
        
        try:
            user = await self._verify_credentials(email, password)
            logger.info(
                "authentication_success",
                user_id=str(user.id),
                tenant_id=str(user.tenant_id)
            )
            return user
        except AuthenticationError as e:
            logger.warning(
                "authentication_failed",
                email=email,
                reason=str(e)
            )
            raise
```

## 11. Error Handling

```python
# utils/exceptions.py
class SentinelException(Exception):
    """Base exception for Sentinel platform"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class AuthenticationError(SentinelException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_FAILED")

class PermissionDeniedError(SentinelException):
    """Permission denied"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "PERMISSION_DENIED")

class ResourceNotFoundError(SentinelException):
    """Resource not found"""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, "RESOURCE_NOT_FOUND")

# Global error handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(SentinelException)
async def sentinel_exception_handler(request: Request, exc: SentinelException):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message
            },
            "request_id": request.state.request_id
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": exc.errors()
            },
            "request_id": request.state.request_id
        }
    )
```

## 12. Deployment Configuration

### 12.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/prod.txt .
RUN pip install --no-cache-dir -r prod.txt

# Copy application
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create non-root user
RUN useradd -m -u 1000 sentinel && chown -R sentinel:sentinel /app
USER sentinel

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 12.2 Environment Configuration

```python
# config.py
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Sentinel Access Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str
    DATABASE_SCHEMA: str = "sentinel"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    
    # Redis
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    CACHE_TTL: int = 300
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # AI Features
    AI_ENABLED: bool = True
    AI_MODEL_PATH: str = "/app/models"
    ANOMALY_DETECTION_THRESHOLD: float = 0.7
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```