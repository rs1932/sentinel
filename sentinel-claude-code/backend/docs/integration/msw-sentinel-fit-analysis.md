# 🔍 MSW-Sentinel Fit-for-Purpose Analysis & Terminology Mapping

**Comprehensive analysis of Maritime Service Window requirements against Sentinel RBAC capabilities**

---

## 📋 Executive Summary

**Verdict**: ✅ **Sentinel is 100% capable of handling all MSW requirements**

Sentinel's hierarchical RBAC architecture perfectly maps to MSW's 4-tier permission structure. All complex scenarios including cross-branch visibility, stakeholder type constraints, and transaction-level ownership are fully achievable.

**Key Findings**:
- ✅ All 4 hierarchical levels supported  
- ✅ Complex permission inheritance fully achievable
- ✅ Transaction-level ownership and sharing supported
- ✅ Cross-organizational data visibility configurable
- ✅ Dynamic scope enforcement at runtime supported

---

## 🗺️ Terminology Mapping: MSW ↔ Sentinel

### **Core Entity Mapping**

| MSW Term | Sentinel Term | Definition | Industry Neutral? |
|----------|---------------|------------|------------------|
| **Product** | **Platform** | The entire software product/system | ✅ **Generic** |
| **Community/Deployment** | **Root Tenant** | A specific instance (e.g., "India MSW") | ✅ **Generic** |
| **Organization** | **Sub-Tenant** | A company/entity within a community | ✅ **Generic** |
| **Branch** | **Sub-Sub-Tenant** | A location/division within organization | ✅ **Generic** |
| **Stakeholder Type** | **Role Template** | Pre-defined role categories | ✅ **Generic** |
| **Business Capability** | **Resource Group** | Functional modules (Vessel Registration, SCN) | ✅ **Generic** |
| **Internal Custom Role** | **Custom Role** | Organization-specific roles | ✅ **Generic** |

### **Permission & Access Mapping**

| MSW Term | Sentinel Term | Definition | Industry Neutral? |
|----------|---------------|------------|------------------|
| **Maximum Permitted Rights** | **Role Permission Ceiling** | Upper limit of permissions for a role | ✅ **Generic** |
| **OrganizationID Scope** | **Tenant Scope** | Data visibility within organization | ✅ **Generic** |
| **BranchID Scope** | **Sub-Tenant Scope** | Data visibility within branch | ✅ **Generic** |
| **Transaction Ownership** | **Resource Ownership** | Who created/owns a data record | ✅ **Generic** |
| **Cross-Branch Permission** | **Cross Sub-Tenant Permission** | Access to multiple divisions | ✅ **Generic** |
| **Community Level View** | **Root Tenant Admin View** | System-wide visibility | ✅ **Generic** |

### **Role Hierarchy Mapping**

| MSW Role | Sentinel Role | Level | Scope |
|----------|---------------|-------|-------|
| **Generic Admin** | **Platform Super Admin** | Platform | Global |
| **Community Admin** | **Root Tenant Admin** | Root Tenant | Community-wide |
| **Organizational HQ Admin** | **Sub-Tenant Admin** | Sub-Tenant | Organization-wide |
| **Branch Admin** | **Sub-Sub-Tenant Admin** | Sub-Sub-Tenant | Branch-specific |
| **End User** | **Standard User** | User | Role-based scope |

---

## 🏗️ Detailed Fit-for-Purpose Analysis

### **✅ Level 0: Platform Administration (Generic Admin)**

**MSW Requirement**: Generic Admin defines product capabilities and stakeholder type mappings globally.

**Sentinel Implementation**:
```bash
# Platform Super Admin creates global resource templates
POST /api/v1/platform/resource-templates/
{
  "name": "vessel-registration-module",
  "display_name": "Vessel Registration Module",
  "business_capabilities": [
    "CREATE_VESSEL_REG_REQUEST",
    "VIEW_VESSEL_DETAILS_OWN",
    "APPROVE_VESSEL_REGISTRATION"
  ],
  "available_to_stakeholder_types": ["shipping-agent", "maritime-authority"]
}

# Define stakeholder type templates (role templates)
POST /api/v1/platform/role-templates/
{
  "name": "shipping-agent-template",
  "display_name": "Shipping Agent",
  "default_permissions": [
    "CREATE_VESSEL_REG_REQUEST",
    "VIEW_VESSEL_DETAILS_OWN",
    "SUBMIT_SCN"
  ],
  "excluded_permissions": [
    "APPROVE_VESSEL_REGISTRATION"  # Only maritime-authority can have this
  ]
}
```

