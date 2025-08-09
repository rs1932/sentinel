# 🔧 Sentinel Technical Integration Guide

**Complete technical documentation for integrating applications with Sentinel RBAC**

---

## 🏗️ Architecture Overview

### **High-Level Integration Pattern**

```mermaid
graph TB
    User[👤 User] --> App[🎯 Your Application]
    App --> Auth[🔐 Authentication Check]
    Auth --> Sentinel[🛡️ Sentinel Platform]
    Sentinel --> Permissions[📋 User Permissions]
    Permissions --> Menu[🧭 Dynamic Menus]
    Menu --> App
    App --> UI[🎨 Personalized UI]
    UI --> User

    subgraph "Your Application"
        App
        Auth
        UI
    end

    subgraph "Sentinel Platform"
        Sentinel
        Permissions
        Menu
        DB[(🗄️ RBAC Database)]
        Sentinel --> DB
    end
```

### **Integration Layers**

| Layer | Responsibility | Your Code | Sentinel |
|-------|---------------|-----------|----------|
| **Authentication** | User identity verification | Login UI/flow | JWT token validation |
| **Authorization** | Permission checking | API calls to Sentinel | Permission resolution |
| **Menu Generation** | Dynamic navigation | Render menus from API | Menu structure + permissions |
| **Field-Level Control** | Show/hide UI elements | UI logic based on permissions | Field visibility rules |
| **Audit Logging** | Track user actions | Send action logs | Store audit trails |

---

## 🔌 Core Integration APIs

### **1. Authentication Flow**

#### **Step 1: User Login**
```bash
# User login to get JWT token
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "john@acme.com",
  "password": "secure_password",
  "tenant_id": "acme-corp-uuid"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "user-uuid",
    "email": "john@acme.com",
    "tenant_id": "acme-corp-uuid",
    "roles": ["hr-manager"],
    "groups": ["hr-department"]
  }
}
```

#### **Step 2: Token Validation**
```bash
# Validate token on each request
GET /api/v1/auth/verify
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### **2. Permission Checking**

#### **Check User Permissions**
```bash
# Get all permissions for a user
GET /api/v1/permissions/evaluate?user_id=user-uuid&resource_type=API
Authorization: Bearer {token}
```

**Response:**
```json
{
  "user_id": "user-uuid",
  "permissions": [
    {
      "resource_id": "customer-data",
      "resource_type": "API",
      "actions": ["READ", "UPDATE"],
      "conditions": {
        "department": "HR",
        "time_restricted": false
      },
      "field_permissions": {
        "customer.salary": "DENIED",
        "customer.name": "ALLOWED",
        "customer.department": "ALLOWED"
      }
    }
  ]
}
```

#### **Check Specific Resource Access**
```bash
# Check if user can perform specific action
POST /api/v1/permissions/check
Authorization: Bearer {token}

