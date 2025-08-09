# 🚀 Sentinel Setup Guide: From Zero to Production

**Complete step-by-step guide for setting up a new application with Sentinel RBAC**

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Sentinel Platform Access** - Running Sentinel instance with API access
- [ ] **Super Admin Credentials** - For initial tenant setup
- [ ] **Application Requirements** - Clear understanding of your app's permission needs
- [ ] **Technical Stack** - Development environment ready
- [ ] **Database Access** - If you need custom field definitions

---

## 🏗️ Phase 1: Initial Platform Setup

### **Step 1: Access Sentinel Super Admin**

```bash
# Login as super admin
POST /api/v1/auth/login
{
  "email": "superadmin@sentinel.com",
  "password": "super_secure_password",
  "tenant_id": "sentinel-platform"  # Super admin tenant
}
```

**Expected Result**: JWT token with super admin privileges

### **Step 2: Create Your Application Tenant**

```bash
# Create root tenant for your application
POST /api/v1/tenants/
Authorization: Bearer {super_admin_token}

{
  "name": "my-awesome-app",
  "display_name": "My Awesome Application",
  "type": "root",
  "isolation_mode": "shared",
  "settings": {
    "max_users": 10000,
    "features": ["RBAC", "AUDIT", "MENUS", "FIELD_DEFINITIONS"],
    "default_role": "employee",
    "session_timeout": 3600
  },
  "metadata": {
    "application_type": "SaaS",
    "industry": "Healthcare",
    "compliance_requirements": ["HIPAA", "SOC2"]
  }
}
```

**Expected Result**: Tenant created with UUID, ready for configuration

### **Step 3: Create Tenant Administrator**

```bash
# Create the first admin user for your tenant
POST /api/v1/users/
Authorization: Bearer {super_admin_token}

{
  "email": "admin@myawesome.com",
  "password": "secure_admin_password",
  "first_name": "Admin",
  "last_name": "User",
  "tenant_id": "{your_tenant_uuid}",
  "user_type": "admin",
  "attributes": {
    "department": "IT",
    "access_level": "full"
  }
}
```

### **Step 4: Assign Super Admin Role**

```bash
# Assign super admin role to tenant administrator
POST /api/v1/roles/{admin_role_id}/users
Authorization: Bearer {super_admin_token}

{
  "user_id": "{admin_user_uuid}",
  "assigned_by": "{super_admin_uuid}",
  "expires_at": null,
  "metadata": {
    "assignment_reason": "Initial tenant setup"
  }
}
```

---

## 🎯 Phase 2: Application Structure Setup

**⚠️ From this point forward, login as the Tenant Administrator**

```bash
# Login as tenant admin
POST /api/v1/auth/login
{
  "email": "admin@myawesome.com",
  "password": "secure_admin_password", 
  "tenant_id": "{your_tenant_uuid}"
}
```

### **Step 5: Define Application Resources**

Create resources that represent your application's components:

```bash
# Create main application resources
POST /api/v1/resources/
Authorization: Bearer {tenant_admin_token}

# Customer Data Resource
{
  "name": "customer-data",
  "display_name": "Customer Records", 
  "resource_type": "DATA",
  "resource_path": "/api/customers/*",
  "description": "Customer information and records",
  "metadata": {
    "sensitivity_level": "high",
    "data_classification": "PII"
  }
}

# Dashboard Resource  
{
  "name": "admin-dashboard",
  "display_name": "Admin Dashboard",
  "resource_type": "UI", 
  "resource_path": "/admin/*",
  "description": "Administrative dashboard and controls"
}

# Reports Resource
{
  "name": "financial-reports",
  "display_name": "Financial Reports",
  "resource_type": "DATA",
  "resource_path": "/api/reports/financial/*", 
  "description": "Financial reporting and analytics"
}
```

### **Step 6: Create Field Definitions** 

Define dynamic fields for your application data:

```bash
# Create field definitions for customer data
POST /api/v1/field-definitions/

# Customer Name Field
{
  "field_name": "customer_name",
  "display_name": "Customer Name",
  "field_type": "STRING",
  "resource_id": "{customer_data_resource_id}",
  "validation_rules": {
    "required": true,
    "max_length": 100
  },
  "default_visibility": "VISIBLE",
  "search_config": {
    "searchable": true,
    "search_weight": 1.0
  }
}

# Customer Salary Field (Sensitive)
{
  "field_name": "customer_salary", 
  "display_name": "Annual Salary",
  "field_type": "DECIMAL",
  "resource_id": "{customer_data_resource_id}",
  "validation_rules": {
    "min_value": 0,
    "max_value": 1000000
  },
  "default_visibility": "HIDDEN",  # Sensitive data
  "search_config": {
    "searchable": false
  }
}
```

