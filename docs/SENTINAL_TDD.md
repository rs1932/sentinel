# Technical Design Document (TDD)
## Sentinel Access Platform
### Version 2.0 - Complete Implementation with All Components

## 1. System Overview

The Sentinel Access Platform is designed as a modular monolith architecture using Python 3.10 and FastAPI, with clear separation of concerns between authentication, authorization, resource management, approval workflows, and AI-powered features. The system uses PostgreSQL with a dedicated `sentinel` schema for all database objects and supports both Redis and in-memory caching through a factory pattern.

## 2. Component Design

### 2.1 Auth Service
**Responsibilities:**
- JWT token generation and validation
- User and service account authentication (unified)
- Token refresh logic
- Token blacklisting
- API key management for service accounts

**Key Classes:**
```python
class AuthService:
    def __init__(self, 
                 user_repo: UserRepository, 
                 token_manager: TokenManager,
                 cache_service: CacheServiceInterface):
        self.user_repo = user_repo
        self.token_manager = token_manager
        self.cache = cache_service
    
    async def authenticate_user(self, email: str, password: str, tenant_id: UUID) -> TokenPair:
        user = await self.user_repo.get_by_email(email, tenant_id)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise AccountLockedError(f"Account locked until {user.locked_until}")
        
        access_token = self.token_manager.create_access_token(user)
        refresh_token = self.token_manager.create_refresh_token(user)
        
        # Update login stats
        await self.user_repo.update_login_stats(user.id)
        
        return TokenPair(access_token, refresh_token)
    
    async def authenticate_service_account(self, api_key: str) -> Token:
        # Service accounts use the same users table with is_service_account=True
        account = await self.user_repo.get_by_service_account_key(api_key)
        if not account or not account.is_service_account:
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
            "is_service_account": user.is_service_account,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # For blacklisting
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
```

### 2.2 Permission Service (Enhanced)
**Responsibilities:**
- Permission evaluation with approval chain integration
- Policy engine implementation
- Three-tier field-level access control
- Dynamic attribute evaluation
- Permission caching with factory pattern

**Key Classes:**
```python
class PermissionEvaluator:
    def __init__(self, 
                 role_service: RoleService,
                 approval_service: ApprovalChainService,
                 cache_factory: CacheServiceFactory):
        self.role_service = role_service
        self.approval_service = approval_service
        self.cache = cache_factory.get_cache_service()
    
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
        
        # Check if approval is required
        if await self.approval_service.needs_approval(user_id, resource, action):
            return PermissionResult(
                allowed=False,
                requires_approval=True,
                approval_chain_id=await self.approval_service.get_chain_id(resource)
            )
        
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
        resource: Resource,
        entity_type: str
    ) -> Dict[str, Dict[str, List[str]]]:
        """Get three-tier field permissions"""
        permissions = await self._get_user_permissions(user_id)
        
        field_perms = {
            "core": {},
            "platform_dynamic": {},
            "tenant_specific": {}
        }
        
        for perm in permissions:
            if self._matches_resource(perm, resource):
                for tier, fields in perm.field_permissions.items():
                    for field, actions in fields.items():
                        if field not in field_perms[tier]:
                            field_perms[tier][field] = []
                        field_perms[tier][field].extend(actions)
        
        return field_perms
```

### 2.3 Approval Chain Service (NEW)
**Responsibilities:**
- Approval workflow management
- Multi-level approval processing
- Automatic escalation
- Auto-approval evaluation

**Key Classes:**
```python
class ApprovalChainService:
    def __init__(self, 
                 approval_repo: ApprovalRepository,
                 notification_service: NotificationService):
        self.approval_repo = approval_repo
        self.notification_service = notification_service
    
    async def create_access_request(
        self,
        requester_id: UUID,
        request_details: dict,
        justification: str = None
    ) -> AccessRequest:
        # Find applicable approval chain
        chain = await self._find_approval_chain(request_details)
        
        if not chain:
            # No approval needed
            return None
        
        # Check auto-approval conditions
        if await self._check_auto_approval(chain, requester_id, request_details):
            return await self._auto_approve_request(requester_id, request_details)
        
        # Create request
        request = await self.approval_repo.create_request(
            requester_id=requester_id,
            request_details=request_details,
            justification=justification,
            chain_id=chain.id
        )
        
        # Notify first-level approvers
        await self._notify_approvers(request, level=1)
        
        return request
    
    async def process_approval(
        self,
        request_id: UUID,
        approver_id: UUID,
        decision: str,
        comments: str = None
    ) -> ApprovalResult:
        request = await self.approval_repo.get_request(request_id)
        
        # Validate approver
        if not await self._can_approve(approver_id, request):
            raise PermissionDeniedError("Not authorized to approve this request")
        
        # Record decision
        approval = await self.approval_repo.record_approval(
            request_id=request_id,
            approver_id=approver_id,
            decision=decision,
            comments=comments
        )
        
        if decision == "approved":
            # Check if all levels approved
            if await self._all_levels_approved(request):
                await self._grant_access(request)
                return ApprovalResult(status="completed", access_granted=True)
            else:
                # Notify next level
                next_level = await self._get_next_level(request)
                await self._notify_approvers(request, level=next_level)
                return ApprovalResult(status="pending_next_level")
        else:
            # Denied
            await self._deny_access(request)
            return ApprovalResult(status="denied", access_granted=False)
    
    async def check_escalations(self):
        """Background task to handle timeout escalations"""
        expired_approvals = await self.approval_repo.get_expired_approvals()
        
        for approval in expired_approvals:
            await self._escalate_approval(approval)
```

