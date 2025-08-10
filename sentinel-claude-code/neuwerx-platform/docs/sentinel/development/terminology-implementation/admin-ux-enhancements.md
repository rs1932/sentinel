# Admin UX Enhancements for Terminology Mapping

**Version**: 1.0  
**Date**: 2025-08-09  
**Status**: Planning Phase

---

## 🎯 Overview

Enhance existing Sentinel admin interfaces to support industry terminology mapping without building entirely new screens. Focus on integrating terminology configuration seamlessly into current Super Admin and Tenant Admin workflows.

### Design Principles
1. **Extend, Don't Replace**: Enhance existing screens rather than create new ones
2. **Progressive Disclosure**: Show terminology options when relevant
3. **Intuitive Defaults**: Maintain familiar labels as defaults
4. **Visual Inheritance**: Clearly show inherited vs. custom terminology
5. **Contextual Help**: Provide guidance for terminology configuration

---

## 🔍 Current Admin Interface Analysis

### Super Admin Interfaces

#### 1. Platform Tenant Management (`/admin/platform/tenants`)
**Current State**: List view of all root tenants with basic CRUD operations

**Terminology Integration Points**:
- **Tenant List Table**: Show terminology status indicator
- **Create Tenant Modal**: Add optional terminology configuration step
- **Tenant Detail View**: Add terminology configuration section

#### 2. Tenant Detail/Edit Form (`/admin/tenants/{id}/edit`)
**Current State**: Form with tenant metadata, settings, features

**Terminology Integration Points**:
- **New Section**: "Display Terminology" configuration panel
- **Settings Tab**: Integrate terminology into existing settings structure
- **Preview Feature**: Live preview of how terminology affects UI labels

#### 3. Tenant Hierarchy View (`/admin/tenants/{id}/hierarchy`)
**Current State**: Tree view of tenant hierarchy with basic info

**Terminology Integration Points**:
- **Hierarchy Nodes**: Show terminology inheritance indicators
- **Bulk Operations**: Apply terminology to multiple tenants in hierarchy
- **Inheritance Visualization**: Visual flow of terminology inheritance

### Tenant Admin Interfaces

#### 1. Tenant Dashboard (`/dashboard`)
**Current State**: Overview of tenant metrics, user counts, recent activity

**Terminology Integration Points**:
- **Quick Settings**: Add terminology customization widget
- **Navigation Labels**: Dynamic labels based on current terminology
- **Welcome Text**: Personalized based on industry terminology

#### 2. Organization Management (`/admin/organization`)
**Current State**: Manage organization structure, branches, departments

**Terminology Integration Points**:
- **Section Headers**: Dynamic headers using terminology
- **Create Forms**: Labels adapt to current terminology
- **Breadcrumbs**: Navigation reflects terminology

#### 3. User Management (`/admin/users`)
**Current State**: User list, creation, role assignment

**Terminology Integration Points**:
- **Page Title**: "Stakeholder Management" instead of "User Management"
- **Action Buttons**: "Add Maritime Professional" instead of "Add User"
- **Table Headers**: Industry-specific column names

---

## 🎨 Detailed UX Enhancement Specifications

### 1. Super Admin - Tenant List Enhancement

#### Current Screen
```
[Tenants Management]
┌─────────────────────────────────────────────────────┐
│ Name           | Type      | Status  | Actions      │
├─────────────────────────────────────────────────────┤
│ Maritime Corp  | Root      | Active  | Edit Delete  │
│ Healthcare Inc | Root      | Active  | Edit Delete  │
└─────────────────────────────────────────────────────┘
```

#### Enhanced Screen
```
[Tenants Management]
┌──────────────────────────────────────────────────────────────┐
│ Name           | Type | Status | Terminology    | Actions     │
├──────────────────────────────────────────────────────────────┤
│ Maritime Corp  | Root | Active | 🏢 Maritime    | Edit Delete │
│ Healthcare Inc | Root | Active | 🏥 Healthcare  | Edit Delete │  
│ Finance Bank   | Root | Active | 💰 Default     | Edit Delete │
└──────────────────────────────────────────────────────────────┘
```

