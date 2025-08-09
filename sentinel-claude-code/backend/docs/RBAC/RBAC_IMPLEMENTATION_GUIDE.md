# Dynamic RBAC Implementation Guide

## Overview

This document describes the implementation of dynamic Role-Based Access Control (RBAC) in the Sentinel platform, replacing the previous hardcoded scope system with a flexible, database-driven permission resolution system.

## Architecture

### Previous System (Hardcoded Scopes)
```python
def _get_user_scopes(self, user: User) -> List[str]:
    if user.is_service_account:
        return ["api:read", "api:write", "tenant:admin", ...]
    elif is_super_admin:
        return ["platform:admin", "tenant:global", ...]
    else:
        return ["user:profile", "tenant:read", ...]
```

**Problems:**
- All users of same type get identical permissions
- No tenant-specific customization
- Cannot create granular roles like "HR Manager" or "Port Operations Supervisor"

### New System (Dynamic RBAC)
```python
async def _get_user_scopes(self, user: User) -> List[str]:
    if USE_DYNAMIC_RBAC:
        rbac_service = await self._get_rbac_service()
        return await rbac_service.get_user_scopes(user)
    else:
        # Fallback to hardcoded scopes
        return self._get_hardcoded_scopes(user)
```

**Benefits:**
- Database-driven permission resolution
- Tenant-specific role customization
- Group-based access control
- Role inheritance support
- Performance caching
- Graceful fallback to hardcoded system

## Implementation Components

### 1. RBACService (`src/services/rbac_service.py`)

Core service for dynamic permission resolution:

```python
class RBACService:
    async def get_user_scopes(self, user: User) -> List[str]
    async def get_user_direct_roles(self, user_id: UUID) -> List[Role]
    async def get_user_group_roles(self, user_id: UUID) -> List[Role]
    async def resolve_role_inheritance(self, roles: List[Role]) -> List[Role]
    async def invalidate_user_cache(self, user_id: UUID) -> None
```

**Features:**
- Caching with TTL (5 minutes default)
- Role inheritance resolution
- Group-based role assignments
- Performance monitoring
- Conflict resolution using role priority

### 2. Updated AuthenticationService

Modified to use dynamic RBAC with feature flag:

```python
# Feature flag (environment variable)
USE_DYNAMIC_RBAC = os.getenv("USE_DYNAMIC_RBAC", "true").lower() == "true"

async def _get_user_scopes(self, user: User) -> List[str]:
    if USE_DYNAMIC_RBAC:
        try:
            rbac_service = await self._get_rbac_service()
            return await rbac_service.get_user_scopes(user)
        except Exception as e:
            logger.error(f"Dynamic RBAC failed: {e}")
            # Graceful fallback
    
    # Original hardcoded logic as fallback
    return self._get_hardcoded_scopes(user)
```

### 3. Cache Manager (`src/core/cache.py`)

In-memory cache with TTL support:

```python
class InMemoryCacheManager:
    async def get(self, key: str) -> Optional[str]
    async def set(self, key: str, value: str, ttl: int = 300) -> None
    async def delete(self, key: str) -> None
```

**Features:**
- Background cleanup of expired entries
- TTL-based expiration
- Memory-efficient storage
- Ready for Redis upgrade

## Database Schema Integration

Uses existing Modules 4-7 models:

### Core Models
- **User**: Platform users with tenant isolation
- **Role**: Hierarchical roles with priority and inheritance
- **Group**: Departmental/organizational groups
- **Permission**: Granular resource-action permissions
- **Resource**: Hierarchical resources (Product Family > App > Capability > Service)

### Junction Tables
- **UserRole**: Direct user-role assignments
- **UserGroup**: User group memberships
- **GroupRole**: Group-role assignments
- **RolePermission**: Role-permission grants

### Permission Resolution Flow

1. **Direct Roles**: Query user's directly assigned roles
2. **Group Roles**: Query roles inherited through group membership
3. **Role Inheritance**: Resolve parent-child role relationships
4. **Permission Aggregation**: Collect all permissions from resolved roles
5. **Scope Generation**: Convert permissions to API scope strings
6. **Conflict Resolution**: Apply role priority for conflicts
7. **Caching**: Store results with TTL for performance

## Logistics Industry Test Data

### Tenants
- **Maritime Port Operations**: Port and vessel management
- **AirCargo Express**: Air freight and cargo handling  
- **GroundLink Logistics**: Warehousing and ground transportation