### 2.4 Behavioral Biometrics Service (NEW)
**Responsibilities:**
- Keystroke dynamics analysis
- Mouse pattern tracking
- Continuous authentication
- Deviation scoring

**Key Classes:**
```python
class BiometricsService:
    def __init__(self,
                 biometrics_repo: BiometricsRepository,
                 ml_service: MLService):
        self.biometrics_repo = biometrics_repo
        self.ml_service = ml_service
    
    async def capture_keystroke_dynamics(
        self,
        user_id: UUID,
        session_id: UUID,
        keystroke_data: List[KeystrokeEvent]
    ) -> None:
        """Capture and analyze keystroke patterns"""
        # Calculate typing cadence
        cadence = self._calculate_cadence(keystroke_data)
        
        # Calculate dwell and flight times
        dwell_times = self._calculate_dwell_times(keystroke_data)
        flight_times = self._calculate_flight_times(keystroke_data)
        
        biometric_data = {
            "cadence": cadence,
            "dwell_times": dwell_times,
            "flight_times": flight_times,
            "pattern_hash": self._generate_pattern_hash(keystroke_data)
        }
        
        await self.biometrics_repo.store_keystroke_data(
            user_id, session_id, biometric_data
        )
    
    async def analyze_mouse_patterns(
        self,
        user_id: UUID,
        session_id: UUID,
        mouse_data: List[MouseEvent]
    ) -> None:
        """Analyze mouse movement patterns"""
        patterns = {
            "velocity": self._calculate_velocity(mouse_data),
            "acceleration": self._calculate_acceleration(mouse_data),
            "curvature": self._calculate_curvature(mouse_data),
            "click_patterns": self._analyze_clicks(mouse_data)
        }
        
        await self.biometrics_repo.store_mouse_patterns(
            user_id, session_id, patterns
        )
    
    async def calculate_deviation_score(
        self,
        user_id: UUID,
        current_session: UUID
    ) -> float:
        """Calculate deviation from user's baseline behavior"""
        # Get baseline profile
        baseline = await self.biometrics_repo.get_baseline_profile(user_id)
        
        if not baseline:
            # New user, create baseline
            return await self._create_baseline(user_id, current_session)
        
        # Get current session data
        current_data = await self.biometrics_repo.get_session_data(current_session)
        
        # Calculate deviation using ML model
        deviation = await self.ml_service.calculate_behavioral_deviation(
            baseline, current_data
        )
        
        # Update baseline with exponential moving average
        if deviation < 0.3:  # Normal behavior
            await self._update_baseline(user_id, current_data)
        
        return deviation
    
    async def continuous_authentication(
        self,
        user_id: UUID,
        session_id: UUID
    ) -> AuthenticationStatus:
        """Perform continuous authentication based on behavior"""
        deviation = await self.calculate_deviation_score(user_id, session_id)
        
        if deviation < 0.3:
            return AuthenticationStatus.AUTHENTICATED
        elif deviation < 0.7:
            return AuthenticationStatus.SUSPICIOUS
        else:
            return AuthenticationStatus.UNAUTHORIZED
```

### 2.5 AI Service Components (Enhanced)
**Responsibilities:**
- Anomaly detection with behavioral integration
- Permission optimization
- Natural language processing
- Predictive access
- Compliance monitoring
- Feature store management