**Implementation**:
```typescript
// Enhanced tenant list component
const TenantListItem = ({ tenant }) => {
  const terminologyIcon = getTerminologyIcon(tenant.terminology_type);
  const terminologyLabel = tenant.terminology_config?.label || 'Default';
  
  return (
    <tr>
      <td>{tenant.name}</td>
      <td>{tenant.type}</td>
      <td>{tenant.status}</td>
      <td>
        <span className="terminology-badge">
          {terminologyIcon} {terminologyLabel}
        </span>
      </td>
      <td>{/* Actions */}</td>
    </tr>
  );
};
```

### 2. Super Admin - Create Tenant Modal Enhancement

#### Current Modal
```
┌─── Create Tenant ───────────────────────┐
│ Name: [____________________]            │
│ Code: [____________________]            │
│ Type: [Root ▼]                         │
│ Parent: [None ▼]                       │
│                                        │
│ [Cancel]              [Create Tenant]  │
└────────────────────────────────────────┘
```

#### Enhanced Modal
```
┌─── Create Tenant ───────────────────────────────────┐
│ Basic Information                                   │
│ Name: [____________________]                        │
│ Code: [____________________]                        │
│ Type: [Root ▼]                                     │
│ Parent: [None ▼]                                   │
│                                                    │
│ ┌─ Display Terminology (Optional) ─────────────┐   │
│ │ ○ Use Default Terms                          │   │
│ │ ○ Industry Template: [Maritime ▼]           │   │
│ │ ○ Custom Terminology                         │   │
│ │                                              │   │
│ │ Preview: "Create Maritime Authority"         │   │
│ └──────────────────────────────────────────────┘   │
│                                                    │
│ [Cancel]                        [Create Tenant]    │
└────────────────────────────────────────────────────┘
```

**Implementation**:
```tsx
const CreateTenantModal = () => {
  const [terminologyMode, setTerminologyMode] = useState('default');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [customTerms, setCustomTerms] = useState({});
  
  const getPreviewLabel = () => {
    switch (terminologyMode) {
      case 'template':
        return INDUSTRY_TEMPLATES[selectedTemplate]?.create_tenant || 'Create Tenant';
      case 'custom':
        return customTerms.create_tenant || 'Create Tenant';
      default:
        return 'Create Tenant';
    }
  };
  
  return (
    <Modal>
      {/* Basic fields */}
      
      <div className="terminology-section">
        <h3>Display Terminology (Optional)</h3>
        
        <RadioGroup value={terminologyMode} onChange={setTerminologyMode}>
          <Radio value="default">Use Default Terms</Radio>
          <Radio value="template">
            Industry Template:
            <Select value={selectedTemplate} onChange={setSelectedTemplate}>
              <option value="maritime">Maritime</option>
              <option value="healthcare">Healthcare</option>
              <option value="finance">Finance</option>
            </Select>
          </Radio>
          <Radio value="custom">Custom Terminology</Radio>
        </RadioGroup>
        
        {terminologyMode === 'custom' && (
          <TerminologyEditor terms={customTerms} onChange={setCustomTerms} />
        )}
        
        <div className="terminology-preview">
          Preview: "{getPreviewLabel()}"
        </div>
      </div>
      
      {/* Create button */}
    </Modal>
  );
};
```

### 3. Super Admin - Tenant Detail Enhancement

#### Current Detail Page
```
┌─── Tenant Details: Maritime Corp ──────────────────┐
│ Basic Information                                   │
│ Name: Maritime Corp                                │
│ Code: MARITIME-CORP                                │
│ Type: Root                                         │
│ Status: Active                                     │
│                                                    │
│ Settings                                           │
│ Features: [multi_factor_auth, api_access]         │
│ Isolation: Shared                                  │
│                                                    │
│ [Edit] [Delete] [Deactivate]                      │
└────────────────────────────────────────────────────┘
```