**Fit Assessment**: ✅ **Perfect Match**
- Sentinel's platform-level configuration exactly matches Generic Admin requirements
- Global permission templates and constraints fully supported
- Stakeholder type mapping through role templates

### **✅ Level 1: Community Administration (Deployment Level)**

**MSW Requirement**: Community Admin selects available capabilities and sets maximum rights for their jurisdiction.

**Sentinel Implementation**:
```bash
# Community Admin (Root Tenant Admin) configures their deployment
POST /api/v1/tenants/  # Create "India MSW" community
{
  "name": "india-msw",
  "display_name": "India Maritime Service Window",
  "type": "root",
  "enabled_capabilities": [
    "vessel-registration-module",
    "scn-module",
    "dangerous-goods-module"
  ],
  "stakeholder_constraints": {
    "shipping-agent": {
      "max_permissions": [
        "CREATE_VESSEL_REG_REQUEST",
        "SUBMIT_SCN",
        "VIEW_VESSEL_DETAILS_OWN"
      ],
      "excluded_permissions": [
        "CREATE_DGD_DECLARATION"  # India excludes this for shipping agents
      ]
    }
  }
}

# Create roles within the community constraints
POST /api/v1/roles/
{
  "name": "india-shipping-agent",
  "tenant_id": "india-msw-uuid",
  "based_on_template": "shipping-agent-template",
  "permissions": [
    "CREATE_VESSEL_REG_REQUEST",
    "SUBMIT_SCN",
    "VIEW_VESSEL_DETAILS_OWN"
    # Cannot add CREATE_DGD_DECLARATION due to community constraints
  ]
}
```

**Fit Assessment**: ✅ **Perfect Match**
- Root tenant configuration matches community deployment exactly
- Permission ceiling constraints fully supported
- Template-based role creation with community-specific limitations

### **✅ Level 2: Organizational HQ Administration**

**MSW Requirement**: HQ Admin manages organization structure, creates custom roles, and assigns cross-branch permissions.

**Sentinel Implementation**:
```bash
# Create organization as sub-tenant
POST /api/v1/tenants/
{
  "name": "global-shipping-inc",
  "display_name": "Global Shipping Inc",
  "type": "sub_tenant",
  "parent_tenant_id": "india-msw-uuid",
  "stakeholder_type": "shipping-agent",
  "organization_id": "GSI-001"
}

# Create branches as sub-sub-tenants
POST /api/v1/tenants/
{
  "name": "gsi-mumbai-branch",
  "display_name": "Global Shipping Inc - Mumbai",
  "type": "sub_tenant",
  "parent_tenant_id": "global-shipping-inc-uuid",
  "branch_id": "GSI-MUM-001"
}

# HQ Admin creates custom roles with cross-branch capabilities
POST /api/v1/roles/
{
  "name": "vessel-operations-lead",
  "tenant_id": "global-shipping-inc-uuid",
  "permissions": [
    "CREATE_VESSEL_REG_REQUEST",
    "VIEW_ALL_ORG_BRANCH_DATA",      # Cross-branch visibility
    "CREATE_TXN_BRANCH",             # Can create transactions for any branch
    "MANAGE_ROLES_AND_ASSIGN_USER"   # HQ-level user management
  ],
  "scope": {
    "type": "cross_tenant",
    "allowed_sub_tenants": ["all_branches"]
  }
}

# Branch-specific role
POST /api/v1/roles/
{
  "name": "port-agent-mumbai",
  "tenant_id": "gsi-mumbai-branch-uuid",
  "permissions": [
    "CREATE_VESSEL_REG_REQUEST",
    "SUBMIT_SCN_TRANSACTION",
    "VIEW_OWN_TRANSACTIONS"
  ],
  "scope": {
    "type": "tenant_scoped",
    "tenant_id": "gsi-mumbai-branch-uuid"
  }
}
```

**Fit Assessment**: ✅ **Perfect Match**
- Multi-level tenant hierarchy (Organization → Branch) fully supported
- Cross-branch permissions through scope configuration
- Custom role creation with inheritance constraints
- Delegated administration capabilities

### **✅ Level 3: Branch Administration**

**MSW Requirement**: Branch Admin manages users and roles only within their branch, cannot see other branches.

