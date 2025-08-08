# Database Schema Audit Report

## Overview

This report compares the SQL specification with the actual PostgreSQL database
for Modules 1-7 core functionality.

## Summary Statistics

- **SPEC_MATCH**: 55 findings
- **EXTRA_FIELD**: 19 findings
- **MISSING_FIELD**: 3 findings
- **TYPE_MISMATCH**: 42 findings
- **EXTRA_TABLE**: 3 findings
- **MISSING_TABLE**: 0 findings
- **Total Findings**: 122

## Modules 1-7 Core Tables

| Table | Status | Description |
|-------|--------|-------------|
| tenants | ⚠️ Modified | Module 2 - Tenant Management |
| users | ⚠️ Modified | Module 3 - User Management |
| roles | ⚠️ Modified | Module 4 - Role Management |
| user_roles | ⚠️ Modified | Module 4 - User-Role Assignments |
| groups | ⚠️ Modified | Module 5 - Group Management |
| user_groups | ⚠️ Modified | Module 5 - User-Group Assignments |
| group_roles | ⚠️ Modified | Module 5 - Group-Role Assignments |
| permissions | ⚠️ Modified | Module 6 - Permission Management |
| role_permissions | ⚠️ Modified | Module 6 - Role-Permission Assignments |
| resources | ⚠️ Modified | Module 7 - Resource Management |
| refresh_tokens | ⚠️ Modified | Module 1 - Authentication |
| token_blacklist | ⚠️ Modified | Module 1 - Authentication |

## Spec Match (55 findings)

### token_blacklist.user_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### token_blacklist.revoked_by
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### token_blacklist.reason
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### roles.is_active
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### roles.description
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### roles.tenant_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### roles.parent_role_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### roles.priority
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### roles.role_metadata
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### roles.created_by
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### roles.is_assignable
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### users.is_service_account
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### users.is_active
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### users.failed_login_count
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### users.login_count
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### users.attributes
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### users.tenant_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### users.preferences
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### refresh_tokens.user_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### refresh_tokens.device_info
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### tenants.is_active
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### tenants.settings
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### tenants.tenant_metadata
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### tenants.parent_tenant_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### permissions.conditions
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### permissions.is_active
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### permissions.field_permissions
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### permissions.tenant_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### permissions.resource_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### permissions.resource_path
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### resources.path
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### resources.is_active
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### resources.workflow_enabled
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### resources.parent_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### resources.attributes
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### resources.tenant_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### resources.workflow_config
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### user_groups.user_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### user_groups.added_by
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### user_groups.group_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### group_roles.group_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### group_roles.granted_by
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### group_roles.role_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### role_permissions.permission_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### role_permissions.granted_by
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### role_permissions.role_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### groups.is_active
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### groups.description
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### groups.group_metadata
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### groups.parent_group_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### groups.tenant_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### user_roles.user_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### user_roles.is_active
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### user_roles.granted_by
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

### user_roles.role_id
- **Status**: SPEC_MATCH
- **Description**: Field matches specification

## Extra Field (19 findings)

### token_blacklist.jti
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: character varying

### token_blacklist.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### roles.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### users.service_account_key
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: character varying

### users.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### users.avatar_file_id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: character varying

### users.avatar_url
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: character varying

### refresh_tokens.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### refresh_tokens.token_hash
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: character varying

### tenants.code
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: character varying

### tenants.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### permissions.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### resources.code
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: character varying

### resources.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### user_groups.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### group_roles.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### role_permissions.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### groups.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

### user_roles.id
- **Status**: EXTRA_FIELD
- **Description**: Field exists in database but not in spec
- **Actual Definition**: uuid

## Missing Field (3 findings)

### users.(is_service_account
- **Status**: MISSING_FIELD
- **Description**: Field defined in spec but missing from database
- **Spec Definition**: =

### tenants.(type
- **Status**: MISSING_FIELD
- **Description**: Field defined in spec but missing from database
- **Spec Definition**: =