### **Step 7: Create Business Roles**

Define roles that match your business structure:

```bash
# Create role hierarchy
POST /api/v1/roles/

# Super Admin Role
{
  "name": "super-admin", 
  "display_name": "Super Administrator",
  "description": "Full system access and administration",
  "role_type": "system",
  "priority": 100,
  "is_assignable": true,
  "parent_role_id": null
}

# Department Manager Role
{
  "name": "dept-manager",
  "display_name": "Department Manager", 
  "description": "Department-level management access",
  "role_type": "custom",
  "priority": 80,
  "is_assignable": true,
  "parent_role_id": null
}

# Employee Role  
{
  "name": "employee",
  "display_name": "Employee",
  "description": "Standard employee access",
  "role_type": "custom", 
  "priority": 50,
  "is_assignable": true,
  "parent_role_id": "{dept_manager_role_id}"  # Inherits from manager
}
```

### **Step 8: Define Permissions**

Create permissions for each resource and role combination:

```bash
# Create permissions for customer data
POST /api/v1/permissions/

# Super Admin - Full Customer Access
{
  "name": "customer-data-full-access",
  "resource_id": "{customer_data_resource_id}",
  "resource_type": "DATA", 
  "actions": ["CREATE", "READ", "UPDATE", "DELETE", "EXPORT"],
  "conditions": {},  # No restrictions
  "field_permissions": {
    "customer_name": "VISIBLE",
    "customer_email": "VISIBLE", 
    "customer_salary": "VISIBLE",  # Admin can see salary
    "customer_ssn": "VISIBLE"
  }
}

# Manager - Limited Customer Access
{
  "name": "customer-data-manager-access",
  "resource_id": "{customer_data_resource_id}",
  "resource_type": "DATA",
  "actions": ["READ", "UPDATE"],
  "conditions": {
    "department_match": true  # Only access customers in same department
  },
  "field_permissions": {
    "customer_name": "VISIBLE",
    "customer_email": "VISIBLE",
    "customer_salary": "HIDDEN",   # Managers cannot see salary
    "customer_ssn": "MASKED"       # SSN is masked
  }
}

# Employee - Read Only Access
{
  "name": "customer-data-employee-access", 
  "resource_id": "{customer_data_resource_id}",
  "resource_type": "DATA",
  "actions": ["READ"],
  "conditions": {
    "own_customers_only": true  # Only customers assigned to them
  },
  "field_permissions": {
    "customer_name": "VISIBLE",
    "customer_email": "VISIBLE", 
    "customer_salary": "HIDDEN",
    "customer_ssn": "HIDDEN"
  }
}
```

### **Step 9: Assign Permissions to Roles**

Link permissions to appropriate roles:

```bash
# Assign permissions to roles
POST /api/v1/permissions/{permission_id}/roles

# Super Admin gets full access
{
  "role_id": "{super_admin_role_id}",
  "assigned_by": "{admin_user_id}"
}

# Manager gets manager access  
{
  "role_id": "{dept_manager_role_id}",
  "assigned_by": "{admin_user_id}"
}

# Employee gets employee access
{
  "role_id": "{employee_role_id}", 
  "assigned_by": "{admin_user_id}"
}
```

---

## 👥 Phase 3: Organizational Structure

### **Step 10: Create Groups**

Set up organizational groups:

```bash
# Create department groups
POST /api/v1/groups/

# Sales Department
{
  "name": "sales-department",
  "display_name": "Sales Department",
  "description": "Sales team and management",
  "parent_group_id": null,
  "group_metadata": {
    "department_code": "SALES",
    "cost_center": "CC001"
  }
}

# Sales Managers Sub-group
{
  "name": "sales-managers", 
  "display_name": "Sales Managers",
  "description": "Sales management team",
  "parent_group_id": "{sales_department_id}",
  "group_metadata": {
    "management_level": "middle"
  }
}
```

### **Step 11: Assign Roles to Groups**