{
  "user_id": "user-uuid",
  "resource_id": "customer-data",
  "action": "UPDATE",
  "context": {
    "customer_department": "HR",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### **3. Dynamic Menu Generation**

#### **Get User's Personalized Menu**
```bash
# Get menu structure based on user permissions
GET /api/v1/navigation/menu/{user-id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "menu_items": [
    {
      "id": "dashboard",
      "name": "dashboard",
      "display_name": "Dashboard",
      "icon": "dashboard",
      "url": "/dashboard",
      "order_index": 1,
      "visible": true,
      "children": []
    },
    {
      "id": "hr-section",
      "name": "hr-management",
      "display_name": "HR Management",
      "icon": "people",
      "url": "/hr",
      "order_index": 2,
      "visible": true,
      "children": [
        {
          "id": "employees",
          "display_name": "Employee Records",
          "url": "/hr/employees",
          "permissions_required": ["hr-data:READ"]
        }
      ]
    }
  ]
}
```

---

## 💻 Implementation Patterns

### **Pattern 1: Permission Middleware** ⭐ **Recommended**

Create middleware that checks permissions before handling requests:

```python
# Python/FastAPI Example
from functools import wraps
import requests

def require_permission(resource: str, action: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from JWT token
            user_id = get_current_user_id()
            
            # Check permission with Sentinel
            response = requests.post(
                f"{SENTINEL_BASE_URL}/api/v1/permissions/check",
                headers={"Authorization": f"Bearer {jwt_token}"},
                json={
                    "user_id": user_id,
                    "resource_id": resource,
                    "action": action,
                    "context": get_request_context()
                }
            )
            
            if response.status_code == 200 and response.json().get("allowed"):
                return await func(*args, **kwargs)
            else:
                raise PermissionDenied("Access denied")
                
        return wrapper
    return decorator

# Usage
@app.get("/api/customers")
@require_permission("customer-data", "READ")
async def get_customers():
    return fetch_customers()
```

```javascript
// JavaScript/Node.js Example
const checkPermission = (resource, action) => {
  return async (req, res, next) => {
    try {
      const response = await fetch(`${SENTINEL_BASE_URL}/api/v1/permissions/check`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${req.jwt}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: req.user.id,
          resource_id: resource,
          action: action,
          context: {
            ip_address: req.ip,
            timestamp: new Date().toISOString()
          }
        })
      });
      
      const result = await response.json();
      if (result.allowed) {
        next();
      } else {
        res.status(403).json({ error: 'Permission denied' });
      }
    } catch (error) {
      res.status(500).json({ error: 'Authorization service unavailable' });
    }
  };
};

// Usage
app.get('/api/customers', 
  checkPermission('customer-data', 'READ'),
  (req, res) => {
    res.json(getCustomers());
  }
);
```

### **Pattern 2: Permission-Aware UI Components**

Create UI components that automatically hide/show based on permissions:

```jsx
// React Example
import { usePermissions } from './hooks/usePermissions';

const PermissionGate = ({ resource, action, children, fallback = null }) => {
  const { checkPermission, loading } = usePermissions();
  
  if (loading) return <div>Loading...</div>;
  
  const hasPermission = checkPermission(resource, action);
  return hasPermission ? children : fallback;
};

// Usage
<PermissionGate resource="customer-data" action="UPDATE">
  <EditCustomerButton />
</PermissionGate>

<PermissionGate resource="financial-reports" action="READ" 
               fallback={<div>Access Denied</div>}>
  <FinancialDashboard />
</PermissionGate>
```

### **Pattern 3: Field-Level Permission Control**

Implement granular field visibility:

```python
# Python Example
def filter_fields_by_permissions(data: dict, user_permissions: dict) -> dict:
    """Filter data fields based on user permissions."""
    filtered_data = {}
    
    for field, value in data.items():
        field_permission = user_permissions.get("field_permissions", {}).get(field)
        
        if field_permission == "ALLOWED":
            filtered_data[field] = value
        elif field_permission == "MASKED":
            filtered_data[field] = "***"
        # DENIED fields are not included
    
    return filtered_data

# Usage
@app.get("/api/customers/{customer_id}")
@require_permission("customer-data", "READ")
async def get_customer(customer_id: str):
    customer = fetch_customer(customer_id)
    user_permissions = get_user_permissions()
    
    return filter_fields_by_permissions(customer, user_permissions)
```

---

## 🔄 Integration Workflows

### **User Session Flow**

```mermaid
sequenceDiagram
    participant User
    participant App
    participant Sentinel
    
    User->>App: 1. Login Request
    App->>Sentinel: 2. Authenticate User
    Sentinel-->>App: 3. JWT Token + User Info
    
    App->>Sentinel: 4. Get User Menu
    Sentinel-->>App: 5. Personalized Menu Structure
    
    App-->>User: 6. Application UI with Menu
    
    User->>App: 7. Access Protected Resource
    App->>Sentinel: 8. Check Permission
    Sentinel-->>App: 9. Permission Result
    
    alt Permission Granted
        App-->>User: 10a. Show Resource
    else Permission Denied
        App-->>User: 10b. Access Denied
    end
```

### **Real-Time Permission Updates**

For applications requiring real-time permission updates:

```javascript
// WebSocket connection for real-time updates
const permissionSocket = new WebSocket(`${SENTINEL_WS_URL}/permissions/${userId}`);

permissionSocket.onmessage = (event) => {
  const update = JSON.parse(event.data);
  
  switch (update.type) {
    case 'PERMISSION_GRANTED':
      // Show newly accessible features
      showFeature(update.resource);
      break;
      
    case 'PERMISSION_REVOKED':
      // Hide features user can no longer access
      hideFeature(update.resource);
      break;
      
    case 'MENU_UPDATED':
      // Refresh user menu
      refreshUserMenu();
      break;
  }
};
```

---

## 🛠️ SDK and Helper Libraries

### **Sentinel Client SDK** (Recommended)

```bash
# Install SDK
npm install @sentinel/client-sdk
# or
pip install sentinel-client-sdk
```

```javascript
// JavaScript SDK Usage
import { SentinelClient } from '@sentinel/client-sdk';

const sentinel = new SentinelClient({
  baseUrl: 'https://sentinel.yourcompany.com',
  apiKey: 'your-api-key'
});

// Check permission
const canEdit = await sentinel.checkPermission({
  userId: 'user-123',
  resource: 'customer-data',
  action: 'UPDATE'
});

// Get user menu
const menu = await sentinel.getUserMenu('user-123');
```

```python
# Python SDK Usage
from sentinel_client import SentinelClient

sentinel = SentinelClient(
    base_url="https://sentinel.yourcompany.com",
    api_key="your-api-key"
)

# Check permission
can_edit = sentinel.check_permission(
    user_id="user-123",
    resource="customer-data", 
    action="UPDATE"
)

# Get user menu
menu = sentinel.get_user_menu("user-123")
```

---

## ⚡ Performance Optimization & Caching Strategies

### **🎯 Recommended Approach: Smart Hybrid Caching**

Based on real-world usage patterns, we recommend a **three-tier caching strategy** that balances security with performance:

#### **Tier 1: Aggressive Caching (5 minutes) - Navigation & UI**
- **Use Case**: Menu rendering, UI component visibility
- **Risk Level**: Low (UI elements)
- **Cache TTL**: 5 minutes
- **API Calls**: ~95% reduction

#### **Tier 2: Balanced Caching (2 minutes) - Data Operations**
- **Use Case**: Read operations, data filtering  
- **Risk Level**: Medium (data access)
- **Cache TTL**: 2 minutes
- **API Calls**: ~85% reduction

#### **Tier 3: Real-Time Validation - Critical Operations**
- **Use Case**: Create, update, delete operations
- **Risk Level**: High (data modification)
- **Cache TTL**: Always validate
- **API Calls**: 0% reduction (always check)

### **1. Advanced Permission Caching Service**

```python
# app/services/smart_permission_cache.py
import asyncio
import time
from typing import Dict, Set, Optional
from enum import Enum
from dataclasses import dataclass
import aioredis
import json

class CacheStrategy(Enum):
    AGGRESSIVE = "aggressive"  # 5 min cache, UI elements
    BALANCED = "balanced"      # 2 min cache, data operations  
    REAL_TIME = "real_time"    # Always validate, critical ops

@dataclass
class CachedPermissions:
    user_id: str
    permissions: Set[str]
    hierarchical_access: Dict[str, bool]
    field_permissions: Dict[str, Dict[str, str]]
    expires_at: float
    cache_strategy: CacheStrategy

class SmartPermissionCache:
    def __init__(self):
        self.local_cache: Dict[str, CachedPermissions] = {}
        self.redis_client = None
        self.sentinel_base = "http://localhost:8000"
        
        # TTL configuration by strategy
        self.cache_ttl = {
            CacheStrategy.AGGRESSIVE: 300,   # 5 minutes - UI/Navigation
            CacheStrategy.BALANCED: 120,     # 2 minutes - Data reads
            CacheStrategy.REAL_TIME: 0       # No cache - Critical operations
        }
    
    async def initialize_redis(self):
        """Initialize Redis connection for distributed caching"""
        try:
            self.redis_client = await aioredis.from_url("redis://localhost:6379")
        except Exception:
            print("Redis not available, using local cache only")
    
    async def get_permissions(
        self, 
        user_id: str, 
        token: str, 
        strategy: CacheStrategy = CacheStrategy.BALANCED
    ) -> CachedPermissions:
        """Get user permissions with strategy-based caching"""
        
        # For real-time strategy, always fetch fresh
        if strategy == CacheStrategy.REAL_TIME:
            return await self._fetch_fresh_permissions(user_id, token, strategy)
        
        # Check local cache first
        cached = self.local_cache.get(user_id)
        if cached and time.time() < cached.expires_at:
            return cached
        
        # Check Redis cache if available
        if self.redis_client:
            redis_cached = await self._get_from_redis(user_id)
            if redis_cached and time.time() < redis_cached.expires_at:
                self.local_cache[user_id] = redis_cached
                return redis_cached
        
        # Fetch fresh permissions
        fresh_permissions = await self._fetch_fresh_permissions(user_id, token, strategy)
        
        # Cache locally and in Redis
        self.local_cache[user_id] = fresh_permissions
        if self.redis_client:
            await self._store_in_redis(fresh_permissions)
            
        return fresh_permissions
    
    async def _fetch_fresh_permissions(
        self, 
        user_id: str, 
        token: str, 
        strategy: CacheStrategy
    ) -> CachedPermissions:
        """Fetch comprehensive permissions from Sentinel with single API call"""
        
        import httpx
        async with httpx.AsyncClient() as client:
            # Single batch API call for all permission data
            response = await client.post(
                f"{self.sentinel_base}/api/v1/permissions/comprehensive-check",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "user_id": user_id,
                    "include_hierarchical": True,
                    "include_field_permissions": True,
                    "include_menu_permissions": True
                },
                timeout=5.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Permission fetch failed: {response.status_code}")
            
            data = response.json()
            
            # Process into structured format
            permissions = set(data.get("permissions", []))
            hierarchical_access = data.get("hierarchical_access", {})
            field_permissions = data.get("field_permissions", {})
            
            ttl = self.cache_ttl[strategy]
            expires_at = time.time() + ttl if ttl > 0 else 0
            
            return CachedPermissions(
                user_id=user_id,
                permissions=permissions,
                hierarchical_access=hierarchical_access,
                field_permissions=field_permissions,
                expires_at=expires_at,
                cache_strategy=strategy
            )
    
    async def check_permission(
        self, 
        user_id: str, 
        token: str,
        resource: str, 
        action: str,
        operation_type: str = "read"
    ) -> bool:
        """Check permission with automatic strategy selection"""
        
        # Automatically select cache strategy based on operation
        strategy_map = {
            "ui": CacheStrategy.AGGRESSIVE,      # Menu/navigation rendering
            "read": CacheStrategy.BALANCED,      # Data fetching
            "create": CacheStrategy.REAL_TIME,   # Data creation
            "update": CacheStrategy.REAL_TIME,   # Data modification  
            "delete": CacheStrategy.REAL_TIME,   # Data deletion
            "admin": CacheStrategy.REAL_TIME     # Administrative operations
        }
        
        strategy = strategy_map.get(operation_type, CacheStrategy.BALANCED)
        
        permissions = await self.get_permissions(user_id, token, strategy)
        permission_key = f"{resource}:{action}"
        
        return permission_key in permissions.permissions
    
    async def check_hierarchical_access(
        self,
        user_id: str,
        token: str, 
        path: str,
        operation_type: str = "read"
    ) -> bool:
        """Check hierarchical access path: 'pcs-system->msw-module->vessel-management'"""
        
        strategy_map = {
            "ui": CacheStrategy.AGGRESSIVE,
            "read": CacheStrategy.BALANCED, 
            "create": CacheStrategy.REAL_TIME,
            "update": CacheStrategy.REAL_TIME,
            "delete": CacheStrategy.REAL_TIME
        }
        
        strategy = strategy_map.get(operation_type, CacheStrategy.BALANCED)
        permissions = await self.get_permissions(user_id, token, strategy)
        
        # Parse hierarchical path
        levels = path.split('->')
        for level in levels:
            key = level if ':' in level else f"{level}:ACCESS"
            if not permissions.hierarchical_access.get(key, False):
                return False
        
        return True
    
    def invalidate_user(self, user_id: str):
        """Invalidate all cached data for a user"""
        if user_id in self.local_cache:
            del self.local_cache[user_id]
        
        # Also invalidate Redis cache
        if self.redis_client:
            asyncio.create_task(self._invalidate_redis(user_id))

# Global cache instance
smart_cache = SmartPermissionCache()
```

### **2. Optimized FastAPI Middleware**

```python
# app/middleware/optimized_auth.py
from fastapi import Request, HTTPException, Depends
from app.services.smart_permission_cache import smart_cache

class OptimizedAuthMiddleware:
    def __init__(self):
        self.cache = smart_cache
    
    async def require_access(
        self,
        hierarchical_path: str,
        operation_type: str = "read"
    ):
        """Optimized permission check with automatic caching strategy"""
        async def check_access(request: Request):
            token = self._extract_token(request)
            user_id = self._get_user_id(token)
            
            # Smart caching based on operation type
            has_access = await self.cache.check_hierarchical_access(
                user_id=user_id,
                token=token,
                path=hierarchical_path,
                operation_type=operation_type
            )
            
            if not has_access:
                raise HTTPException(403, f"Access denied to {hierarchical_path}")
            
            return {"user_id": user_id, "token": token}
        
        return check_access

# Usage examples with automatic cache strategy selection
auth = OptimizedAuthMiddleware()

# UI operations - uses 5-minute aggressive cache
@app.get("/api/navigation")
async def get_navigation(user: dict = Depends(auth.require_access("pcs-system", "ui"))):
    # Navigation rendering - cached for 5 minutes
    pass

# Read operations - uses 2-minute balanced cache  
@app.get("/api/vessel-registration/")
async def list_vessels(user: dict = Depends(auth.require_access("pcs-system->msw-module->vessel-management->vessel-registration-api:READ", "read"))):
    # Data reads - cached for 2 minutes
    pass

# Create operations - always validates in real-time
@app.post("/api/vessel-registration/")
async def create_vessel(user: dict = Depends(auth.require_access("pcs-system->msw-module->vessel-management->vessel-registration-api:CREATE", "create"))):
    # Critical operations - always real-time validation
    pass
```

### **3. Frontend Zustand Store with Smart Caching**

```javascript
// frontend/src/stores/optimizedPermissionStore.js
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useOptimizedPermissionStore = create(
  persist(
    (set, get) => ({
      // State with cache strategies
      permissions: new Set(),
      hierarchicalAccess: {},
      fieldPermissions: {},
      cacheMetadata: {
        ui: { expires: null, strategy: 'aggressive' },
        read: { expires: null, strategy: 'balanced' }, 
        write: { expires: null, strategy: 'realtime' }
      },
      
      // Smart cache check
      isCacheValid: (operation_type = 'read') => {
        const { cacheMetadata } = get();
        const metadata = cacheMetadata[operation_type];
        
        if (metadata.strategy === 'realtime') return false;
        return metadata.expires && Date.now() < metadata.expires;
      },
      
      // Optimized permission check
      canAccess: async (path, operation_type = 'read') => {
        const { hierarchicalAccess, isCacheValid } = get();
        
        // For real-time operations, always check with server
        if (operation_type === 'create' || operation_type === 'update' || operation_type === 'delete') {
          return await get().checkWithSentinel(path, operation_type);
        }
        
        // Use cache for UI and read operations
        if (isCacheValid(operation_type)) {
          return get().checkLocalCache(path);
        }
        
        // Cache expired, refresh for this operation type
        return await get().refreshAndCheck(path, operation_type);
      },
      
      checkLocalCache: (path) => {
        const { hierarchicalAccess } = get();
        const levels = path.split('->');
        
        for (const level of levels) {
          const key = level.includes(':') ? level : `${level}:ACCESS`;
          if (!hierarchicalAccess[key]) return false;
        }
        return true;
      },
      
      // Batch permission loading on login
      loadUserPermissions: async (token) => {
        try {
          const response = await fetch('http://localhost:8000/api/v1/permissions/comprehensive-check', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              user_id: get().getUserId(token),
              include_hierarchical: true,
              include_field_permissions: true,
              include_menu_permissions: true
            })
          });
          
          if (response.ok) {
            const data = await response.json();
            const now = Date.now();
            
            set({
              permissions: new Set(data.permissions),
              hierarchicalAccess: data.hierarchical_access,
              fieldPermissions: data.field_permissions,
              cacheMetadata: {
                ui: { expires: now + (5 * 60 * 1000), strategy: 'aggressive' },      // 5 min
                read: { expires: now + (2 * 60 * 1000), strategy: 'balanced' },      // 2 min
                write: { expires: now, strategy: 'realtime' }                        // No cache
              }
            });
          }
        } catch (error) {
          console.error('Failed to load permissions:', error);
        }
      },
      
      // Real-time permission updates via WebSocket
      handlePermissionUpdate: (update) => {
        switch (update.type) {
          case 'PERMISSION_REVOKED':
            // Immediately invalidate all caches
            set({
              cacheMetadata: {
                ui: { expires: 0, strategy: 'aggressive' },
                read: { expires: 0, strategy: 'balanced' },
                write: { expires: 0, strategy: 'realtime' }
              }
            });
            
            // Hide affected UI elements immediately
            get().updateUIVisibility(update.revokedPermissions);
            break;
            
          case 'PERMISSION_GRANTED':
            // Force refresh to get new permissions
            get().loadUserPermissions(update.token);
            break;
        }
      }
    }),
    {
      name: 'optimized-permissions',
      // Persist cache expiry times
      partialize: (state) => ({
        cacheMetadata: state.cacheMetadata
      })
    }
  )
);

export default useOptimizedPermissionStore;
```

### **4. Performance Monitoring & Metrics**

```python
# app/middleware/performance_monitor.py
import time
from prometheus_client import Counter, Histogram
from functools import wraps

# Metrics
permission_checks = Counter(
    'sentinel_permission_checks_total',
    'Total permission checks', 
    ['resource', 'action', 'result', 'cache_hit']
)

permission_latency = Histogram(
    'sentinel_permission_check_duration_seconds',
    'Permission check duration'
)

cache_hits = Counter(
    'sentinel_cache_hits_total',
    'Cache hits by strategy',
    ['strategy', 'operation_type']
)

def monitor_performance(operation_type: str = "read"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            cache_hit = False
            result = "denied"
            
            try:
                # Call the actual permission check
                allowed = await func(*args, **kwargs)
                result = "allowed" if allowed else "denied"
                
                # Detect if this was a cache hit (response < 10ms = likely cached)
                cache_hit = (time.time() - start_time) < 0.01
                
                return allowed
            finally:
                # Record metrics
                duration = time.time() - start_time
                permission_latency.observe(duration)
                
                permission_checks.labels(
                    resource=kwargs.get('resource', 'unknown'),
                    action=kwargs.get('action', 'unknown'), 
                    result=result,
                    cache_hit=str(cache_hit)
                ).inc()
                
                if cache_hit:
                    cache_hits.labels(
                        strategy="cached",
                        operation_type=operation_type
                    ).inc()
        
        return wrapper
    return decorator

# Usage
@monitor_performance("read")
async def check_vessel_access(user_id, token, resource, action):
    return await smart_cache.check_permission(user_id, token, resource, action, "read")
```

---

## 🔒 Security Best Practices

### **1. Token Management**

```javascript
// Secure token storage and refresh
class TokenManager {
  constructor() {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }
  
  async refreshAccessToken() {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.refreshToken}` }
    });
    
    if (response.ok) {
      const tokens = await response.json();
      this.accessToken = tokens.access_token;
      localStorage.setItem('access_token', tokens.access_token);
    } else {
      // Redirect to login
      window.location.href = '/login';
    }
  }
}
```

### **2. Request Context**

Always include relevant context when checking permissions:

```python
def get_permission_context(request):
    """Generate context for permission checks."""
    return {
        "ip_address": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": request.session.get("session_id"),
        "department": request.user.department,
        "location": request.headers.get("X-User-Location")
    }
