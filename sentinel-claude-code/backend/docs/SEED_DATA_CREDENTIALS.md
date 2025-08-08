# Seed Data Credentials Documentation

This document provides comprehensive information about all test accounts and credentials created during the database seeding process for the Sentinel RBAC system.

## Database Configuration

- **Database**: `sentinel_dev`
- **Host**: `localhost`
- **User**: `postgres`
- **Schema**: `sentinel`
- **Seeding Date**: August 8, 2025

## Superadmin Account

The platform superadmin account has full system access across all tenants.

| Field | Value |
|-------|-------|
| **Email** | admin@sentinel.com |
| **Password** | admin123 |
| **Username** | admin |
| **Tenant** | PLATFORM |
| **Tenant Code** | PLATFORM |
| **Display Name** | Platform Administrator |
| **Role** | superadmin |
| **Access Level** | Full system access |

## Logistics Company Tenants

### 1. Maritime Port Operations (MARITIME)

**Tenant Information:**
- **Name**: Maritime Port Operations
- **Code**: MARITIME
- **Industry**: Maritime Logistics
- **Headquarters**: Singapore
- **Domain**: maritime.logistics.com

**Users:**
| Name | Email | Username | Role | Description |
|------|-------|----------|------|-------------|
| Sarah Thompson | port.manager@maritime.com | port.manager | Manager | Port management and operations oversight |
| Marcus Chen | vessel.coord@maritime.com | vessel.coord | Coordinator | Vessel scheduling and coordination |
| Ahmed Hassan | customs.officer@maritime.com | customs.officer | Officer | Customs clearance and compliance |
| Jose Rodriguez | dock.worker@maritime.com | dock.worker | Worker | Dock operations and cargo handling |

### 2. AirCargo Express (AIRCARGO)

**Tenant Information:**
- **Name**: AirCargo Express
- **Code**: AIRCARGO
- **Industry**: Air Cargo
- **Headquarters**: Frankfurt
- **Domain**: aircargo.express.com

**Users:**
| Name | Email | Username | Role | Description |
|------|-------|----------|------|-------------|
| Lisa Wagner | ops.manager@aircargo.com | ops.manager | Manager | Air cargo operations management |
| David Kim | flight.coord@aircargo.com | flight.coord | Coordinator | Flight coordination and scheduling |
| Emma Johnson | security.inspector@aircargo.com | security.inspector | Inspector | Security screening and compliance |
| Carlos Mendez | cargo.handler@aircargo.com | cargo.handler | Handler | Cargo handling and loading operations |

### 3. GroundLink Logistics (GROUNDLINK)

**Tenant Information:**
- **Name**: GroundLink Logistics
- **Code**: GROUNDLINK
- **Industry**: Ground Logistics
- **Headquarters**: Memphis
- **Domain**: groundlink.logistics.com

**Users:**
| Name | Email | Username | Role | Description |
|------|-------|----------|------|-------------|
| Michael O'Connor | warehouse.mgr@groundlink.com | warehouse.mgr | Manager | Warehouse management and operations |
| Priya Patel | logistics.coord@groundlink.com | logistics.coord | Coordinator | Logistics coordination and planning |
| Jennifer Lee | compliance.officer@groundlink.com | compliance.officer | Officer | Compliance oversight and documentation |
| Robert Johnson | warehouse.associate@groundlink.com | warehouse.associate | Associate | Warehouse operations and order fulfillment |

## Common Passwords

All logistics company users share the same password for testing purposes:

**Password**: `LogisticsTest2024!`

## Account Attributes

All user accounts include the following additional attributes stored in the `attributes` JSON field:

- `first_name`: User's first name
- `last_name`: User's last name  
- `display_name`: Full display name
- `email_verified`: true
- `role`: User's role within the organization
- `test_account`: true (indicates this is a test account)
- `default_password`: The password used for this account

## Database Statistics

After seeding completion:
- **Total Tenants**: 4 (1 Platform + 3 Logistics companies)
- **Total Users**: 13 (1 Superadmin + 12 Logistics users)
- **User Distribution**: 4 users per logistics tenant

## Testing Scenarios

This seed data enables testing of the following RBAC scenarios:

### 1. Cross-Tenant Isolation
- Verify users can only access resources within their tenant
- Test that MARITIME users cannot access AIRCARGO or GROUNDLINK resources

### 2. Role-Based Access Patterns
- **Managers**: Should have highest access within their tenant
- **Coordinators**: Operational access with some management capabilities
- **Officers**: Compliance and security-focused access
- **Workers/Handlers/Associates**: Basic operational access

### 3. Superadmin Capabilities
- Platform admin should have access across all tenants
- Can manage tenant settings and cross-tenant resources

## Security Considerations

⚠️ **Important Security Notes:**

1. **Test Environment Only**: These credentials are for development and testing purposes only
2. **Password Complexity**: All passwords meet minimum security requirements
3. **Account Expiration**: Consider implementing account expiration for test accounts
4. **Regular Rotation**: Rotate passwords regularly in non-production environments
5. **Access Monitoring**: Monitor access patterns during testing

## Usage Instructions

### Login Testing
1. Navigate to the authentication endpoint
2. Use any email/password combination from the tables above
3. Verify tenant isolation and role-based access

### API Testing
Use these credentials for testing API endpoints:
```bash
# Example login request
curl -X POST /api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "port.manager@maritime.com",
    "password": "LogisticsTest2024!"
  }'
```

### Database Queries
Direct database access for verification:
```sql
-- List all users with their tenant information
SELECT 
    u.email,
    u.attributes->>'display_name' as name,
    u.attributes->>'role' as role,
    t.name as tenant_name,
    t.code as tenant_code
FROM sentinel.users u
JOIN sentinel.tenants t ON u.tenant_id = t.id
ORDER BY t.code, u.email;
```

## Maintenance

### Cleaning Test Data
To remove all test data while preserving the superadmin:
```bash
cd backend
export DATABASE_URL="postgresql://postgres:svr967567@localhost/sentinel_dev"
venv/bin/python scripts/cleanup_database.py
```

### Re-seeding Data
To recreate the logistics test data:
```bash
cd backend
export DATABASE_URL="postgresql://postgres:svr967567@localhost/sentinel_dev"
venv/bin/python scripts/seed_simple_logistics.py
```

## Contact Information

For questions about this seed data or to request additional test scenarios, contact the development team.

---

**Generated**: August 8, 2025  
**Version**: 1.0.0  
**Database Schema**: Implementation v2.0  
**Last Updated**: After successful logistics industry data seeding