```bash
# Assign roles to groups
POST /api/v1/groups/{group_id}/roles

# Sales managers get manager role
{
  "role_id": "{dept_manager_role_id}",
  "assigned_by": "{admin_user_id}"
}
```

---

## 🧭 Phase 4: Menu and Navigation Setup

### **Step 12: Create Menu Structure**

Build navigation menus based on roles:

```bash
# Create menu items
POST /api/v1/navigation/menu-items/

# Main Dashboard Menu
{
  "name": "dashboard",
  "display_name": "Dashboard", 
  "icon": "dashboard",
  "url": "/dashboard",
  "order_index": 1,
  "is_visible": true,
  "parent_id": null,
  "resource_id": "{dashboard_resource_id}",
  "menu_metadata": {
    "description": "Main application dashboard"
  }
}

# Customer Management Menu (Restricted)
{
  "name": "customer-management",
  "display_name": "Customer Management",
  "icon": "people", 
  "url": "/customers",
  "order_index": 2,
  "is_visible": true,
  "parent_id": null,
  "resource_id": "{customer_data_resource_id}",
  "menu_metadata": {
    "requires_permission": "customer-data:READ"
  }
}

# Admin Menu (Super Restricted)
{
  "name": "admin-panel",
  "display_name": "Administration",
  "icon": "settings",
  "url": "/admin", 
  "order_index": 99,
  "is_visible": true,
  "parent_id": null,
  "resource_id": "{admin_dashboard_resource_id}",
  "menu_metadata": {
    "requires_role": "super-admin"
  }
}
```

---

## 👤 Phase 5: User Creation and Testing

### **Step 13: Create Test Users**

Create users to test your setup:

```bash
# Create manager user
POST /api/v1/users/

{
  "email": "manager@myawesome.com",
  "password": "manager_password",
  "first_name": "Jane", 
  "last_name": "Manager",
  "tenant_id": "{your_tenant_uuid}",
  "user_type": "standard",
  "attributes": {
    "department": "Sales",
    "hire_date": "2024-01-15"
  }
}

# Create employee user
{
  "email": "employee@myawesome.com", 
  "password": "employee_password",
  "first_name": "John",
  "last_name": "Employee", 
  "tenant_id": "{your_tenant_uuid}",
  "user_type": "standard",
  "attributes": {
    "department": "Sales",
    "hire_date": "2024-02-01"
  }
}
```

### **Step 14: Assign Users to Groups**

```bash
# Add manager to sales managers group
POST /api/v1/groups/{sales_managers_group_id}/users

{
  "user_id": "{manager_user_id}",
  "assigned_by": "{admin_user_id}",
  "assignment_metadata": {
    "assignment_date": "2024-01-15",
    "assignment_reason": "Department manager"
  }
}
```

### **Step 15: Test User Permissions**

Verify that permissions work correctly:

```bash
# Test manager login
POST /api/v1/auth/login
{
  "email": "manager@myawesome.com",
  "password": "manager_password",
  "tenant_id": "{your_tenant_uuid}"
}

# Test manager permissions
GET /api/v1/permissions/evaluate?user_id={manager_user_id}
Authorization: Bearer {manager_token}

# Test manager menu
GET /api/v1/navigation/menu/{manager_user_id}
Authorization: Bearer {manager_token}
```

**Expected Results**:
- Manager should see dashboard and customer management menus
- Manager should NOT see admin panel menu
- Manager should have READ/UPDATE permissions for customer data  
- Salary fields should be HIDDEN for manager

---

## 🔧 Phase 6: Application Integration

### **Step 16: Configure Your Application**

Set up your application with Sentinel credentials:

```bash
# Environment variables for your app
SENTINEL_BASE_URL=https://sentinel.yourcompany.com
SENTINEL_TENANT_ID={your_tenant_uuid}  
SENTINEL_API_KEY={your_api_key}
SENTINEL_JWT_SECRET={jwt_secret}
```

### **Step 17: Implement Authentication Flow**

```python
# Example: Python application setup
import requests
from functools import wraps

class SentinelAuth:
    def __init__(self, base_url, tenant_id):
        self.base_url = base_url
        self.tenant_id = tenant_id
    
    def login_user(self, email, password):
        """Authenticate user with Sentinel."""
        response = requests.post(f"{self.base_url}/api/v1/auth/login", json={
            "email": email,
            "password": password, 
            "tenant_id": self.tenant_id
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Login failed")
    
    def check_permission(self, user_id, resource, action, token):
        """Check user permission."""
        response = requests.post(
            f"{self.base_url}/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": user_id,
                "resource_id": resource, 
                "action": action
            }
        )
        
        return response.json().get("allowed", False)

# Usage in your app
sentinel = SentinelAuth(
    base_url=os.getenv("SENTINEL_BASE_URL"),
    tenant_id=os.getenv("SENTINEL_TENANT_ID")
)
```