#### Enhanced Detail Page
```
┌─── Tenant Details: Maritime Corp ──────────────────────────────┐
│ Basic Information                                               │
│ Name: Maritime Corp                                            │
│ Code: MARITIME-CORP                                            │
│ Type: Root                                                     │
│ Status: Active                                                 │
│                                                                │
│ ┌─ Display Terminology ─────────────────────────────────────┐ │
│ │ Status: 🏢 Maritime Industry Template                    │ │
│ │                                                          │ │
│ │ Key Terms:                                               │ │
│ │ • Tenant → "Maritime Authority"                          │ │
│ │ • User → "Maritime Stakeholder"                          │ │
│ │ • Role → "Stakeholder Type"                              │ │
│ │                                                          │ │
│ │ Applied to: 5 child tenants                              │ │
│ │ Last Updated: 2025-08-09 10:30 AM                        │ │
│ │                                                          │ │
│ │ [Edit Terminology] [Reset to Default] [Apply to Children]│ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                                │
│ Settings                                                       │
│ Features: [multi_factor_auth, api_access]                     │
│ Isolation: Shared                                              │
│                                                                │
│ [Edit] [Delete] [Deactivate]                                  │
└────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```tsx
const TenantDetailPage = ({ tenantId }) => {
  const { tenant, terminology } = useTenantWithTerminology(tenantId);
  
  return (
    <div className="tenant-detail">
      {/* Basic info */}
      
      <TerminologySection 
        tenant={tenant}
        terminology={terminology}
        onUpdate={handleTerminologyUpdate}
        onReset={handleTerminologyReset}
        onApplyToChildren={handleApplyToChildren}
      />
      
      {/* Other sections */}
    </div>
  );
};