**Key Classes:**
```python
class AnomalyDetectionService:
    def __init__(self, 
                 ml_model_registry: ModelRegistry,
                 user_behavior_repo: UserBehaviorRepository,
                 biometrics_service: BiometricsService,
                 feature_store: FeatureStoreService):
        self.model_registry = ml_model_registry
        self.user_behavior_repo = user_behavior_repo
        self.biometrics_service = biometrics_service
        self.feature_store = feature_store
    
    async def check_anomaly(
        self,
        user_id: UUID,
        access_request: AccessRequest,
        session_id: UUID = None
    ) -> AnomalyResult:
        # Get user's behavior profile
        profile = await self.user_behavior_repo.get_profile(user_id)
        
        # Get pre-computed features from feature store
        ml_features = await self.feature_store.get_features(
            "user_access_patterns", user_id
        )
        
        # Include biometric deviation if available
        biometric_score = 0.0
        if session_id:
            biometric_score = await self.biometrics_service.calculate_deviation_score(
                user_id, session_id
            )
        
        # Extract real-time features
        features = self._extract_features(access_request, profile, ml_features)
        features['biometric_deviation'] = biometric_score
        
        # Get active model
        model = await self.model_registry.get_active_model('anomaly_detection')
        
        # Predict anomaly
        anomaly_score = model.predict_proba([features])[0]
        
        if anomaly_score > 0.7:
            anomaly_types = self._identify_anomaly_types(features, profile)
            
            # Log to database
            await self._log_anomaly(user_id, access_request, anomaly_score, anomaly_types)
            
            return AnomalyResult(
                detected=True,
                risk_score=anomaly_score,
                anomaly_types=anomaly_types,
                recommended_actions=self._get_recommended_actions(anomaly_score),
                require_mfa=anomaly_score > 0.85,
                block_access=anomaly_score > 0.95
            )
        
        return AnomalyResult(detected=False, risk_score=anomaly_score)

class FeatureStoreService:
    def __init__(self,
                 feature_repo: FeatureRepository,
                 compute_engine: ComputeEngine):
        self.feature_repo = feature_repo
        self.compute_engine = compute_engine
    
    async def compute_features(
        self,
        feature_set: str,
        entity_type: str,
        entity_id: UUID
    ) -> dict:
        """Compute ML features for an entity"""
        # Get feature definition
        definition = await self._get_feature_definition(feature_set)
        
        # Compute features based on definition
        features = await self.compute_engine.compute(
            definition, entity_type, entity_id
        )
        
        # Store in feature store with TTL
        await self.feature_repo.store_features(
            feature_set, entity_type, entity_id, features,
            ttl=settings.FEATURE_STORE_TTL
        )
        
        return features
    
    async def get_features(
        self,
        feature_set: str,
        entity_id: UUID
    ) -> dict:
        """Get pre-computed features or compute if missing"""
        features = await self.feature_repo.get_features(feature_set, entity_id)
        
        if not features or self._is_expired(features):
            # Recompute features
            entity_type = await self._get_entity_type(entity_id)
            features = await self.compute_features(
                feature_set, entity_type, entity_id
            )
        
        return features

class AIAgentService:
    def __init__(self,
                 agent_repo: AgentRepository,
                 message_queue: MessageQueue):
        self.agent_repo = agent_repo
        self.message_queue = message_queue
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize AI agents"""
        self.agents['anomaly_detector'] = AnomalyDetectorAgent()
        self.agents['permission_optimizer'] = PermissionOptimizerAgent()
        self.agents['compliance_monitor'] = ComplianceMonitorAgent()
        self.agents['coordinator'] = CoordinatorAgent()
    
    async def send_agent_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: dict,
        priority: str = 'normal'
    ) -> UUID:
        """Send message between AI agents"""
        message = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            priority=priority,
            content=content,
            correlation_id=uuid.uuid4()
        )
        
        await self.agent_repo.store_message(message)
        
        if priority == 'critical':
            # Process immediately
            await self._process_message(message)
        else:
            # Queue for processing
            await self.message_queue.enqueue(message)
        
        return message.correlation_id
    
    async def process_agent_messages(self):
        """Background task to process agent messages"""
        while True:
            messages = await self.agent_repo.get_unprocessed_messages()
            
            for message in messages:
                try:
                    await self._process_message(message)
                except Exception as e:
                    await self._handle_processing_error(message, e)
            
            await asyncio.sleep(settings.AGENT_MESSAGE_TIMEOUT)
```

## 3. Database Schema Implementation

All tables use the `sentinel` schema in PostgreSQL:

```python
# src/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# All tables in sentinel schema
metadata = MetaData(schema="sentinel")
Base = declarative_base(metadata=metadata)
```

Example model implementation:
```python
# src/models/user.py
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('sentinel.tenants.id'), nullable=False)
    email = Column(String(255), nullable=False)
    username = Column(String(100))
    password_hash = Column(String(255))  # NULL for SSO users
    is_service_account = Column(Boolean, default=False)
    service_account_key = Column(String(255), unique=True)  # For M2M
    attributes = Column(JSONB, default={})
    preferences = Column(JSONB, default={})
    last_login = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    failed_login_count = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    roles = relationship("Role", secondary="sentinel.user_roles", back_populates="users")
    groups = relationship("Group", secondary="sentinel.user_groups", back_populates="users")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='unique_email_per_tenant'),
        CheckConstraint(
            "(is_service_account = true AND service_account_key IS NOT NULL AND password_hash IS NULL) OR "
            "(is_service_account = false)",
            name='check_service_account'
        ),
        {'schema': 'sentinel'}
    )
```

## 4. API Implementation Examples