### Industry-Specific Roles

**Maritime Roles:**
- Port Manager (Priority 90): Full port operations access
- Vessel Coordinator (Priority 70): Vessel scheduling and berth assignment
- Customs Officer (Priority 80): Customs processing and compliance
- Terminal Supervisor (Priority 60): Terminal operations oversight
- Dock Worker (Priority 30): Basic cargo handling operations

**Air Cargo Roles:**
- Operations Manager (Priority 90): Complete air cargo oversight
- Flight Coordinator (Priority 75): Flight scheduling and manifests
- Security Inspector (Priority 80): Cargo security and screening
- Ground Services Coordinator (Priority 65): Ground support equipment
- Cargo Handler (Priority 40): Physical cargo operations

**Ground Logistics Roles:**
- Warehouse Manager (Priority 85): Warehouse operations management
- Logistics Coordinator (Priority 70): Transportation planning
- Fleet Manager (Priority 75): Vehicle fleet oversight
- Inventory Controller (Priority 60): Stock management
- Compliance Officer (Priority 80): Regulatory compliance

### Resource Hierarchy

```
Logistics Platform (Product Family)
├── Maritime Port Management System (App)
│   ├── Vessel Operations (Capability)
│   │   ├── Berth Assignment (Service)
│   │   ├── Cargo Manifest (Service)
│   │   └── Customs Processing (Service)
│   └── Terminal Management (Capability)
│       ├── Equipment Tracking (Service)
│       └── Worker Scheduling (Service)
├── Air Cargo System (App)
│   ├── Flight Operations (Capability)
│   │   ├── Cargo Loading (Service)
│   │   ├── Flight Planning (Service)
│   │   └── Security Screening (Service)
│   └── Ground Services (Capability)
│       ├── GSE Management (Service)
│       └── Fuel Services (Service)
└── Ground Operations (App)
    ├── Warehouse Management (Capability)
    │   ├── Inventory Tracking (Service)
    │   ├── Order Fulfillment (Service)
    │   └── Quality Control (Service)
    └── Fleet Management (Capability)
        ├── Vehicle Tracking (Service)
        └── Route Optimization (Service)
```

## Usage Examples

### Setting Up Dynamic RBAC

1. **Enable Feature Flag**:
   ```bash
   export USE_DYNAMIC_RBAC=true
   ```

2. **Run Database Cleanup** (preserves superadmin):
   ```bash
   python scripts/cleanup_database.py
   ```

3. **Seed Logistics Test Data**:
   ```bash
   python scripts/seed_logistics_industry.py
   ```

### Testing Scenarios

**Port Manager Full Access:**
```python
# Port Manager can create, read, update, delete berth assignments
scopes = await rbac_service.get_user_scopes(port_manager_user)
# Returns: ['service:create', 'service:read', 'service:update', 'service:delete', ...]
```

**Dock Worker Limited Access:**
```python
# Dock Worker gets read-only access through group membership
scopes = await rbac_service.get_user_scopes(dock_worker_user)  
# Returns: ['service:read']
```

**Cross-Tenant Isolation:**
```python
# Maritime user cannot access AirCargo resources
maritime_scopes = await rbac_service.get_user_scopes(maritime_user)
aircargo_scopes = await rbac_service.get_user_scopes(aircargo_user)
# No resource overlap between tenants
```

### API Integration

All existing API endpoints automatically use the new RBAC system:

```python
# Resource API with dynamic scopes
@router.get("/", dependencies=[Depends(require_scope("resource:read"))])
async def list_resources(current_user=Depends(get_current_user)):
    # current_user.scopes now resolved dynamically
    pass
```

### Performance Monitoring

```python
rbac_service = await RBACServiceFactory.create(db, use_cache=True)
stats = rbac_service.get_stats()
print(f"Cache hits: {stats['cache_hits']}")
print(f"Cache misses: {stats['cache_misses']}")  
print(f"DB queries: {stats['db_queries']}")
```

## Configuration

### Environment Variables

- `USE_DYNAMIC_RBAC`: Enable/disable dynamic RBAC (default: "true")
- `RBAC_CACHE_TTL`: Cache TTL in seconds (default: 300)
- `RBAC_ENABLE_INHERITANCE`: Enable role inheritance (default: "true")

### Feature Flags