const TerminologySection = ({ tenant, terminology, onUpdate, onReset, onApplyToChildren }) => {
  const getTerminologyStatus = () => {
    if (terminology.is_inherited) {
      return `📄 Inherited from ${terminology.inherited_from_name}`;
    }
    if (terminology.is_template) {
      return `🏢 ${terminology.template_name} Industry Template`;
    }
    return '⚙️ Custom Configuration';
  };
  
  return (
    <div className="terminology-section">
      <h3>Display Terminology</h3>
      
      <div className="terminology-status">
        Status: {getTerminologyStatus()}
      </div>
      
      <div className="key-terms">
        <h4>Key Terms:</h4>
        {Object.entries(terminology.terms).slice(0, 5).map(([key, value]) => (
          <div key={key} className="term-mapping">
            • {key} → "{value}"
          </div>
        ))}
      </div>
      
      <div className="terminology-stats">
        Applied to: {tenant.child_count} child tenants<br/>
        Last Updated: {terminology.last_updated}
      </div>
      
      <div className="terminology-actions">
        <Button onClick={onUpdate}>Edit Terminology</Button>
        <Button onClick={onReset} variant="secondary">Reset to Default</Button>
        <Button onClick={onApplyToChildren} variant="secondary">Apply to Children</Button>
      </div>
    </div>
  );
};
```

### 4. Terminology Configuration Modal

#### Full Editor Modal
```
┌─── Configure Terminology: Maritime Corp ───────────────────────┐
│ ┌─ Basic Terms ─────────────────────────────────────────────┐ │
│ │ Tenant:      [Maritime Authority          ] Default       │ │
│ │ Sub-Tenant:  [Port Organization          ] Default       │ │  
│ │ User:        [Maritime Stakeholder       ] Default       │ │
│ │ Role:        [Stakeholder Type           ] Default       │ │
│ │ Permission:  [Service Clearance          ] Default       │ │
│ │ Resource:    [Maritime Service           ] Default       │ │
│ │ Group:       [Stakeholder Group          ] Default       │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─ Action Labels ───────────────────────────────────────────┐ │
│ │ Create Tenant:    [Register Maritime Organization] Default│ │
│ │ Tenant Mgmt:      [Maritime Authority Management ] Default│ │
│ │ User Management:  [Stakeholder Management        ] Default│ │
│ │ Role Assignment:  [Stakeholder Type Assignment   ] Default│ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─ Inheritance Options ─────────────────────────────────────┐ │
│ │ ☑ Apply to child tenants                                  │ │
│ │ ☑ Allow children to override                              │ │
│ │ ☐ Lock terminology (prevent child changes)                │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─ Preview ─────────────────────────────────────────────────┐ │
│ │ Button: "Register Maritime Organization"                   │ │
│ │ Header: "Maritime Authority Management"                    │ │
│ │ Label:  "Stakeholder Name"                                │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│ [Reset to Template] [Cancel]              [Save Terminology] │
└───────────────────────────────────────────────────────────────┘
```

**Implementation**:
```tsx
const TerminologyConfigModal = ({ tenant, isOpen, onClose, onSave }) => {
  const [terminology, setTerminology] = useState(tenant.terminology || {});
  const [inheritanceOptions, setInheritanceOptions] = useState({
    applyToChildren: false,
    allowChildOverride: true,
    lockTerminology: false
  });
  
  const updateTerm = (key, value) => {
    setTerminology(prev => ({ ...prev, [key]: value }));
  };
  
  const resetToDefault = (key) => {
    const defaultValue = DEFAULT_TERMINOLOGY[key];
    updateTerm(key, defaultValue);
  };
  
  const previewLabels = {
    createButton: terminology.create_tenant || 'Create Tenant',
    managementHeader: terminology.tenant_management || 'Tenant Management',
    userLabel: `${terminology.user || 'User'} Name`
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <h2>Configure Terminology: {tenant.name}</h2>
      
      <div className="terminology-editor">
        <section className="basic-terms">
          <h3>Basic Terms</h3>
          {BASIC_TERM_KEYS.map(key => (
            <div key={key} className="term-field">
              <label>{key.replace('_', ' ').toTitleCase()}:</label>
              <div className="term-input-group">
                <input
                  value={terminology[key] || ''}
                  onChange={(e) => updateTerm(key, e.target.value)}
                  placeholder={DEFAULT_TERMINOLOGY[key]}
                />
                <button 
                  className="reset-default"
                  onClick={() => resetToDefault(key)}
                  title="Reset to default"
                >
                  Default
                </button>
              </div>
            </div>
          ))}
        </section>
        
        <section className="action-labels">
          <h3>Action Labels</h3>
          {ACTION_LABEL_KEYS.map(key => (
            <div key={key} className="term-field">
              <label>{key.replace('_', ' ').toTitleCase()}:</label>
              <div className="term-input-group">
                <input
                  value={terminology[key] || ''}
                  onChange={(e) => updateTerm(key, e.target.value)}
                  placeholder={DEFAULT_TERMINOLOGY[key]}
                />
                <button onClick={() => resetToDefault(key)}>Default</button>
              </div>
            </div>
          ))}
        </section>
        
        <section className="inheritance-options">
          <h3>Inheritance Options</h3>
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={inheritanceOptions.applyToChildren}
                onChange={(e) => setInheritanceOptions(prev => ({
                  ...prev, applyToChildren: e.target.checked
                }))}
              />
              Apply to child tenants
            </label>
            
            <label>
              <input
                type="checkbox"
                checked={inheritanceOptions.allowChildOverride}
                onChange={(e) => setInheritanceOptions(prev => ({
                  ...prev, allowChildOverride: e.target.checked
                }))}
              />
              Allow children to override
            </label>
            
            <label>
              <input
                type="checkbox"
                checked={inheritanceOptions.lockTerminology}
                onChange={(e) => setInheritanceOptions(prev => ({
                  ...prev, lockTerminology: e.target.checked
                }))}
              />
              Lock terminology (prevent child changes)
            </label>
          </div>
        </section>
        
        <section className="preview">
          <h3>Preview</h3>
          <div className="preview-examples">
            <div>Button: "{previewLabels.createButton}"</div>
            <div>Header: "{previewLabels.managementHeader}"</div>
            <div>Label: "{previewLabels.userLabel}"</div>
          </div>
        </section>
      </div>
      
      <div className="modal-actions">
        <button onClick={() => resetToTemplate()}>Reset to Template</button>
        <button onClick={onClose}>Cancel</button>
        <button 
          onClick={() => onSave(terminology, inheritanceOptions)}
          className="primary"
        >
          Save Terminology
        </button>
      </div>
    </Modal>
  );
};
```

### 5. Tenant Admin - Dashboard Enhancement

#### Current Dashboard
```
┌─── Dashboard - Maritime Corp ──────────────────────┐
│ Welcome back, Admin!                               │
│                                                    │
│ ┌─ Quick Stats ─────────────────────────────────┐  │
│ │ Users: 45        Roles: 12                   │  │
│ │ Groups: 8        Resources: 23               │  │
│ └──────────────────────────────────────────────┘  │
│                                                    │
│ Recent Activity                                    │
│ • User John created                                │
│ • Role 'Manager' updated                           │
│                                                    │
│ Quick Actions                                      │
│ [Create User] [Manage Roles] [View Resources]     │
└────────────────────────────────────────────────────┘
```

#### Enhanced Dashboard
```
┌─── Maritime Authority Dashboard - Maritime Corp ────────────────┐
│ Welcome back, Maritime Administrator!                           │
│                                                                 │
│ ┌─ Quick Stats ─────────────────────────────────────────────┐   │
│ │ Stakeholders: 45    Stakeholder Types: 12               │   │
│ │ Groups: 8           Maritime Services: 23               │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│ ┌─ Terminology Settings ───────────────┐ Recent Activity       │
│ │ Current: 🏢 Maritime Industry        │ • Stakeholder John... │
│ │ Last Updated: Aug 9, 2025            │ • Stakeholder Type... │
│ │                                      │                       │
│ │ [Customize Terminology]              │ Quick Actions         │
│ └──────────────────────────────────────┘ [Add Stakeholder]    │
│                                          [Manage Types]        │
│                                          [View Services]       │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```tsx
const TenantDashboard = () => {
  const { tenant, terminology } = useCurrentTenantWithTerminology();
  const { user } = useCurrentUser();
  
  // Dynamic labels based on terminology
  const labels = {
    welcome: `Welcome back, ${terminology.admin_title || 'Administrator'}!`,
    stakeholders: terminology.user || 'Users',
    stakeholderTypes: terminology.role || 'Roles', 
    services: terminology.resource || 'Resources',
    addStakeholder: `Add ${terminology.user || 'User'}`,
    manageTypes: `Manage ${terminology.role_plural || 'Roles'}`,
    viewServices: `View ${terminology.resource_plural || 'Resources'}`
  };
  
  return (
    <div className="dashboard">
      <h1>{terminology.dashboard_title || 'Dashboard'} - {tenant.name}</h1>
      <p>{labels.welcome}</p>
      
      <div className="quick-stats">
        <div className="stat">
          <span className="label">{labels.stakeholders}:</span>
          <span className="value">{tenant.user_count}</span>
        </div>
        <div className="stat">
          <span className="label">{labels.stakeholderTypes}:</span>
          <span className="value">{tenant.role_count}</span>
        </div>
        <div className="stat">
          <span className="label">Groups:</span>
          <span className="value">{tenant.group_count}</span>
        </div>
        <div className="stat">
          <span className="label">{labels.services}:</span>
          <span className="value">{tenant.resource_count}</span>
        </div>
      </div>
      
      <div className="dashboard-content">
        <div className="terminology-widget">
          <h3>Terminology Settings</h3>
          <div className="terminology-status">
            Current: {getTerminologyStatusIcon(terminology)} {terminology.display_name}
          </div>
          <div className="terminology-meta">
            Last Updated: {formatDate(terminology.last_updated)}
          </div>
          <button onClick={() => openTerminologyModal()}>
            Customize Terminology
          </button>
        </div>
        
        <div className="recent-activity">
          <h3>Recent Activity</h3>
          <ActivityFeed terminology={terminology} />
        </div>
      </div>
      
      <div className="quick-actions">
        <button className="primary">{labels.addStakeholder}</button>
        <button>{labels.manageTypes}</button>
        <button>{labels.viewServices}</button>
      </div>
    </div>
  );
};
```