### 4.1 Permission Check with Approval Integration

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
    approval_service: ApprovalChainService = Depends(get_approval_service),
    cache_factory: CacheServiceFactory = Depends(get_cache_factory)
):
    # Get appropriate cache service
    cache = cache_factory.get_cache_service()
    
    # Validate user has permission to check permissions
    if not await can_check_permissions(current_user, request.user_id):
        raise HTTPException(403, "Insufficient permissions")
    
    # Try cache first
    cache_key = f"perm:{request.user_id}:{request.resource.type}:{request.resource.id}:{request.action}"
    cached_result = await cache.get(cache_key)
    
    if cached_result:
        return PermissionCheckResponse.parse_raw(cached_result)
    
    # Check if approval is required
    if await approval_service.needs_approval(
        request.user_id, request.resource, request.action
    ):
        # Create access request
        access_request = await approval_service.create_access_request(
            requester_id=request.user_id,
            request_details={
                "resource": request.resource.dict(),
                "action": request.action
            },
            justification=request.justification
        )
        
        return PermissionCheckResponse(
            allowed=False,
            requires_approval=True,
            approval_request_id=access_request.id,
            reason="Approval required for this action"
        )
    
    # Evaluate permission
    result = await permission_service.check_permission(
        user_id=request.user_id,
        resource=request.resource,
        action=request.action,
        context=request.context
    )
    
    # Get three-tier field permissions
    field_perms = await permission_service.get_field_permissions(
        request.user_id,
        request.resource,
        request.resource.type
    )
    
    response = PermissionCheckResponse(
        allowed=result.allowed,
        reason=result.reason,
        field_permissions=field_perms,
        matched_conditions=result.matched_conditions
    )
    
    # Cache result
    await cache.set(cache_key, response.json(), ttl=300)
    
    # Audit log
    await audit_service.log_permission_check(
        user_id=request.user_id,
        resource=request.resource,
        action=request.action,
        result=result.allowed
    )
    
    return response
```

### 4.2 Biometric Capture Endpoint

```python
@router.post("/api/v1/ai/biometrics/capture")
async def capture_biometrics(
    biometric_data: BiometricCaptureRequest,
    current_user: User = Depends(get_current_user),
    biometrics_service: BiometricsService = Depends(get_biometrics_service),
    anomaly_service: AnomalyDetectionService = Depends(get_anomaly_service)
):
    # Capture keystroke dynamics
    if biometric_data.keystroke_events:
        await biometrics_service.capture_keystroke_dynamics(
            user_id=current_user.id,
            session_id=biometric_data.session_id,
            keystroke_data=biometric_data.keystroke_events
        )
    
    # Capture mouse patterns
    if biometric_data.mouse_events:
        await biometrics_service.analyze_mouse_patterns(
            user_id=current_user.id,
            session_id=biometric_data.session_id,
            mouse_data=biometric_data.mouse_events
        )
    
    # Calculate deviation score
    deviation_score = await biometrics_service.calculate_deviation_score(
        user_id=current_user.id,
        current_session=biometric_data.session_id
    )
    
    # Check for anomalies
    if deviation_score > settings.KEYSTROKE_THRESHOLD:
        # Trigger anomaly detection
        anomaly_result = await anomaly_service.check_anomaly(
            user_id=current_user.id,
            access_request=None,  # Context from biometrics
            session_id=biometric_data.session_id
        )
        
        if anomaly_result.block_access:
            # Force re-authentication
            raise HTTPException(401, "Behavioral anomaly detected. Please re-authenticate.")
    
    return {
        "deviation_score": deviation_score,
        "status": "captured",
        "continuous_auth": deviation_score < 0.3
    }
```

## 5. Caching Strategy Implementation (Factory Pattern)

```python
# src/services/cache_service.py
from abc import ABC, abstractmethod
from typing import Optional, Any
from datetime import datetime, timedelta
import json
import redis.asyncio as redis

class CacheServiceInterface(ABC):
    """Abstract base class for cache services"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        pass
    
    @abstractmethod
    async def get_stats(self) -> dict:
        pass

class InMemoryCacheService(CacheServiceInterface):
    """In-memory cache implementation for development"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if key in self._expiry and datetime.now() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                self._stats["misses"] += 1
                return None
            self._stats["hits"] += 1
            return self._cache[key]
        self._stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        self._cache[key] = value
        self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
        self._stats["sets"] += 1
    
    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        self._stats["deletes"] += 1
    
    async def clear(self) -> None:
        self._cache.clear()
        self._expiry.clear()
    
    async def get_stats(self) -> dict:
        return {
            **self._stats,
            "size": len(self._cache),
            "hit_rate": self._stats["hits"] / max(1, self._stats["hits"] + self._stats["misses"])
        }

