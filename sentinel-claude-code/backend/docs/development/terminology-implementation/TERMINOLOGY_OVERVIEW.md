# Industry Terminology Mapping System

## Executive Summary

The Sentinel RBAC platform includes a sophisticated terminology mapping system that allows organizations to customize system labels to match their industry-specific language. This enables seamless adoption across diverse industries by presenting familiar terminology to users while maintaining consistent underlying functionality.

## Core Concept

### The Problem
Different industries use vastly different terminology for similar organizational concepts:
- **Healthcare**: Departments, Divisions, Practitioners
- **Maritime**: Maritime Authorities, Port Organizations, Stakeholders  
- **Finance**: Branches, Subsidiaries, Account Managers
- **Technology**: Teams, Projects, Developers

Using generic terms like "Tenant" and "User" creates cognitive friction and requires extensive training.

### The Solution
Our terminology mapping system provides:
- **Dynamic label translation** throughout the entire application
- **Hierarchical inheritance** where child organizations inherit parent terminology
- **Industry templates** for quick setup
- **Zero breaking changes** to existing APIs and data structures

## Implementation Architecture

### Backend Implementation

#### 1. Database Design (Zero Migration Approach)
```python
# Uses existing tenant.settings JSON field
tenant.settings = {
    "terminology_config": {
        "tenant": "Maritime Authority",
        "user": "Stakeholder",
        "role": "Position Type"
    },
    "terminology_metadata": {
        "template_applied": "maritime",
        "last_updated": "2025-08-09T10:00:00Z"
    }
}
```

#### 2. Model Layer Enhancement
```python
# Tenant model methods
class Tenant(Base):
    def get_terminology(self) -> Dict[str, str]:
        """Get effective terminology with inheritance"""
        
    def set_terminology(self, terminology: Dict[str, str]):
        """Set local terminology configuration"""
        
    def inherit_terminology(self) -> Dict[str, str]:
        """Inherit terminology from parent tenant"""
```

#### 3. Service Layer
```python
class TerminologyService:
    async def get_terminology_for_tenant(tenant_id: str):
        """Get complete terminology with caching"""
        
    async def apply_industry_template(tenant_id: str, template: str):
        """Apply pre-configured industry template"""
        
    async def propagate_to_children(tenant_id: str):
        """Push terminology to child tenants"""
```

#### 4. REST API Endpoints
```
GET    /api/v1/terminology/tenants/{id}
PUT    /api/v1/terminology/tenants/{id}
POST   /api/v1/terminology/tenants/{id}/reset
POST   /api/v1/terminology/tenants/{id}/apply-to-children
GET    /api/v1/terminology/templates
POST   /api/v1/terminology/templates/{name}/apply
POST   /api/v1/terminology/validate
```

### Frontend Implementation

#### 1. Core Service
```typescript
class TerminologyService {
    private cache = new Map<string, TerminologyConfig>();
    
    async initialize(tenantId: string): Promise<void>
    translate(term: string): string
    updateTerminology(tenantId: string, config: UpdateRequest)
}
```

#### 2. React Integration
```tsx
// Simple translation hook
function MyComponent() {
    const t = useT();
    return <h1>{t('tenant_management')}</h1>;
}

// Full management hook
function AdminPanel() {
    const { terminology, updateTerminology } = useTerminology();
    // Full CRUD operations
}
```

#### 3. Context Provider System
```tsx
<TerminologyWrapper>
    <TerminologyProvider tenantId={currentTenant}>
        <App /> {/* All components have access to terminology */}
    </TerminologyProvider>
</TerminologyWrapper>
```

## Industry Template Examples

### Maritime Industry
```json
{
    "tenant": "Maritime Authority",
    "tenants": "Maritime Authorities",
    "sub_tenant": "Port Organization",
    "sub_tenants": "Port Organizations",
    "user": "Maritime Stakeholder",
    "users": "Maritime Stakeholders",
    "role": "Stakeholder Type",
    "roles": "Stakeholder Types",
    "permission": "Service Clearance",
    "permissions": "Service Clearances",
    "resource": "Maritime Service",
    "resources": "Maritime Services",
    "dashboard": "Operations Center",
    "tenant_management": "Maritime Authority Management",
    "user_management": "Stakeholder Management"
}
```

### Healthcare Industry
```json
{
    "tenant": "Healthcare Organization",
    "tenants": "Healthcare Organizations",
    "sub_tenant": "Department",
    "sub_tenants": "Departments",
    "user": "Healthcare Professional",
    "users": "Healthcare Professionals",
    "role": "Clinical Role",
    "roles": "Clinical Roles",
    "permission": "Access Privilege",
    "permissions": "Access Privileges",
    "resource": "Clinical System",
    "resources": "Clinical Systems",
    "dashboard": "Clinical Dashboard",
    "tenant_management": "Organization Management",
    "user_management": "Staff Management"
}
```