### 6. Tenant Admin - User Management Enhancement

#### Current User Management
```
┌─── User Management ─────────────────────────────────────────┐
│ [Add User]                                    [Export] [⚙] │
│                                                             │
│ Name           | Email              | Role      | Status   │
│ John Smith     | john@company.com   | Manager   | Active   │
│ Jane Doe       | jane@company.com   | User      | Active   │
│ Bob Wilson     | bob@company.com    | Admin     | Inactive │
└─────────────────────────────────────────────────────────────┘
```

#### Enhanced User Management (Maritime)
```
┌─── Stakeholder Management ──────────────────────────────────────┐
│ [Add Maritime Stakeholder]                    [Export] [⚙]     │
│                                                                 │
│ Stakeholder Name | Email              | Stakeholder Type | Status │
│ John Smith       | john@company.com   | Port Manager     | Active │
│ Jane Doe         | jane@company.com   | Agent            | Active │
│ Bob Wilson       | bob@company.com    | Authority        | Inactive │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```tsx
const UserManagementPage = () => {
  const { terminology } = useTerminology();
  
  const pageTitle = terminology.user_management || 'User Management';
  const addButtonLabel = `Add ${terminology.user || 'User'}`;
  const nameColumnHeader = `${terminology.user || 'User'} Name`;
  const roleColumnHeader = terminology.role || 'Role';
  
  return (
    <div className="user-management">
      <header className="page-header">
        <h1>{pageTitle}</h1>
        <div className="page-actions">
          <button className="primary">{addButtonLabel}</button>
          <button>Export</button>
          <button>⚙</button>
        </div>
      </header>
      
      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>{nameColumnHeader}</th>
              <th>Email</th>
              <th>{roleColumnHeader}</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <UserRow key={user.id} user={user} terminology={terminology} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const UserRow = ({ user, terminology }) => {
  const editLabel = `Edit ${terminology.user || 'User'}`;
  const deleteLabel = `Delete ${terminology.user || 'User'}`;
  
  return (
    <tr>
      <td>{user.name}</td>
      <td>{user.email}</td>
      <td>{user.role_name}</td>
      <td>
        <span className={`status-badge ${user.status}`}>
          {user.status}
        </span>
      </td>
      <td className="actions">
        <button title={editLabel}>✏</button>
        <button title={deleteLabel}>🗑</button>
      </td>
    </tr>
  );
};
```

---

## 🛠️ Technical Implementation Details

### Frontend Terminology Service

```typescript
// services/terminology.service.ts
interface TerminologyConfig {
  tenant_id: string;
  terminology: Record<string, string>;
  is_inherited: boolean;
  inherited_from?: string;
  last_updated: string;
}

class TerminologyService {
  private cache = new Map<string, TerminologyConfig>();
  
  async getTerminology(tenantId: string): Promise<TerminologyConfig> {
    if (!this.cache.has(tenantId)) {
      const config = await this.fetchFromAPI(tenantId);
      this.cache.set(tenantId, config);
    }
    return this.cache.get(tenantId)!;
  }
  
  async updateTerminology(
    tenantId: string, 
    terminology: Record<string, string>,
    options: TerminologyUpdateOptions
  ): Promise<void> {
    await this.updateViaAPI(tenantId, terminology, options);
    this.cache.delete(tenantId); // Invalidate cache
    
    // If applying to children, invalidate their cache too
    if (options.applyToChildren) {
      await this.invalidateChildrenCache(tenantId);
    }
  }
  
  getTerm(terminology: TerminologyConfig, key: string): string {
    return terminology.terminology[key] || this.getDefaultTerm(key);
  }
  
  private getDefaultTerm(key: string): string {
    return DEFAULT_TERMINOLOGY[key] || key.replace('_', ' ').toTitleCase();
  }
  
  private async fetchFromAPI(tenantId: string): Promise<TerminologyConfig> {
    const response = await fetch(`/api/v1/tenants/${tenantId}/terminology`);
    return response.json();
  }
  
  private async updateViaAPI(
    tenantId: string,
    terminology: Record<string, string>,
    options: TerminologyUpdateOptions
  ): Promise<void> {
    await fetch(`/api/v1/tenants/${tenantId}/terminology`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ terminology, ...options })
    });
  }
  
  private async invalidateChildrenCache(tenantId: string): Promise<void> {
    // Get child tenant IDs and remove from cache
    const childIds = await this.getChildTenantIds(tenantId);
    childIds.forEach(id => this.cache.delete(id));
  }
}
```

### React Hooks for Terminology

```typescript
// hooks/useTerminology.ts
export const useTerminology = () => {
  const { currentTenant } = useCurrentTenant();
  const [terminology, setTerminology] = useState<TerminologyConfig | null>(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (currentTenant?.id) {
      loadTerminology(currentTenant.id);
    }
  }, [currentTenant?.id]);
  
  const loadTerminology = async (tenantId: string) => {
    setLoading(true);
    try {
      const config = await terminologyService.getTerminology(tenantId);
      setTerminology(config);
    } finally {
      setLoading(false);
    }
  };
  
  const updateTerminology = async (
    newTerminology: Record<string, string>,
    options?: TerminologyUpdateOptions
  ) => {
    if (!currentTenant) return;
    
    await terminologyService.updateTerminology(
      currentTenant.id,
      newTerminology,
      options || {}
    );
    
    // Reload terminology
    await loadTerminology(currentTenant.id);
  };
  
  const getTerm = (key: string): string => {
    if (!terminology) return key.replace('_', ' ').toTitleCase();
    return terminologyService.getTerm(terminology, key);
  };
  
  return {
    terminology,
    loading,
    updateTerminology,
    getTerm
  };
};