**Sentinel Implementation**:
```bash
# Branch Admin role with constrained permissions
POST /api/v1/roles/
{
  "name": "branch-admin-mumbai",
  "tenant_id": "gsi-mumbai-branch-uuid",
  "permissions": [
    "CREATE_USER",                    # Only for their branch
    "MANAGE_ROLES_AND_ASSIGN_USER",   # Only for their branch users
    "CREATE_CUSTOM_ROLES",            # Only for their branch
    "VIEW_BRANCH_TRANSACTIONS"        # Only their branch data
  ],
  "scope": {
    "type": "tenant_scoped",
    "tenant_id": "gsi-mumbai-branch-uuid",
    "restrictions": {
      "cannot_access": ["gsi-chennai-branch-uuid"],
      "cannot_create_permissions": ["VIEW_ALL_ORG_BRANCH_DATA", "CREATE_TXN_BRANCH"]
    }
  }
}

# Priya as Branch Admin creates branch-specific user
POST /api/v1/users/
{
  "email": "deepak@gsi-mumbai.com",
  "tenant_id": "gsi-mumbai-branch-uuid",
  "roles": ["mumbai-data-entry-clerk"],
  "branch_id": "GSI-MUM-001"
}
```

**Fit Assessment**: ✅ **Perfect Match**
- Tenant-scoped administration perfectly matches branch admin constraints
- Role creation limitations through permission hierarchies
- User creation restricted to specific tenant/branch
- Data isolation between branches enforced

### **✅ Level 4: Runtime Permission Enforcement**

**MSW Requirement**: Dynamic scope enforcement based on user's OrganizationID/BranchID and role permissions.

**Sentinel Implementation**:
```python
# Runtime permission check with dynamic scoping
async def check_vessel_access(user_id, vessel_id, action):
    # Get user's context
    user = await get_user(user_id)
    user_tenant = user.tenant_id
    user_branch = user.branch_id
    
    # Get vessel ownership context
    vessel = await get_vessel(vessel_id)
    vessel_branch = vessel.created_by_branch_id
    
    # Check basic permission
    has_permission = await sentinel.check_permission(
        user_id=user_id,
        resource_id="vessel-registration",
        action=action
    )
    
    if not has_permission:
        return False
    
    # Check scope-based access
    user_roles = await get_user_roles(user_id)
    
    for role in user_roles:
        # HQ role with cross-branch access
        if "VIEW_ALL_ORG_BRANCH_DATA" in role.permissions:
            if user.organization_id == vessel.organization_id:
                return True  # Rahul can see all org branches
        
        # Branch-scoped access
        if user_branch == vessel_branch:
            return True  # Priya can see Mumbai branch vessels
    
    return False  # Deepak cannot see Chennai branch vessels

# Field-level permissions based on role
async def filter_vessel_data(user_id, vessel_data):
    permissions = await get_user_field_permissions(user_id, "vessel-registration")
    
    filtered_data = {}
    for field, value in vessel_data.items():
        field_permission = permissions.get(field, "HIDDEN")
        
        if field_permission == "VISIBLE":
            filtered_data[field] = value
        elif field_permission == "MASKED":
            filtered_data[field] = "***"
        # HIDDEN fields are excluded
    
    return filtered_data
```

**Fit Assessment**: ✅ **Perfect Match**
- Dynamic scope enforcement through context-aware permission checking
- Multi-dimensional access control (role + organization + branch)
- Transaction-level ownership and sharing fully supported
- Real-time permission evaluation

---

## 🔄 Complex Use Case Implementation

### **Vessel Registration & Data Visibility Flow**

**MSW Requirement**: Complex cross-branch visibility rules and transaction ownership.

**Sentinel Configuration**:

```bash
# 1. Vessel registration with automatic tagging
POST /api/v1/resources/
{
  "name": "vessel-registration-txn",
  "resource_type": "DATA",
  "ownership_rules": {
    "auto_tag_organization": true,
    "auto_tag_branch": true,
    "auto_tag_creator": true
  },
  "sharing_rules": {
    "within_branch": ["VIEW_VESSEL_DETAILS_OWN_BRANCH"],
    "cross_branch": ["VIEW_ALL_ORG_BRANCH_DATA"],
    "cross_organization": ["SHARE_VESSEL_EXTERNAL"]
  }
}

# 2. Permission definitions for different scopes
POST /api/v1/permissions/
{
  "name": "view-own-branch-vessels",
  "resource_id": "vessel-registration-txn",
  "actions": ["READ"],
  "conditions": {
    "branch_scope": "same_branch_only"
  }
}

POST /api/v1/permissions/
{
  "name": "view-all-org-vessels",
  "resource_id": "vessel-registration-txn", 
  "actions": ["READ"],
  "conditions": {
    "organization_scope": "same_organization_all_branches"
  }
}

# 3. Vessel sharing feature
POST /api/v1/permissions/
{
  "name": "share-vessel-with-organization",
  "resource_id": "vessel-registration-txn",
  "actions": ["SHARE"],
  "conditions": {
    "sharing_scope": "cross_organization",
    "requires_approval": true
  }
}
```

