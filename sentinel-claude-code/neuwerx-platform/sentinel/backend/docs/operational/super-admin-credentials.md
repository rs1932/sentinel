# Super Admin Credentials Documentation

## Current Super Admin Account

The following super admin account has been created for the Sentinel Platform:

### Credentials
- **Email**: `admin@sentinel.com`
- **Password**: `admin123`
- **Tenant**: `PLATFORM`
- **Tenant ID**: `00000000-0000-0000-0000-000000000000`

### Authentication
To authenticate as super admin, use the `/auth/login` endpoint with:
```json
{
  "email": "admin@sentinel.com",
  "password": "admin123",
  "tenant_code": "PLATFORM"
}
```

### Token Scopes
When authenticated, the super admin receives the following 21 scopes:
- `user:profile` - Access to own profile
- `platform:admin` - **Global platform administration**
- `tenant:read`, `tenant:write`, `tenant:admin`, `tenant:global` - **Global tenant management**
- `user:read`, `user:write`, `user:admin`, `user:global` - **Global user management**
- `service_account:read`, `service_account:write`, `service_account:admin`, `service_account:global` - **Global service account management**
- `role:read`, `role:write`, `role:admin`, `role:global` - **Global role management**
- `system:admin` - **System-level administration**
- `audit:read`, `audit:write` - **Audit log access**

**Note**: The `:global` scopes are exclusive to super admin users and provide cross-tenant access.

## Security Notes

### Password Policy
- Current password is simple for development purposes: `admin123`
- **For production**: Change to a strong password meeting security requirements
- Consider implementing MFA for super admin accounts

### Access Control
- Super admin has unrestricted access across ALL tenants
- Can create, modify, and delete any resource in the system
- Has audit trail access for compliance and monitoring

### Best Practices
1. **Change default credentials immediately in production**
2. **Use strong, unique passwords**
3. **Enable audit logging for super admin actions**
4. **Limit super admin access to necessary personnel only**
5. **Consider using service accounts for automated tasks**

## Creating Additional Super Admins

Use the provided script to create additional super admin accounts:

```bash
# From the backend directory with virtual environment activated
./venv/bin/python docs/operational/create-super-admin.py \
  --email "new-admin@example.com" \
  --password "SecurePassword123!" \
  --tenant-code "PLATFORM"
```

## Tenant Structure

### PLATFORM Tenant
- **ID**: `00000000-0000-0000-0000-000000000000`
- **Code**: `PLATFORM`
- **Name**: `Platform Administration`
- **Purpose**: System-level administration and super admin users
- **Special Properties**: Users on this tenant receive enhanced global permissions

### Regular Tenants
- Have their own UUID identifiers
- Users are scoped to their specific tenant
- Tenant admins have admin rights within their tenant only
- Cannot access other tenants' data or users

## Troubleshooting

### Login Issues
1. Verify tenant code is exactly `PLATFORM` (case-sensitive)
2. Check email format and spelling
3. Ensure database connection is working
4. Verify user exists in the database

### Permission Issues
1. Confirm user is on PLATFORM tenant
2. Check JWT token contains global scopes
3. Verify authentication service is running latest code
4. Check for any blacklisted tokens

### Database Queries
To verify super admin exists:
```sql
SELECT u.id, u.email, t.code, t.name 
FROM sentinel.users u 
JOIN sentinel.tenants t ON u.tenant_id = t.id 
WHERE t.code = 'PLATFORM' AND u.email = 'admin@sentinel.com';
```