// hooks/useTerminologyLabels.ts
export const useTerminologyLabels = () => {
  const { getTerm } = useTerminology();
  
  return {
    // Basic entities
    tenant: getTerm('tenant'),
    subTenant: getTerm('sub_tenant'),
    user: getTerm('user'),
    role: getTerm('role'),
    permission: getTerm('permission'),
    resource: getTerm('resource'),
    group: getTerm('group'),
    
    // Plural forms
    tenants: getTerm('tenants'),
    users: getTerm('users'),
    roles: getTerm('roles'),
    permissions: getTerm('permissions'),
    resources: getTerm('resources'),
    groups: getTerm('groups'),
    
    // Actions
    createTenant: getTerm('create_tenant'),
    createUser: getTerm('create_user'),
    createRole: getTerm('create_role'),
    
    // Management pages
    tenantManagement: getTerm('tenant_management'),
    userManagement: getTerm('user_management'),
    roleManagement: getTerm('role_management'),
    
    // Dashboard
    dashboardTitle: getTerm('dashboard_title'),
    welcomeMessage: getTerm('welcome_message'),
    adminTitle: getTerm('admin_title')
  };
};
```

### CSS for Terminology UI

```scss
// terminology-ui.scss
.terminology-section {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 1rem 0;
  
  h3 {
    margin-top: 0;
    color: #495057;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    
    &::before {
      content: '🎨';
      font-size: 1.2em;
    }
  }
}