### **Step 18: Test Integration**

```python
# Test the integration
def test_integration():
    # Test login
    login_result = sentinel.login_user("manager@myawesome.com", "manager_password")
    assert "access_token" in login_result
    
    # Test permission check
    can_read_customers = sentinel.check_permission(
        user_id=login_result["user"]["id"],
        resource="customer-data",
        action="READ", 
        token=login_result["access_token"]
    )
    assert can_read_customers == True
    
    # Test forbidden permission
    can_admin = sentinel.check_permission(
        user_id=login_result["user"]["id"],
        resource="admin-dashboard", 
        action="READ",
        token=login_result["access_token"]
    )
    assert can_admin == False

test_integration()
print("✅ Integration test passed!")
```

---

## ✅ Phase 7: Production Readiness

### **Step 19: Security Hardening**

```bash
# Update default passwords
PATCH /api/v1/users/{admin_user_id}
{
  "password": "new_super_secure_password_with_complexity"
}

# Enable additional security features
PATCH /api/v1/tenants/{tenant_id}
{
  "settings": {
    "password_policy": {
      "min_length": 12,
      "require_uppercase": true, 
      "require_numbers": true,
      "require_special_chars": true
    },
    "session_timeout": 1800,  # 30 minutes
    "max_login_attempts": 3,
    "require_mfa": false  # Enable in production
  }
}
```

### **Step 20: Monitoring Setup**

```bash
# Set up health checks
GET /api/v1/health
GET /api/v1/tenants/{tenant_id}/statistics
```

### **Step 21: Backup and Documentation**

```bash
# Export your configuration for backup
GET /api/v1/tenants/{tenant_id}/export
Authorization: Bearer {admin_token}

# This exports:
# - All roles and permissions
# - Group structure
# - Menu configuration  
# - Field definitions
# - Resource definitions
```

---

## 🎯 Validation Checklist

Before going to production, verify:

**Authentication & Authorization**:
- [ ] Super admin login works
- [ ] Tenant admin login works
- [ ] Test users can login
- [ ] Permission checks return correct results
- [ ] Unauthorized access is properly denied

**Menu & Navigation**:
- [ ] Different users see different menus based on roles
- [ ] Menu hierarchy is correct
- [ ] All menu links work
- [ ] Admin features hidden from regular users

**Field-Level Permissions**:
- [ ] Sensitive fields hidden from unauthorized users
- [ ] Field masking works (e.g., SSN shows as ***-**-1234)
- [ ] Field permissions align with business requirements

**Integration**:
- [ ] Your application successfully authenticates users
- [ ] Permission middleware blocks unauthorized access
- [ ] API responses respect field permissions
- [ ] Error handling works for Sentinel failures

**Performance**:
- [ ] Permission checks complete within acceptable time
- [ ] Menu loading is fast
- [ ] Caching is working (if implemented)
- [ ] System handles expected user load

---

## 🚀 Next Steps

1. **Deploy to Production**: Follow security best practices
2. **User Training**: Train admins on permission management
3. **Monitoring**: Set up logging and alerting
4. **Optimization**: Implement caching and performance improvements
5. **Scale**: Add more users, roles, and permissions as needed

---

## 🆘 Troubleshooting Common Issues

### **Issue: User Can't See Expected Menus**
```bash
# Debug user permissions
GET /api/v1/users/{user_id}/effective-permissions
GET /api/v1/navigation/menu/{user_id}/debug
```

### **Issue: Permission Denied Errors** 
```bash
# Check permission assignment
GET /api/v1/permissions/{permission_id}/roles
GET /api/v1/users/{user_id}/roles
```

### **Issue: Field Not Visible**
```bash  
# Check field definition and permissions
GET /api/v1/field-definitions/resource/{resource_id}
GET /api/v1/permissions/evaluate?user_id={user_id}&field_level=true
```

---

**Setup complete! 🎉 Your application is now secured with Sentinel RBAC. Continue with the [Developer Quickstart](./developer-quickstart.md) for implementation examples.**