### Financial Services
```json
{
    "tenant": "Financial Institution",
    "tenants": "Financial Institutions",
    "sub_tenant": "Branch",
    "sub_tenants": "Branches",
    "user": "Account Manager",
    "users": "Account Managers",
    "role": "Position",
    "roles": "Positions",
    "permission": "Authorization",
    "permissions": "Authorizations",
    "resource": "Financial Service",
    "resources": "Financial Services",
    "dashboard": "Executive Dashboard",
    "tenant_management": "Institution Management",
    "user_management": "Staff Administration"
}
```

## Usage Examples

### 1. Basic Label Translation
```tsx
// Before
<h1>Tenant Management</h1>
<button>Create Tenant</button>

// After
const t = useT();
<h1>{t('tenant_management')}</h1>  // → "Maritime Authority Management"
<button>{t('create_tenant')}</button>  // → "Create Maritime Authority"
```

### 2. Dynamic Menu Labels
```tsx
// Navigation automatically adapts
const menuItems = [
    { label: t('dashboard'), icon: Home },        // → "Operations Center"
    { label: t('tenants'), icon: Building2 },     // → "Maritime Authorities"
    { label: t('users'), icon: Users },           // → "Maritime Stakeholders"
    { label: t('roles'), icon: Shield }           // → "Stakeholder Types"
];
```

### 3. Admin Terminology Management
```tsx
// Terminology management dialog
<TerminologyManagementDialog 
    tenant={selectedTenant}
    onSave={handleTerminologyUpdate}
/>
```

## Hierarchical Inheritance

The system supports multi-level terminology inheritance:

```
PLATFORM (Default Terminology)
    ├── Maritime Corp (Maritime Template)
    │   ├── Port of Miami (Inherits Maritime)
    │   └── Port of LA (Custom Override)
    └── Healthcare Inc (Healthcare Template)
        ├── Regional Hospital (Inherits Healthcare)
        └── Clinic Network (Custom Terms)
```

### Inheritance Rules
1. **Child inherits from parent** by default
2. **Local overrides** take precedence
3. **Selective inheritance** - can override specific terms
4. **Propagation options** - parent can push updates to children

## Performance Optimization

### Caching Strategy
- **In-memory cache** at service layer
- **Selective invalidation** on updates
- **Lazy loading** of terminology data
- **Optimistic updates** in frontend

### Database Optimization
- **Single JSON field** - no additional queries
- **Indexed tenant lookups**
- **Batch operations** for hierarchy updates

## Security Considerations

### Access Control
- Only **Super Admins** and **Tenant Admins** can modify terminology
- Changes are **audit logged**
- **Validation** prevents injection attacks

### Data Integrity
- **Schema validation** for terminology structure
- **Referential integrity** maintained
- **Rollback capability** for failed updates

## Migration Path

### For New Tenants
1. Select industry template during creation
2. Customize as needed
3. Apply to child tenants

### For Existing Tenants
1. Access Terminology from tenant dropdown menu
2. Choose industry template or customize manually
3. Save and apply changes
4. Optional: Propagate to children

## Benefits

### For End Users
- **Familiar terminology** reduces learning curve
- **Industry-specific language** feels natural
- **Consistent experience** across the platform

### For Administrators
- **Easy configuration** through UI
- **Template library** for quick setup
- **Hierarchical management** simplifies large deployments

### For Developers
- **Zero breaking changes** to existing code
- **Simple integration** with useT() hook
- **Type-safe** with TypeScript support
- **Extensible** for future enhancements

## Technical Details

### API Response Example
```json
{
    "terminology": {
        "tenant": "Maritime Authority",
        "user": "Stakeholder"
    },
    "is_inherited": false,
    "inherited_from": null,
    "local_config": {
        "tenant": "Maritime Authority"
    },
    "template_applied": "maritime",
    "last_updated": "2025-08-09T10:00:00Z"
}
```

### Frontend State Management
```typescript
// Terminology service maintains state
const terminologyService = {
    currentTerminology: Record<string, string>,
    cache: Map<tenantId, TerminologyConfig>,
    listeners: Set<callback>,
    
    // Real-time updates
    subscribe(callback) { /* ... */ },
    notifyListeners() { /* ... */ }
}
```

## Testing Strategy

### Unit Tests
- Terminology inheritance logic
- Translation functions
- Cache invalidation

### Integration Tests
- API endpoint responses
- Cross-tenant inheritance
- Template application

### E2E Tests
- UI terminology updates
- Real-time label changes
- Multi-tenant scenarios

## Future Enhancements

### Planned Features
1. **Multi-language support** - Combine with i18n
2. **Custom field mapping** - Beyond standard terms
3. **Bulk terminology import/export**
4. **AI-suggested terminology** based on industry
5. **Terminology versioning** with rollback

### Extensibility
The system is designed to be extended:
- Additional terminology keys
- New industry templates
- Custom validation rules
- Advanced inheritance patterns

## Conclusion

The terminology mapping system transforms Sentinel RBAC from a generic platform into an industry-specific solution without code changes. By allowing organizations to use their native terminology, we reduce friction, accelerate adoption, and improve user satisfaction while maintaining a single, unified codebase.

---

*Last Updated: 2025-08-09*  
*Version: 1.0*  
*Status: Production Ready*