.terminology-status {
  font-weight: 500;
  color: #28a745;
  margin-bottom: 1rem;
}

.key-terms {
  margin: 1rem 0;
  
  .term-mapping {
    padding: 0.25rem 0;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.9em;
    color: #6c757d;
  }
}

.terminology-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  
  button {
    padding: 0.5rem 1rem;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    
    &:hover {
      background: #f8f9fa;
    }
    
    &.primary {
      background: #007bff;
      color: white;
      border-color: #007bff;
      
      &:hover {
        background: #0056b3;
      }
    }
  }
}

.terminology-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.85em;
  color: #495057;
}

.terminology-editor {
  .term-field {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    
    label {
      min-width: 120px;
      font-weight: 500;
    }
    
    .term-input-group {
      display: flex;
      gap: 0.5rem;
      flex: 1;
      
      input {
        flex: 1;
        padding: 0.5rem;
        border: 1px solid #ced4da;
        border-radius: 4px;
        
        &:focus {
          outline: none;
          border-color: #007bff;
          box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }
      }
      
      .reset-default {
        padding: 0.5rem 0.75rem;
        background: #f8f9fa;
        border: 1px solid #ced4da;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.8em;
        
        &:hover {
          background: #e9ecef;
        }
      }
    }
  }
}

.terminology-preview {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1rem;
  
  h4 {
    margin-top: 0;
    margin-bottom: 0.5rem;
  }
  
  .preview-examples {
    div {
      padding: 0.25rem 0;
      font-family: 'Monaco', 'Menlo', monospace;
      font-size: 0.9em;
    }
  }
}

.inheritance-options {
  .checkbox-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    
    label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      
      input[type="checkbox"] {
        margin: 0;
      }
    }
  }
}