**Production Deployment:**
```bash
# Enable dynamic RBAC gradually
USE_DYNAMIC_RBAC=true
RBAC_CACHE_TTL=600  # 10 minutes for production
```

**Rollback Safety:**
```bash
# Immediate rollback to hardcoded scopes
USE_DYNAMIC_RBAC=false
```

## Testing

### Unit Tests
- `tests/unit/test_rbac_service.py`: Core RBAC logic testing
- Mock-based testing with logistics scenarios
- Permission resolution, caching, inheritance

### Integration Tests
- `tests/integration/test_logistics_rbac_scenarios.py`: Full database integration
- Real logistics data scenarios
- Cross-tenant isolation verification
- Performance testing with caching

### API Tests
- `tests/api/test_rbac_api_scenarios.py`: API endpoint testing
- Authentication integration
- Scope-based access control
- Audit trail verification

### Running Tests

```bash
# Unit tests
pytest tests/unit/test_rbac_service.py -v

# Integration tests
pytest tests/integration/test_logistics_rbac_scenarios.py -v

# API tests  
pytest tests/api/test_rbac_api_scenarios.py -v

# All RBAC tests
pytest tests/ -k "rbac" -v
```

## Performance Considerations

### Caching Strategy
- **TTL**: 5 minutes default (configurable)
- **Invalidation**: User-specific and role-based cascading
- **Memory Usage**: Monitored with cleanup tasks
- **Hit Rate**: Tracked for optimization

### Database Optimization
- **Indexes**: Foreign keys and frequently queried columns
- **Query Patterns**: Optimized joins for role resolution
- **Connection Pooling**: Efficient database resource usage

### Monitoring Metrics
- Permission resolution time
- Cache hit/miss ratios
- Database query counts
- Memory usage patterns

## Migration Path

### Phase 1: Parallel Operation (Current)
- Dynamic RBAC enabled alongside hardcoded fallback
- Feature flag controls which system is used
- Full backward compatibility maintained

### Phase 2: Gradual Rollout
- Enable dynamic RBAC for specific tenants
- Monitor performance and correctness
- Gather user feedback and metrics

### Phase 3: Full Migration
- Dynamic RBAC becomes default
- Remove hardcoded scope logic
- Optimize for production workloads

### Phase 4: Advanced Features
- Redis caching integration
- Advanced permission evaluation
- Real-time permission updates
- Audit and compliance features

## Troubleshooting

### Common Issues

**Dynamic RBAC Not Working:**
```bash
# Check feature flag
echo $USE_DYNAMIC_RBAC

# Check logs for fallback messages
grep "Using hardcoded scopes" logs/app.log
```

**Performance Issues:**
```python
# Check RBAC service stats
stats = rbac_service.get_stats()
print(f"Avg resolution time: {stats['db_queries']/stats['permission_resolutions']}")
```

**Permission Denied Errors:**
```python
# Debug user permissions
details = await rbac_service.get_effective_permissions(user_id)
print(json.dumps(details, indent=2))
```

### Debug Commands

**User Permission Analysis:**
```bash
python -c "
import asyncio
from src.services.rbac_service import get_permission_details
from src.database import get_db_engine

async def debug_user(user_id):
    async with get_db_engine().connect() as db:
        details = await get_permission_details(db, user_id)
        print(json.dumps(details, indent=2))

asyncio.run(debug_user('user-uuid'))
"
```

**Cache Statistics:**
```python
# Monitor cache performance
rbac_service = await RBACServiceFactory.create(db)
stats = rbac_service.get_stats()
print(f"Cache efficiency: {stats['cache_hits']/(stats['cache_hits']+stats['cache_misses'])*100:.1f}%")
```

## Next Steps

1. **Production Deployment**: Deploy with feature flag enabled
2. **Monitoring Setup**: Implement metrics collection and alerting
3. **Performance Tuning**: Optimize cache settings and database queries
4. **Advanced Features**: Add Redis support, real-time updates
5. **UI Integration**: Admin interface for role/permission management

## Contributing

When modifying the RBAC system:

1. **Test Coverage**: Ensure comprehensive test coverage for changes
2. **Backward Compatibility**: Maintain fallback to hardcoded scopes
3. **Performance Impact**: Profile changes with realistic data volumes
4. **Documentation**: Update this guide and API documentation
5. **Security Review**: Review permission logic for potential bypasses