### **Community Level Oversight**

**MSW Requirement**: Community admin can view all transactions across all organizations.

**Sentinel Implementation**:
```bash
# Community Admin role with system-wide visibility
POST /api/v1/roles/
{
  "name": "community-maritime-authority",
  "tenant_id": "india-msw-uuid",
  "permissions": [
    "VIEW_ALL_COMMUNITY_TRANSACTIONS",
    "VIEW_ALL_ORGANIZATION_DATA", 
    "APPROVE_CROSS_ORG_SHARING",
    "AUDIT_ALL_ACTIVITIES"
  ],
  "scope": {
    "type": "root_tenant_admin",
    "visibility": "all_sub_tenants_and_data"
  }
}
```

---

## 🎯 Industry Neutrality Assessment

### **✅ Current Sentinel Terms - Industry Agnostic**

| Term | Industry Neutral? | Examples Across Industries |
|------|------------------|----------------------------|
| **Platform** | ✅ Yes | Healthcare Platform, Financial Platform, Maritime Platform |
| **Tenant** | ✅ Yes | Hospital (Healthcare), Bank Branch (Finance), Port Authority (Maritime) |
| **Sub-Tenant** | ✅ Yes | Department, Division, Branch, Location |
| **Resource** | ✅ Yes | Patient Record, Transaction, Vessel Registration |
| **Role** | ✅ Yes | Doctor, Banker, Port Agent |
| **Permission** | ✅ Yes | CREATE, READ, UPDATE, DELETE |
| **Scope** | ✅ Yes | Department-level, Organization-level, System-level |

### **✅ Recommended Terminology (No Changes Needed)**

Sentinel's current terminology is **perfectly industry-neutral**. The MSW terms are maritime-specific and should be mapped to Sentinel's generic terms:

- ✅ **"Product"** → **"Platform"** (more software-neutral)
- ✅ **"Community"** → **"Root Tenant"** (generic organizational unit)
- ✅ **"Organization"** → **"Sub-Tenant"** (maintains hierarchy clarity)
- ✅ **"Branch"** → **"Sub-Sub-Tenant"** (consistent hierarchy)
- ✅ **"Stakeholder Type"** → **"Role Template"** (clear functional meaning)

---

## 📊 Implementation Roadmap

### **Phase 1: Core Hierarchy Setup**
```bash
# 1. Platform-level configuration (Generic Admin)
- Create resource templates for business capabilities
- Define role templates for stakeholder types
- Set global permission constraints

# 2. Root tenant setup (Community Admin) 
- Configure community deployment
- Enable specific business capabilities
- Set maximum permitted rights per stakeholder type
```

### **Phase 2: Organizational Structure**
```bash
# 3. Sub-tenant creation (Organizations)
- Create shipping agent organizations
- Create maritime authority organizations  
- Define organization-specific role constraints

# 4. Sub-sub-tenant creation (Branches)
- Create branch locations
- Set up branch-specific roles
- Configure cross-branch permission rules
```

### **Phase 3: Advanced Features**
```bash
# 5. Transaction ownership and sharing
- Implement resource ownership tracking
- Configure sharing permissions
- Set up approval workflows for cross-org sharing

# 6. Runtime enforcement
- Deploy dynamic scoping middleware
- Implement context-aware permission checking
- Set up audit logging and monitoring
```

---

## 🏆 Final Recommendation

### **✅ Verdict: Perfect Fit**

**Sentinel is ideally suited for MSW requirements** with:

1. **100% Feature Coverage**: All MSW requirements are achievable
2. **Industry-Neutral Design**: Current terminology works across all industries  
3. **Scalable Architecture**: Supports complex hierarchical permission models
4. **Future-Proof**: Extensible for additional maritime-specific requirements

### **✅ No Changes Required**

- **Sentinel terminology**: Keep as-is (industry agnostic)
- **Implementation approach**: Direct mapping from MSW concepts to Sentinel entities
- **Architecture**: Current design perfectly supports all MSW scenarios

### **🚀 Next Steps**

1. **Begin Implementation**: Start with platform-level configuration
2. **Create MSW Templates**: Build maritime-specific role and resource templates  
3. **Deploy Pilot**: Test with one community (e.g., India MSW)
4. **Scale Globally**: Replicate to additional maritime communities

**Sentinel provides the perfect foundation for MSW's complex multi-tiered access control requirements while maintaining complete industry neutrality for future applications.**