// Responsive design
@media (max-width: 768px) {
  .terminology-section {
    padding: 1rem;
  }
  
  .terminology-actions {
    flex-direction: column;
    
    button {
      width: 100%;
    }
  }
  
  .terminology-editor .term-field {
    flex-direction: column;
    align-items: stretch;
    
    label {
      min-width: unset;
    }
  }
}
```

---

## 📱 Mobile Responsiveness

### Mobile Terminology Configuration
```scss
// Mobile-specific terminology UI
@media (max-width: 480px) {
  .terminology-config-modal {
    .modal-content {
      margin: 0;
      height: 100vh;
      border-radius: 0;
    }
    
    .terminology-editor {
      .term-field {
        margin-bottom: 1.5rem;
        
        .term-input-group {
          flex-direction: column;
          
          input {
            margin-bottom: 0.5rem;
          }
        }
      }
    }
    
    .modal-actions {
      position: sticky;
      bottom: 0;
      background: white;
      border-top: 1px solid #dee2e6;
      padding: 1rem;
    }
  }
}
```

---

## ♿ Accessibility Considerations

### ARIA Labels and Screen Reader Support
```tsx
const TerminologySection = ({ terminology }) => {
  return (
    <section 
      className="terminology-section"
      aria-labelledby="terminology-heading"
      aria-describedby="terminology-description"
    >
      <h3 id="terminology-heading">Display Terminology</h3>
      <p id="terminology-description" className="sr-only">
        Configure how entity names appear in the user interface
      </p>
      
      <div className="terminology-status" role="status" aria-live="polite">
        Status: {getTerminologyStatusDescription(terminology)}
      </div>
      
      {/* Rest of component */}
    </section>
  );
};

const TerminologyEditor = ({ terms, onChange }) => {
  return (
    <div className="terminology-editor" role="group" aria-label="Terminology configuration">
      {Object.entries(terms).map(([key, value]) => (
        <div key={key} className="term-field">
          <label htmlFor={`term-${key}`}>
            {key.replace('_', ' ').toTitleCase()}:
          </label>
          <div className="term-input-group">
            <input
              id={`term-${key}`}
              value={value}
              onChange={(e) => onChange(key, e.target.value)}
              aria-describedby={`term-${key}-help`}
            />
            <span id={`term-${key}-help`} className="sr-only">
              Default value: {DEFAULT_TERMINOLOGY[key]}
            </span>
            <button 
              onClick={() => onChange(key, DEFAULT_TERMINOLOGY[key])}
              aria-label={`Reset ${key} to default value`}
            >
              Default
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## 🧪 Testing Strategy for UX Components

### Component Testing
```tsx
// TerminologySection.test.tsx
describe('TerminologySection', () => {
  it('displays inherited terminology status', () => {
    const terminology = {
      is_inherited: true,
      inherited_from_name: 'Parent Tenant',
      terms: { tenant: 'Maritime Authority' }
    };
    
    render(<TerminologySection terminology={terminology} />);
    
    expect(screen.getByText(/Inherited from Parent Tenant/)).toBeInTheDocument();
  });
  
  it('allows editing custom terminology', async () => {
    const onUpdate = jest.fn();
    render(<TerminologySection onUpdate={onUpdate} />);
    
    const editButton = screen.getByText('Edit Terminology');
    fireEvent.click(editButton);
    
    expect(onUpdate).toHaveBeenCalled();
  });
  
  it('shows correct terminology preview', () => {
    const terminology = {
      terms: {
        tenant: 'Maritime Authority',
        create_tenant: 'Register Maritime Organization'
      }
    };
    
    render(<TerminologySection terminology={terminology} />);
    
    expect(screen.getByText(/Maritime Authority/)).toBeInTheDocument();
  });
});
```

### Integration Testing
```tsx
// TenantDetail.integration.test.tsx  
describe('Tenant Detail Integration', () => {
  it('updates terminology and reflects changes in UI', async () => {
    const tenant = createMockTenant();
    render(<TenantDetailPage tenantId={tenant.id} />);
    
    // Open terminology editor
    const editButton = await screen.findByText('Edit Terminology');
    fireEvent.click(editButton);
    
    // Update terminology
    const tenantInput = screen.getByLabelText(/Tenant:/);
    fireEvent.change(tenantInput, { target: { value: 'Custom Authority' } });
    
    const saveButton = screen.getByText('Save Terminology');
    fireEvent.click(saveButton);
    
    // Verify API call
    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith(
        expect.objectContaining({
          terminology: expect.objectContaining({
            tenant: 'Custom Authority'
          })
        })
      );
    });
    
    // Verify UI updates
    await waitFor(() => {
      expect(screen.getByText(/Custom Authority/)).toBeInTheDocument();
    });
  });
});
```

---

*Last Updated: 2025-08-09*