# Industry Terminology Mapping - Implementation Plan

**Version**: 1.0  
**Date**: 2025-08-09  
**Status**: Active Development

---

## 🎯 Project Overview

### Goal
Enable Sentinel RBAC platform to serve multiple industries with domain-specific terminology while maintaining complete API consistency and zero breaking changes.

### Key Principles
1. **Zero Breaking Changes**: All existing APIs continue to work unchanged
2. **Display-Layer Only**: Terminology affects UI labels only, not data structures
3. **Inheritance-Based**: Child tenants automatically inherit parent terminology
4. **Performance Optimized**: Minimal overhead for terminology lookups
5. **UX Enhancement**: Extend existing admin screens rather than building new ones

### Example Transformation
```
Maritime Industry View:
- "Create Maritime Authority" (instead of "Create Tenant")
- "Port Organization" (instead of "Sub-Tenant")
- "Stakeholder Management" (instead of "User Management")
- "Service Clearance" (instead of "Permission")

Healthcare Industry View:
- "Create Health System" (instead of "Create Tenant")  
- "Hospital" (instead of "Sub-Tenant")
- "Healthcare Professional Management" (instead of "User Management")
- "Clinical Access" (instead of "Permission")
```

---

## 🏗️ Technical Architecture

### Current Schema Analysis
**Tenant Model** (`src/models/tenant.py:32`):
```python
settings = Column(JSON, default=dict)  # ✅ Can store terminology_config
```

**Assessment**: No database migration needed - use existing `settings` JSON field.

### Terminology Configuration Schema
```json
{
  "settings": {
    "terminology_config": {
      "tenant": "Maritime Authority",
      "sub_tenant": "Port Organization", 
      "user": "Stakeholder",
      "role": "Stakeholder Type",
      "permission": "Service Clearance",
      "resource": "Maritime Service",
      "group": "Stakeholder Group",
      "create_tenant": "Register Maritime Organization",
      "tenant_management": "Maritime Authority Management",
      "user_management": "Stakeholder Management"
    },
    "terminology_inherited": true,
    "terminology_last_updated": "2025-08-09T10:00:00Z"
  }
}
```

### Inheritance Logic
```python
class Tenant(BaseModel):
    def get_effective_terminology(self):
        """Get terminology with inheritance from parent"""
        config = self.settings.get("terminology_config", {})
        
        # If no local config and has parent, inherit from parent
        if not config and self.parent:
            parent_config = self.parent.get_effective_terminology()
            return parent_config
            
        # If partial config, merge with parent
        if self.parent and config.get("inherit_parent", True):
            parent_config = self.parent.get_effective_terminology()
            merged_config = parent_config.copy()
            merged_config.update(config)
            return merged_config
            
        return config or self._get_default_terminology()
```

---

## 📡 API Design

### New Endpoints

#### 1. Get Tenant Terminology
```
GET /api/v1/tenants/{tenant_id}/terminology
```

**Response**:
```json
{
  "tenant_id": "uuid",
  "terminology": {
    "tenant": "Maritime Authority",
    "sub_tenant": "Port Organization",
    // ... other terms
  },
  "inherited_from": "parent_tenant_id",  // null if not inherited
  "is_inherited": true,
  "last_updated": "2025-08-09T10:00:00Z"
}
```

#### 2. Update Tenant Terminology
```
PUT /api/v1/tenants/{tenant_id}/terminology
```

**Request**:
```json
{
  "terminology": {
    "tenant": "Maritime Authority",
    "sub_tenant": "Port Organization"
  },
  "inherit_parent": false,  // Optional, default true
  "apply_to_children": true  // Optional, default false
}
```

#### 3. Reset Terminology
```
DELETE /api/v1/tenants/{tenant_id}/terminology
```
Resets to parent inheritance or default terminology.

### Enhanced Existing Endpoints

#### Update Tenant PATCH Endpoint
Add terminology support to existing `PATCH /api/v1/tenants/{tenant_id}`:

```json
{
  "name": "Updated Tenant Name",
  "settings": {
    "terminology_config": {
      "tenant": "Custom Term"
    }
  }
}
```

---

## 🔧 Service Layer Architecture

### TerminologyService
```python
class TerminologyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = {}  # In-memory cache for performance
    
    async def get_terminology(self, tenant_id: UUID) -> Dict[str, str]:
        """Get effective terminology for tenant with caching"""
        
    async def update_terminology(self, tenant_id: UUID, terminology: Dict[str, str]) -> None:
        """Update tenant terminology and invalidate cache"""
        
    async def reset_terminology(self, tenant_id: UUID) -> None:
        """Reset to parent inheritance"""
        
    async def apply_to_children(self, tenant_id: UUID, terminology: Dict[str, str]) -> None:
        """Apply terminology to all child tenants"""
```

### Performance Optimization
- **In-memory caching** of terminology configurations
- **Lazy loading** - fetch only when needed
- **Cache invalidation** on terminology updates
- **Batch operations** for applying to multiple children

---

## 🎨 Frontend Integration