class RedisCacheService(CacheServiceInterface):
    """Redis-based cache implementation for production"""
    
    def __init__(self, redis_url: str):
        self.redis_client = None
        self.redis_url = redis_url
    
    async def _ensure_connected(self):
        if not self.redis_client:
            self.redis_client = await redis.from_url(self.redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        await self._ensure_connected()
        value = await self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        await self._ensure_connected()
        await self.redis_client.setex(
            key, ttl, json.dumps(value, default=str)
        )
    
    async def delete(self, key: str) -> None:
        await self._ensure_connected()
        await self.redis_client.delete(key)
    
    async def clear(self) -> None:
        await self._ensure_connected()
        await self.redis_client.flushdb()
    
    async def get_stats(self) -> dict:
        await self._ensure_connected()
        info = await self.redis_client.info("stats")
        return {
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / 
                       max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
        }

class CacheServiceFactory:
    """Factory for creating cache service instances"""
    
    _instance = None
    
    @classmethod
    def get_cache_service(cls, settings=None) -> CacheServiceInterface:
        if settings is None:
            from src.config import settings
        
        if not cls._instance:
            if settings.REDIS_ENABLED:
                cls._instance = RedisCacheService(settings.REDIS_URL)
            else:
                cls._instance = InMemoryCacheService()
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset singleton instance (for testing)"""
        cls._instance = None
```

## 6. Middleware Implementation

### 6.1 Authentication Middleware (Enhanced)

```python
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class AuthenticationMiddleware:
    def __init__(self, 
                 token_service: TokenService,
                 biometrics_service: BiometricsService):
        self.token_service = token_service
        self.biometrics_service = biometrics_service
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
            
            # Check if token is blacklisted
            if await self.token_service.is_blacklisted(payload.get("jti")):
                raise InvalidTokenError("Token has been revoked")
            
            request.state.user_id = payload["sub"]
            request.state.tenant_id = payload["tenant_id"]
            request.state.roles = payload.get("roles", [])
            request.state.is_service_account = payload.get("is_service_account", False)
            request.state.session_id = str(uuid.uuid4())
            
            # For regular users, check continuous authentication
            if not request.state.is_service_account:
                auth_status = await self.biometrics_service.continuous_authentication(
                    user_id=request.state.user_id,
                    session_id=request.state.session_id
                )
                
                if auth_status == AuthenticationStatus.UNAUTHORIZED:
                    return JSONResponse(
                        status_code=401,
                        content={"error": "Behavioral authentication failed"}
                    )
                elif auth_status == AuthenticationStatus.SUSPICIOUS:
                    request.state.require_mfa = True
            
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
            
            # Set tenant context in async context
            tenant_context.set(tenant_id)
            
            # Add tenant filter to SQLAlchemy queries
            with tenant_scope(tenant_id):
                response = await call_next(request)
        else:
            response = await call_next(request)
        
        return response

# Context manager for tenant isolation
from contextvars import ContextVar

tenant_context: ContextVar[UUID] = ContextVar('tenant_context')

class TenantScope:
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
        self.token = None
    
    def __enter__(self):
        self.token = tenant_context.set(self.tenant_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        tenant_context.reset(self.token)

def tenant_scope(tenant_id: UUID):
    return TenantScope(tenant_id)
```

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/unit/test_permission_evaluator.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.cache_service import CacheServiceFactory

class TestPermissionEvaluator:
    @pytest.fixture
    def cache_factory(self):
        # Reset factory and force in-memory cache for tests
        CacheServiceFactory.reset()
        mock_settings = Mock(REDIS_ENABLED=False)
        return CacheServiceFactory
    
    @pytest.fixture
    def evaluator(self, cache_factory):
        role_service = Mock()
        approval_service = AsyncMock()
        return PermissionEvaluator(role_service, approval_service, cache_factory)
    
    async def test_check_permission_with_approval_required(self, evaluator):
        # Setup
        evaluator.approval_service.needs_approval.return_value = True
        evaluator.approval_service.get_chain_id.return_value = UUID("chain-123")
        
        # Execute
        result = await evaluator.check_permission(
            user_id=UUID("user-123"),
            resource=Resource(type="sensitive_data", id="456"),
            action="delete"
        )
        
        # Assert
        assert result.allowed is False
        assert result.requires_approval is True
        assert result.approval_chain_id == UUID("chain-123")
    
    async def test_three_tier_field_permissions(self, evaluator):
        # Setup
        evaluator._get_user_permissions = AsyncMock(return_value=[
            Permission(
                resource_type="vessel",
                resource_id="*",
                actions=["read", "write"],
                field_permissions={
                    "core": {"vessel_name": ["read", "write"]},
                    "platform_dynamic": {"hazmat_code": ["read"]},
                    "tenant_specific": {"internal_notes": ["write"]}
                }
            )
        ])
        
        # Execute
        result = await evaluator.get_field_permissions(
            user_id=UUID("user-123"),
            resource=Resource(type="vessel", id="456"),
            entity_type="vessel"
        )
        
        # Assert
        assert "core" in result
        assert "platform_dynamic" in result
        assert "tenant_specific" in result
        assert result["core"]["vessel_name"] == ["read", "write"]
        assert result["platform_dynamic"]["hazmat_code"] == ["read"]
        assert result["tenant_specific"]["internal_notes"] == ["write"]
```

### 7.2 Integration Tests

```python
# tests/integration/test_approval_flow.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

class TestApprovalFlow:
    @pytest.fixture
    async def setup_approval_chain(self, db: AsyncSession):
        """Create test approval chain"""
        chain = ApprovalChain(
            tenant_id=UUID("test-tenant"),
            name="Sensitive Data Access",
            resource_type="sensitive_data",
            resource_pattern="sensitive_data:*",
            approval_levels=[
                {"level": 1, "approver_role": "manager", "timeout_hours": 24},
                {"level": 2, "approver_role": "director", "timeout_hours": 48}
            ]
        )
        db.add(chain)
        await db.commit()
        return chain
    
    async def test_permission_check_triggers_approval(
        self, 
        client: AsyncClient, 
        test_user,
        setup_approval_chain
    ):
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
        
        # Check permission that requires approval
        response = await client.post(
            "/api/v1/permissions/check",
            json={
                "user_id": str(test_user.id),
                "resource": {
                    "type": "sensitive_data",
                    "id": "confidential-001"
                },
                "action": "delete",
                "justification": "Cleanup old data"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert data["requires_approval"] is True
        assert "approval_request_id" in data
    
    async def test_biometric_continuous_auth(
        self,
        client: AsyncClient,
        authenticated_client
    ):
        # Capture biometric data
        response = await authenticated_client.post(
            "/api/v1/ai/biometrics/capture",
            json={
                "session_id": str(uuid.uuid4()),
                "keystroke_events": [
                    {"key": "a", "timestamp": 1000, "duration": 50},
                    {"key": "b", "timestamp": 1100, "duration": 45}
                ],
                "mouse_events": [
                    {"x": 100, "y": 200, "timestamp": 1000, "type": "move"},
                    {"x": 150, "y": 250, "timestamp": 1050, "type": "move"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deviation_score" in data
        assert data["continuous_auth"] is True or False
```

## 8. Performance Optimization

### 8.1 Database Query Optimization

```python
# Optimized permission query with all relationships
class PermissionRepository:
    async def get_user_permissions_optimized(self, user_id: UUID) -> List[Permission]:
        query = """
        WITH RECURSIVE role_hierarchy AS (
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
            
            UNION
            
            -- Parent roles (inheritance)
            SELECT r.parent_role_id
            FROM role_hierarchy rh
            JOIN sentinel.roles r ON rh.role_id = r.id
            WHERE r.parent_role_id IS NOT NULL
        )
        SELECT DISTINCT p.*
        FROM sentinel.permissions p
        JOIN sentinel.role_permissions rp ON p.id = rp.permission_id
        WHERE rp.role_id IN (SELECT role_id FROM role_hierarchy)
        AND p.is_active = true
        """
        
        result = await self.db.execute(query, {"user_id": user_id})
        return [Permission.from_orm(row) for row in result]
```

### 8.2 Connection Pooling (Python 3.10 Compatible)

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import sys

# Verify Python version
assert sys.version_info[:2] == (3, 10), "Python 3.10 is required"

class DatabaseConfig:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=40,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            future=True  # Use SQLAlchemy 2.0 style
        )
        
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            # Set schema search path for session
            await session.execute("SET search_path TO sentinel, public")
            yield session
```

## 9. Security Implementation

### 9.1 Input Validation with Three-Tier Fields

```python
from pydantic import BaseModel, validator, EmailStr
from typing import Optional, List, Dict
import re

class FieldPermissionModel(BaseModel):
    core: Dict[str, List[str]] = {}
    platform_dynamic: Dict[str, List[str]] = {}
    tenant_specific: Dict[str, List[str]] = {}
    
    @validator('*')
    def validate_field_actions(cls, v):
        valid_actions = {'read', 'write', 'hidden'}
        for field, actions in v.items():
            if not all(action in valid_actions for action in actions):
                raise ValueError(f'Invalid field action. Must be one of {valid_actions}')
        return v

class UserCreate(BaseModel):
    email: EmailStr
    password: Optional[str] = None  # Optional for SSO
    username: Optional[str] = None
    is_service_account: bool = False
    service_account_key: Optional[str] = None
    roles: Optional[List[UUID]] = []
    groups: Optional[List[UUID]] = []
    attributes: Optional[Dict] = {}
    
    @validator('password')
    def validate_password(cls, v, values):
        if not values.get('is_service_account') and v:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters')
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain uppercase letter')
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain lowercase letter')
            if not re.search(r'[0-9]', v):
                raise ValueError('Password must contain digit')
        return v
    
    @validator('service_account_key')
    def validate_service_account(cls, v, values):
        if values.get('is_service_account'):
            if not v:
                raise ValueError('Service account key required for service accounts')
            if values.get('password'):
                raise ValueError('Service accounts cannot have passwords')
        elif v:
            raise ValueError('Service account key only valid for service accounts')
        return v
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
    ['tenant_id', 'method', 'status', 'account_type']
)

permission_checks = Counter(
    'sentinel_permission_checks_total',
    'Total permission checks',
    ['tenant_id', 'resource_type', 'action', 'result', 'requires_approval']
)

approval_requests = Counter(
    'sentinel_approval_requests_total',
    'Total approval requests',
    ['tenant_id', 'resource_type', 'status']
)

biometric_deviations = Histogram(
    'sentinel_biometric_deviation_score',
    'Biometric deviation scores',
    ['user_type'],
    buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
)

cache_operations = Counter(
    'sentinel_cache_operations_total',
    'Cache operations',
    ['operation', 'result', 'cache_type']
)

ai_model_predictions = Histogram(
    'sentinel_ai_model_prediction_time_seconds',
    'AI model prediction time',
    ['model_type', 'model_version']
)

feature_store_operations = Counter(
    'sentinel_feature_store_operations_total',
    'Feature store operations',
    ['operation', 'feature_set', 'status']
)

active_approval_chains = Gauge(
    'sentinel_active_approval_chains',
    'Number of active approval chains',
    ['tenant_id', 'resource_type']
)

# Usage in services
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
session_id_var: ContextVar[str] = ContextVar('session_id')

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
            ip_address=self.request.client.host,
            account_type="user"
        )
        
        try:
            user = await self._verify_credentials(email, password)
            logger.info(
                "authentication_success",
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
                is_service_account=user.is_service_account
            )
            
            # Update metrics
            auth_attempts.labels(
                tenant_id=str(tenant_id),
                method="password",
                status="success",
                account_type="service" if user.is_service_account else "user"
            ).inc()
            
            return user
        except AuthenticationError as e:
            logger.warning(
                "authentication_failed",
                email=email,
                reason=str(e)
            )
            
            auth_attempts.labels(
                tenant_id=str(tenant_id),
                method="password",
                status="failed",
                account_type="unknown"
            ).inc()
            
            raise
```

## 11. Error Handling

```python
# utils/exceptions.py
class SentinelException(Exception):
    """Base exception for Sentinel platform"""
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(SentinelException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_FAILED")

class AccountLockedError(SentinelException):
    """Account is locked"""
    def __init__(self, message: str):
        super().__init__(message, "ACCOUNT_LOCKED")

class PermissionDeniedError(SentinelException):
    """Permission denied"""
    def __init__(self, message: str = "Permission denied", required_permission: str = None):
        super().__init__(
            message, 
            "PERMISSION_DENIED",
            {"required_permission": required_permission} if required_permission else {}
        )

class ApprovalRequiredError(SentinelException):
    """Approval required for action"""
    def __init__(self, approval_chain_id: UUID):
        super().__init__(
            "Approval required for this action",
            "APPROVAL_REQUIRED",
            {"approval_chain_id": str(approval_chain_id)}
        )

class BiometricAuthenticationError(SentinelException):
    """Biometric authentication failed"""
    def __init__(self, deviation_score: float):
        super().__init__(
            "Behavioral authentication failed",
            "BIOMETRIC_AUTH_FAILED",
            {"deviation_score": deviation_score}
        )

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
                "message": exc.message,
                "details": exc.details
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

### 12.1 Docker Configuration (Python 3.10)

```dockerfile
# Dockerfile
FROM python:3.10-slim

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
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str
    DATABASE_SCHEMA: str = "sentinel"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    
    # Redis (Initially disabled)
    REDIS_ENABLED: bool = False
    REDIS_URL: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 50
    CACHE_TTL: int = 300
    CACHE_BACKEND: str = "memory"  # memory or redis
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    
    # Service Accounts
    SERVICE_ACCOUNT_KEY_LENGTH: int = 64
    SERVICE_ACCOUNT_ROTATION_DAYS: int = 90
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Approval Chains
    APPROVAL_TIMEOUT_HOURS: int = 48
    AUTO_APPROVE_ENABLED: bool = False
    APPROVAL_ESCALATION_ENABLED: bool = True
    
    # Behavioral Biometrics
    BIOMETRICS_ENABLED: bool = False
    KEYSTROKE_THRESHOLD: float = 0.7
    MOUSE_PATTERN_THRESHOLD: float = 0.6
    CONTINUOUS_AUTH_INTERVAL: int = 300  # seconds
    
    # AI Features
    AI_ENABLED: bool = True
    AI_MODEL_PATH: str = "/app/models"
    ANOMALY_DETECTION_THRESHOLD: float = 0.7
    PREDICTION_CONFIDENCE_THRESHOLD: float = 0.8
    
    # ML Feature Store
    FEATURE_STORE_TTL: int = 3600
    FEATURE_COMPUTE_BATCH_SIZE: int = 100
    FEATURE_REFRESH_INTERVAL: int = 900  # seconds
    
    # AI Agent Communication
    AGENT_MESSAGE_TIMEOUT: int = 30
    AGENT_RETRY_COUNT: int = 3
    AGENT_PRIORITY_LEVELS: List[str] = ["low", "normal", "high", "critical"]
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Compliance
    COMPLIANCE_CHECKS_ENABLED: bool = True
    COMPLIANCE_REGULATIONS: List[str] = ["GDPR", "SOX", "HIPAA", "ISPS"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 13. Background Tasks

```python
# src/background/tasks.py
from celery import Celery
from datetime import datetime, timedelta
import asyncio

celery = Celery('sentinel', broker=settings.CELERY_BROKER_URL)

@celery.task
def process_approval_escalations():
    """Check and process approval escalations"""
    asyncio.run(_process_escalations())

async def _process_escalations():
    approval_service = ApprovalChainService()
    
    # Get pending approvals that have exceeded timeout
    expired = await approval_service.get_expired_approvals()
    
    for approval in expired:
        try:
            await approval_service.escalate_approval(approval)
            logger.info(
                "approval_escalated",
                approval_id=str(approval.id),
                level=approval.current_level
            )
        except Exception as e:
            logger.error(
                "escalation_failed",
                approval_id=str(approval.id),
                error=str(e)
            )

@celery.task
def refresh_ml_features():
    """Refresh pre-computed ML features"""
    asyncio.run(_refresh_features())

async def _refresh_features():
    feature_store = FeatureStoreService()
    
    # Get features that need refresh
    stale_features = await feature_store.get_stale_features()
    
    for feature_set in stale_features:
        try:
            await feature_store.refresh_feature_set(feature_set)
            logger.info(
                "features_refreshed",
                feature_set=feature_set.name,
                entity_count=feature_set.entity_count
            )
        except Exception as e:
            logger.error(
                "feature_refresh_failed",
                feature_set=feature_set.name,
                error=str(e)
            )

@celery.task
def train_ai_models():
    """Periodic AI model training"""
    asyncio.run(_train_models())

async def _train_models():
    model_service = AIModelService()
    
    # Check which models need retraining
    models_to_train = await model_service.get_models_for_training()
    
    for model_config in models_to_train:
        try:
            job = await model_service.start_training_job(model_config)
            logger.info(
                "model_training_started",
                model_type=model_config.type,
                job_id=str(job.id)
            )
        except Exception as e:
            logger.error(
                "model_training_failed",
                model_type=model_config.type,
                error=str(e)
            )

@celery.task
def compliance_check():
    """Run compliance checks"""
    asyncio.run(_run_compliance_checks())

async def _run_compliance_checks():
    compliance_service = ComplianceMonitoringService()
    
    for regulation in settings.COMPLIANCE_REGULATIONS:
        try:
            result = await compliance_service.check_compliance(regulation)
            
            if result.status != "compliant":
                await compliance_service.send_compliance_alert(result)
            
            logger.info(
                "compliance_check_completed",
                regulation=regulation,
                status=result.status,
                score=result.score
            )
        except Exception as e:
            logger.error(
                "compliance_check_failed",
                regulation=regulation,
                error=str(e)
            )

# Schedule periodic tasks
celery.conf.beat_schedule = {
    'process-escalations': {
        'task': 'tasks.process_approval_escalations',
        'schedule': timedelta(minutes=5),
    },
    'refresh-features': {
        'task': 'tasks.refresh_ml_features',
        'schedule': timedelta(minutes=15),
    },
    'train-models': {
        'task': 'tasks.train_ai_models',
        'schedule': timedelta(hours=24),
    },
    'compliance-check': {
        'task': 'tasks.compliance_check',
        'schedule': timedelta(hours=6),
    },
}
```

## 14. API Documentation

```python
# src/main.py - FastAPI app with complete documentation
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Sentinel Access Platform", version=settings.VERSION)
    await initialize_database()
    await initialize_cache()
    await load_ai_models()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sentinel Access Platform")
    await cleanup_connections()

app = FastAPI(
    title="Sentinel Access Platform",
    description="""
    Enterprise-grade access control system for multi-tenant SaaS applications.
    
    ## Features
    - 🔐 JWT-based authentication with service account support
    - 👥 Hierarchical role and group management
    - 🎯 Fine-grained permissions with three-tier field model
    - ✅ Multi-level approval workflows
    - 🤖 AI-powered anomaly detection and predictions
    - 🔍 Behavioral biometrics for continuous authentication
    - 📊 Comprehensive audit and compliance
    - 🚀 High-performance caching with factory pattern
    
    ## Technical Stack
    - Python 3.10 (strict requirement)
    - FastAPI (modular monolith)
    - PostgreSQL with sentinel schema
    - Redis (optional caching)
    - Machine Learning models
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add all middleware in correct order
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
app.add_middleware(MetricsMiddleware)

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns system status including:
    - Database connectivity
    - Cache availability
    - AI model status
    - Service health
    """
    return await check_system_health()

# Include all routers
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

API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{API_V1_PREFIX}/users", tags=["Users"])
app.include_router(roles_router, prefix=f"{API_V1_PREFIX}/roles", tags=["Roles"])
app.include_router(permissions_router, prefix=f"{API_V1_PREFIX}/permissions", tags=["Permissions"])
app.include_router(groups_router, prefix=f"{API_V1_PREFIX}/groups", tags=["Groups"])
app.include_router(tenants_router, prefix=f"{API_V1_PREFIX}/tenants", tags=["Tenants"])
app.include_router(resources_router, prefix=f"{API_V1_PREFIX}/resources", tags=["Resources"])
app.include_router(fields_router, prefix=f"{API_V1_PREFIX}/field-definitions", tags=["Fields"])
app.include_router(navigation_router, prefix=f"{API_V1_PREFIX}/navigation", tags=["Navigation"])
app.include_router(approvals_router, prefix=f"{API_V1_PREFIX}/approvals", tags=["Approvals"])
app.include_router(audit_router, prefix=f"{API_V1_PREFIX}/audit", tags=["Audit"])
app.include_router(ai_router, prefix=f"{API_V1_PREFIX}/ai", tags=["AI"])
app.include_router(biometrics_router, prefix=f"{API_V1_PREFIX}/biometrics", tags=["Biometrics"])
app.include_router(cache_router, prefix=f"{API_V1_PREFIX}/cache", tags=["Cache"])
```

## Version History
- v1.0: Initial TDD
- v2.0: Complete implementation with approval chains, behavioral biometrics, unified service accounts, ML infrastructure, cache factory pattern