### permissions.(resource_id
- **Status**: MISSING_FIELD
- **Description**: Field defined in spec but missing from database
- **Spec Definition**: IS

## Type Mismatch (42 findings)

### token_blacklist.expires_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### token_blacklist.revoked_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### token_blacklist.token_type
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(50), actual=varchar
- **Spec Definition**: VARCHAR(50)
- **Actual Definition**: character varying

### roles.type
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=sentinel.role_type, actual=user-defined
- **Spec Definition**: sentinel.role_type
- **Actual Definition**: USER-DEFINED

### roles.updated_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### roles.name
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(100), actual=varchar
- **Spec Definition**: VARCHAR(100)
- **Actual Definition**: character varying

### roles.display_name
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(255), actual=varchar
- **Spec Definition**: VARCHAR(255)
- **Actual Definition**: character varying

### roles.created_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### users.email
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(255), actual=varchar
- **Spec Definition**: VARCHAR(255)
- **Actual Definition**: character varying

### users.updated_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### users.username
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(100), actual=varchar
- **Spec Definition**: VARCHAR(100)
- **Actual Definition**: character varying

### users.created_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### users.locked_until
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### users.password_hash
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(255),, actual=varchar
- **Spec Definition**: VARCHAR(255),
- **Actual Definition**: character varying

### users.last_login
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### refresh_tokens.expires_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### refresh_tokens.last_used_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### refresh_tokens.created_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### tenants.type
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=sentinel.tenant_type, actual=user-defined
- **Spec Definition**: sentinel.tenant_type
- **Actual Definition**: USER-DEFINED

### tenants.updated_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### tenants.name
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(255), actual=varchar
- **Spec Definition**: VARCHAR(255)
- **Actual Definition**: character varying

### tenants.features
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=text, actual=array
- **Spec Definition**: TEXT[]
- **Actual Definition**: ARRAY

### tenants.created_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### tenants.isolation_mode
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=sentinel.isolation_mode, actual=user-defined
- **Spec Definition**: sentinel.isolation_mode
- **Actual Definition**: USER-DEFINED

### permissions.updated_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### permissions.name
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(255), actual=varchar
- **Spec Definition**: VARCHAR(255)
- **Actual Definition**: character varying

### permissions.created_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### permissions.resource_type
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=sentinel.resource_type, actual=user-defined
- **Spec Definition**: sentinel.resource_type
- **Actual Definition**: USER-DEFINED

### permissions.actions
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=sentinel.permission_action[], actual=array
- **Spec Definition**: sentinel.permission_action[]
- **Actual Definition**: ARRAY

### resources.type
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=sentinel.resource_type, actual=user-defined
- **Spec Definition**: sentinel.resource_type
- **Actual Definition**: USER-DEFINED

### resources.updated_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### resources.name
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(255), actual=varchar
- **Spec Definition**: VARCHAR(255)
- **Actual Definition**: character varying

### resources.created_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### user_groups.added_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### group_roles.granted_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### role_permissions.granted_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### groups.updated_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### groups.name
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(100), actual=varchar
- **Spec Definition**: VARCHAR(100)
- **Actual Definition**: character varying

### groups.display_name
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=varchar(255), actual=varchar
- **Spec Definition**: VARCHAR(255)
- **Actual Definition**: character varying

### groups.created_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### user_roles.expires_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

### user_roles.granted_at
- **Status**: TYPE_MISMATCH
- **Description**: Data type mismatch: spec=timestamp, actual=timestamptz
- **Spec Definition**: TIMESTAMP
- **Actual Definition**: timestamp with time zone

## Extra Table (3 findings)

### alembic_version
- **Status**: EXTRA_TABLE
- **Description**: Table exists in database but not in Modules 1-7 spec

### schema_version
- **Status**: EXTRA_TABLE
- **Description**: Table exists in database but not in Modules 1-7 spec

### permission_cache
- **Status**: EXTRA_TABLE
- **Description**: Table exists in database but not in Modules 1-7 spec