```

### **3. Error Handling**

```python
class PermissionService:
    def __init__(self):
        self.sentinel_client = SentinelClient()
    
    def check_permission(self, user_id, resource, action, context=None):
        try:
            result = self.sentinel_client.check_permission(
                user_id=user_id,
                resource=resource,
                action=action,
                context=context or {}
            )
            return result.get("allowed", False)
            
        except ConnectionError:
            # Fail secure - deny access if Sentinel is unavailable
            logger.error(f"Sentinel unavailable for permission check: {user_id}, {resource}, {action}")
            return False
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
```

---

## 📊 Monitoring & Observability

### **Integration Health Checks**

```python
@app.get("/health/sentinel")
async def sentinel_health():
    """Check Sentinel service health."""
    try:
        response = requests.get(
            f"{SENTINEL_BASE_URL}/health",
            timeout=5
        )
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "response_time": response.elapsed.total_seconds(),
            "sentinel_version": response.headers.get("X-Sentinel-Version")
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### **Permission Check Metrics**

```python
import time
from prometheus_client import Counter, Histogram

permission_checks = Counter('sentinel_permission_checks_total', 
                          ['resource', 'action', 'result'])
permission_latency = Histogram('sentinel_permission_check_duration_seconds')

def monitored_permission_check(user_id, resource, action):
    start_time = time.time()
    try:
        result = sentinel.check_permission(user_id, resource, action)
        permission_checks.labels(resource=resource, action=action, 
                               result='allowed' if result else 'denied').inc()
        return result
    finally:
        permission_latency.observe(time.time() - start_time)
```

---

## 🚀 Next Steps

1. **Review** the [Setup Guide](./setup-guide.md) for tenant configuration
2. **Try** the [Developer Quickstart](./developer-quickstart.md) for hands-on implementation
3. **Implement** the recommended patterns for your technology stack
4. **Test** thoroughly with the provided examples
5. **Deploy** following the [Best Practices](./best-practices.md)

---

**Ready to start coding? Check out the [Developer Quickstart](./developer-quickstart.md)! 🚀**