### Terminology Service (Frontend)
```typescript
class TerminologyService {
  private cache: Map<string, TerminologyConfig> = new Map();
  
  async getTerm(tenantId: string, key: string): Promise<string> {
    const config = await this.getTerminology(tenantId);
    return config[key] || this.getDefaultTerm(key);
  }
  
  async getTerminology(tenantId: string): Promise<TerminologyConfig> {
    if (!this.cache.has(tenantId)) {
      const response = await fetch(`/api/v1/tenants/${tenantId}/terminology`);
      const config = await response.json();
      this.cache.set(tenantId, config.terminology);
    }
    return this.cache.get(tenantId)!;
  }
  
  invalidateCache(tenantId: string): void {
    this.cache.delete(tenantId);
  }
}
```

### Dynamic Label Usage
```tsx
const TenantManagementPage = () => {
  const { terminology } = useTerminology();
  
  return (
    <div>
      <h1>{terminology.tenant_management || "Tenant Management"}</h1>
      <button>
        {terminology.create_tenant || "Create Tenant"}
      </button>
      
      <table>
        <thead>
          <tr>
            <th>{terminology.tenant_name || "Name"}</th>
            <th>{terminology.tenant_type || "Type"}</th>
          </tr>
        </thead>
      </table>
    </div>
  );
};
```

---

## 🧪 Testing Strategy

### Unit Tests

#### Terminology Inheritance
```python
class TestTerminologyInheritance:
    async def test_child_inherits_parent_terminology(self):
        """Test that child tenants inherit parent terminology"""
        
    async def test_child_overrides_parent_terminology(self):
        """Test that child can override specific parent terms"""
        
    async def test_multilevel_inheritance(self):
        """Test inheritance through 4+ levels of tenants"""
```

#### API Endpoint Tests
```python
class TestTerminologyAPI:
    async def test_get_terminology_returns_effective_config(self):
        """Test GET /tenants/{id}/terminology"""
        
    async def test_update_terminology_saves_and_invalidates_cache(self):
        """Test PUT /tenants/{id}/terminology"""
        
    async def test_reset_terminology_reverts_to_inheritance(self):
        """Test DELETE /tenants/{id}/terminology"""
```

### Integration Tests

#### Full Workflow Tests  
```python
class TestTerminologyWorkflow:
    async def test_complete_maritime_terminology_setup(self):
        """Test setting up maritime terminology for full hierarchy"""
        # 1. Create platform tenant
        # 2. Create maritime root tenant with terminology
        # 3. Create organization sub-tenant (should inherit)
        # 4. Create branch sub-sub-tenant (should inherit)
        # 5. Verify terminology at each level
```

### Performance Tests
- **Cache Performance**: Measure terminology lookup overhead
- **Memory Usage**: Monitor cache memory consumption
- **Response Times**: Ensure < 50ms additional overhead
- **Concurrent Access**: Test cache thread-safety

---

## 🔄 Migration & Rollback Strategy

### Migration Plan
1. **Phase 1**: Deploy backend changes (no impact - additive only)
2. **Phase 2**: Deploy frontend changes with feature flag disabled
3. **Phase 3**: Enable feature flag for testing tenant
4. **Phase 4**: Gradual rollout to production tenants

### Rollback Strategy
- **Feature flag** can disable terminology system instantly
- **Database rollback**: Remove terminology_config from settings (non-destructive)
- **Cache clearing**: Terminology cache can be cleared without system restart

### Backwards Compatibility
- All existing APIs continue to work unchanged
- Default terminology matches current labels
- No changes to existing data structures

---

## 📊 Success Metrics

### Technical Metrics
- **API Response Time**: < 50ms additional overhead
- **Memory Usage**: < 10MB terminology cache per tenant
- **Cache Hit Rate**: > 95% for terminology lookups
- **Test Coverage**: > 90% for terminology features

### Business Metrics
- **User Adoption**: Terminology usage across tenant types
- **Support Reduction**: Fewer terminology-related support requests
- **Time to Setup**: Reduced tenant onboarding time with familiar terms

---

## 🗓️ Implementation Timeline

### Phase 1: Database & Backend (3-4 days)
- Extend Tenant model with terminology methods
- Implement inheritance logic
- Create terminology service layer

### Phase 2: API Development (3-4 days)
- Build terminology CRUD endpoints
- Enhance existing tenant endpoints
- Add comprehensive validation

### Phase 3: Testing & Validation (4-5 days)
- Unit tests for all terminology features
- Integration tests for API workflows
- Performance and regression testing

### Phase 4: Admin UX Enhancement (5-6 days)
- Analyze existing admin screens
- Add terminology configuration to tenant forms
- Create terminology management interfaces

### Phase 5: Frontend Integration (4-5 days)
- Build terminology service and caching
- Update components to use dynamic labels
- Test across existing admin screens

### Phase 6: API-to-UX Analysis (4-5 days)
- Complete audit of admin screens and APIs
- Document terminology integration requirements
- Create guide for new application development

**Total: 23-29 days**

---

## 🚧 Risk Mitigation

### Technical Risks
| Risk | Impact | Likelihood | Mitigation |
|------|---------|------------|------------|
| Performance degradation | High | Low | Comprehensive caching + performance testing |
| Cache memory issues | Medium | Medium | LRU cache with size limits |
| Inheritance complexity | Medium | Medium | Thorough unit testing of edge cases |

### Business Risks
| Risk | Impact | Likelihood | Mitigation |
|------|---------|------------|------------|
| User confusion | High | Low | Maintain familiar defaults + gradual rollout |
| Admin overhead | Medium | Medium | Simple configuration interfaces |
| Support burden | Medium | Low | Comprehensive documentation |

---

*Last Updated: 2025-08-09*