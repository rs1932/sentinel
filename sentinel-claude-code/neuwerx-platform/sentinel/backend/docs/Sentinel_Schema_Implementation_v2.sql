-- =================================================================
-- Sentinel Platform - Implementation Standard Database Schema v2.0
--
-- This script reflects the ACTUAL implemented database schema
-- based on the audit performed on 2025-08-08.
--
-- Changes from v1.0:
-- - Added explicit UUID primary keys to all core tables
-- - Added business code fields (tenants.code, resources.code)
-- - Enhanced user profile fields (avatar_url, avatar_file_id)
-- - Added secure token fields (token_hash, jti)
-- - Standardized audit fields across all tables
-- - Upgraded to timezone-aware timestamps
-- - Added performance optimization tables (permission_cache)
-- =================================================================

-- Create the schema to house all platform objects
CREATE SCHEMA IF NOT EXISTS sentinel;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =====================================================
-- ENUM TYPES
-- =====================================================

CREATE TYPE sentinel.tenant_type AS ENUM ('root', 'sub_tenant');
CREATE TYPE sentinel.isolation_mode AS ENUM ('shared', 'dedicated');
CREATE TYPE sentinel.role_type AS ENUM ('system', 'custom');
CREATE TYPE sentinel.resource_type AS ENUM ('product_family', 'app', 'capability', 'service', 'entity', 'page', 'api');
CREATE TYPE sentinel.permission_action AS ENUM ('create', 'read', 'update', 'delete', 'execute', 'approve', 'reject');
CREATE TYPE sentinel.field_permission AS ENUM ('read', 'write', 'hidden');
CREATE TYPE sentinel.actor_type AS ENUM ('user', 'service_account', 'system');
CREATE TYPE sentinel.token_status AS ENUM ('active', 'revoked', 'expired');
CREATE TYPE sentinel.workflow_state AS ENUM ('draft', 'planning', 'scheduled', 'in_progress', 'completed', 'cancelled');

-- =====================================================
-- CORE TABLES - MODULES 1-7 (Implementation Standard)
-- =====================================================

-- Tenants table (Module 2 - Tenant Management)
CREATE TABLE sentinel.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL, -- Business identifier like 'GSC-001' [IMPLEMENTATION ADDED]
    name VARCHAR(255) NOT NULL,
    type sentinel.tenant_type NOT NULL DEFAULT 'root',
    parent_tenant_id UUID REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    isolation_mode sentinel.isolation_mode NOT NULL DEFAULT 'shared',
    settings JSONB DEFAULT '{}',
    features TEXT[] DEFAULT '{}', -- Enabled features for this tenant
    tenant_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_parent_tenant CHECK (
        (type = 'root' AND parent_tenant_id IS NULL) OR
        (type = 'sub_tenant' AND parent_tenant_id IS NOT NULL)
    ),
    CONSTRAINT unique_tenant_code UNIQUE(code)
);

-- Users table (Module 3 - User Management)
CREATE TABLE sentinel.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    password_hash VARCHAR(255), -- NULL for SSO users
    is_service_account BOOLEAN DEFAULT false,
    service_account_key VARCHAR(255) UNIQUE, -- For M2M authentication [IMPLEMENTATION ADDED]
    avatar_url VARCHAR(512), -- User profile image URL [IMPLEMENTATION ADDED]
    avatar_file_id VARCHAR(255), -- File storage reference [IMPLEMENTATION ADDED]
    attributes JSONB DEFAULT '{}', -- User attributes for ABAC
    preferences JSONB DEFAULT '{}', -- UI preferences, etc.
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    failed_login_count INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_email_per_tenant UNIQUE(tenant_id, email),
    CONSTRAINT check_service_account CHECK (
        (is_service_account = true AND service_account_key IS NOT NULL AND password_hash IS NULL) OR
        (is_service_account = false)
    )
);

-- Roles table (Module 4 - Role Management)
CREATE TABLE sentinel.roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    type sentinel.role_type NOT NULL DEFAULT 'custom',
    parent_role_id UUID REFERENCES sentinel.roles(id) ON DELETE SET NULL,
    is_assignable BOOLEAN DEFAULT true, -- Can be assigned to users
    priority INTEGER DEFAULT 0, -- For role conflict resolution
    role_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES sentinel.users(id),
    CONSTRAINT unique_role_name_per_tenant UNIQUE(tenant_id, name)
);

-- Groups table (Module 5 - Group Management)
CREATE TABLE sentinel.groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    parent_group_id UUID REFERENCES sentinel.groups(id) ON DELETE CASCADE,
    group_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_group_name_per_tenant UNIQUE(tenant_id, name)
);

-- Resource definitions table (Module 7 - Resource Management)
CREATE TABLE sentinel.resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL, -- Business identifier within type [IMPLEMENTATION ADDED]
    type sentinel.resource_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES sentinel.resources(id) ON DELETE CASCADE,
    path TEXT, -- Materialized path for efficient hierarchy queries
    attributes JSONB DEFAULT '{}', -- Resource-specific attributes
    workflow_enabled BOOLEAN DEFAULT false,
    workflow_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_resource_code UNIQUE(tenant_id, type, code)
);

-- Permissions table (Module 6 - Permission Management)
CREATE TABLE sentinel.permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    resource_type sentinel.resource_type NOT NULL,
    resource_id UUID REFERENCES sentinel.resources(id) ON DELETE CASCADE,
    resource_path TEXT, -- For wildcard matching like 'fleet/*'
    actions sentinel.permission_action[] NOT NULL,
    conditions JSONB DEFAULT '{}', -- ABAC conditions
    field_permissions JSONB DEFAULT '{}', -- Field-level permissions
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_resource_specification CHECK (
        (resource_id IS NOT NULL AND resource_path IS NULL) OR
        (resource_id IS NULL AND resource_path IS NOT NULL)
    )
);

-- =====================================================
-- RELATIONSHIP TABLES - MODULES 4-6 (Implementation Standard)
-- =====================================================

-- User-Role assignments (Module 4 - User-Role Assignments)
CREATE TABLE sentinel.user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES sentinel.roles(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES sentinel.users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    CONSTRAINT unique_user_role UNIQUE(user_id, role_id)
);

-- User-Group memberships (Module 5 - User-Group Assignments)
CREATE TABLE sentinel.user_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES sentinel.groups(id) ON DELETE CASCADE,
    added_by UUID REFERENCES sentinel.users(id),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    CONSTRAINT unique_user_group UNIQUE(user_id, group_id)
);

-- Group-Role assignments (Module 5 - Group-Role Assignments)
CREATE TABLE sentinel.group_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES sentinel.groups(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES sentinel.roles(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES sentinel.users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    CONSTRAINT unique_group_role UNIQUE(group_id, role_id)
);

-- Role-Permission assignments (Module 6 - Role-Permission Assignments)
CREATE TABLE sentinel.role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES sentinel.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES sentinel.permissions(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES sentinel.users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    CONSTRAINT unique_role_permission UNIQUE(role_id, permission_id)
);

-- =====================================================
-- SESSION & TOKEN MANAGEMENT - MODULE 1 (Implementation Standard)
-- =====================================================

-- JWT token blacklist (for revoked tokens)
CREATE TABLE sentinel.token_blacklist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jti VARCHAR(255) UNIQUE NOT NULL, -- JWT ID [IMPLEMENTATION ADDED]
    user_id UUID REFERENCES sentinel.users(id) ON DELETE CASCADE,
    token_type VARCHAR(50) NOT NULL, -- 'access', 'refresh'
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_by UUID REFERENCES sentinel.users(id),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- [AUDIT FIELD ADDED]
);

-- Refresh tokens (for token rotation)
CREATE TABLE sentinel.refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL, -- [IMPLEMENTATION ADDED - Secure token storage]
    device_info JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- [AUDIT FIELD ADDED]
);

-- =====================================================
-- PERFORMANCE OPTIMIZATION TABLES (Implementation Added)
-- =====================================================

-- Permission check cache (RBAC performance optimization)
CREATE TABLE sentinel.permission_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(500) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    resource_type sentinel.resource_type NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    action sentinel.permission_action NOT NULL,
    result BOOLEAN NOT NULL,
    field_permissions JSONB DEFAULT '{}',
    conditions_evaluated JSONB DEFAULT '{}',
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- [AUDIT FIELD ADDED]
);

-- =====================================================
-- AUDIT & COMPLIANCE (Core Implementation)
-- =====================================================

-- Comprehensive audit log
CREATE TABLE sentinel.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES sentinel.users(id),
    actor_type sentinel.actor_type NOT NULL,
    actor_details JSONB DEFAULT '{}', -- IP address, user agent, etc.
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    resource_details JSONB DEFAULT '{}',
    changes JSONB DEFAULT '{}', -- Before/after values
    result VARCHAR(50), -- 'success', 'failure', 'denied'
    error_details TEXT,
    audit_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- NAVIGATION & UI CUSTOMIZATION (Implementation Added)
-- =====================================================

-- Menu items definition
CREATE TABLE sentinel.menu_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES sentinel.tenants(id) ON DELETE CASCADE, -- NULL for system-wide
    parent_id UUID REFERENCES sentinel.menu_items(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    icon VARCHAR(50),
    url VARCHAR(500),
    resource_id UUID REFERENCES sentinel.resources(id) ON DELETE SET NULL,
    required_permission VARCHAR(255), -- Simple permission check
    display_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT true,
    menu_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User menu customizations
CREATE TABLE sentinel.user_menu_customizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES sentinel.menu_items(id) ON DELETE CASCADE,
    is_hidden BOOLEAN DEFAULT false,
    custom_order INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    CONSTRAINT unique_user_menu UNIQUE(user_id, menu_item_id)
);

-- =====================================================
-- APPROVAL CHAINS EXTENSION (Implementation Added)
-- =====================================================

-- Access request tracking
CREATE TABLE sentinel.access_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requester_id UUID NOT NULL REFERENCES sentinel.users(id),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id),
    request_type VARCHAR(50) NOT NULL, -- 'role', 'permission', 'resource_access'
    request_details JSONB NOT NULL, -- What is being requested
    justification TEXT,
    expires_at TIMESTAMP WITH TIME ZONE, -- Temporary access
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, denied, expired
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Approval chain configuration
CREATE TABLE sentinel.approval_chains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id),
    name VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100), -- 'terminal', 'port', 'vessel_class'
    resource_pattern VARCHAR(500), -- Pattern matching for resources
    approval_levels JSONB NOT NULL, -- Array of approval levels
    auto_approve_conditions JSONB, -- Conditions for automatic approval
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- [AUDIT FIELD ADDED]
);

-- Individual approval records
CREATE TABLE sentinel.approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL REFERENCES sentinel.access_requests(id),
    approver_id UUID NOT NULL REFERENCES sentinel.users(id),
    approval_level INTEGER NOT NULL,
    decision VARCHAR(50), -- 'approved', 'denied', 'escalated'
    comments TEXT,
    decided_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- [AUDIT FIELD ADDED]
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- [AUDIT FIELD ADDED]
);

-- Password reset tokens (Session Management Extension)
CREATE TABLE sentinel.password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    attempts INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true
);

-- Active sessions tracking (Session Management Extension)
CREATE TABLE sentinel.active_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    session_token_hash VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE (Implementation Standard)
-- =====================================================

-- Tenant indexes
CREATE INDEX idx_tenants_parent ON sentinel.tenants(parent_tenant_id) WHERE parent_tenant_id IS NOT NULL;
CREATE INDEX idx_tenants_active ON sentinel.tenants(is_active) WHERE is_active = true;
CREATE INDEX idx_tenants_code ON sentinel.tenants(code);

-- User indexes
CREATE INDEX idx_users_tenant ON sentinel.users(tenant_id);
CREATE INDEX idx_users_email ON sentinel.users(email);
CREATE INDEX idx_users_service_account ON sentinel.users(service_account_key) WHERE service_account_key IS NOT NULL;
CREATE INDEX idx_users_active_tenant ON sentinel.users(tenant_id, is_active) WHERE is_active = true;

-- Role indexes
CREATE INDEX idx_roles_tenant ON sentinel.roles(tenant_id);
CREATE INDEX idx_roles_parent ON sentinel.roles(parent_role_id) WHERE parent_role_id IS NOT NULL;
CREATE INDEX idx_roles_type ON sentinel.roles(type);

-- Group indexes
CREATE INDEX idx_groups_tenant ON sentinel.groups(tenant_id);
CREATE INDEX idx_groups_parent ON sentinel.groups(parent_group_id) WHERE parent_group_id IS NOT NULL;

-- Resource indexes
CREATE INDEX idx_resources_tenant ON sentinel.resources(tenant_id);
CREATE INDEX idx_resources_type ON sentinel.resources(tenant_id, type);
CREATE INDEX idx_resources_parent ON sentinel.resources(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX idx_resources_path ON sentinel.resources USING gin(path);
CREATE INDEX idx_resources_code ON sentinel.resources(tenant_id, code);

-- Permission indexes
CREATE INDEX idx_permissions_tenant ON sentinel.permissions(tenant_id);
CREATE INDEX idx_permissions_resource ON sentinel.permissions(resource_id) WHERE resource_id IS NOT NULL;
CREATE INDEX idx_permissions_resource_type ON sentinel.permissions(resource_type);
CREATE INDEX idx_permissions_resource_path ON sentinel.permissions USING gin(resource_path);

-- Relationship indexes
CREATE INDEX idx_user_roles_user ON sentinel.user_roles(user_id);
CREATE INDEX idx_user_roles_role ON sentinel.user_roles(role_id);
CREATE INDEX idx_user_groups_user ON sentinel.user_groups(user_id);
CREATE INDEX idx_user_groups_group ON sentinel.user_groups(group_id);
CREATE INDEX idx_group_roles_group ON sentinel.group_roles(group_id);
CREATE INDEX idx_group_roles_role ON sentinel.group_roles(role_id);
CREATE INDEX idx_role_permissions_role ON sentinel.role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission ON sentinel.role_permissions(permission_id);

-- Audit indexes
CREATE INDEX idx_audit_tenant_created ON sentinel.audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_actor ON sentinel.audit_logs(actor_id) WHERE actor_id IS NOT NULL;
CREATE INDEX idx_audit_resource ON sentinel.audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_action ON sentinel.audit_logs(action);

-- Token indexes
CREATE INDEX idx_token_blacklist_expires ON sentinel.token_blacklist(expires_at);
CREATE INDEX idx_token_blacklist_jti ON sentinel.token_blacklist(jti);
CREATE INDEX idx_refresh_tokens_user ON sentinel.refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON sentinel.refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_hash ON sentinel.refresh_tokens(token_hash);

-- Permission cache indexes
CREATE INDEX idx_perm_cache_user ON sentinel.permission_cache(user_id);
CREATE INDEX idx_perm_cache_expires ON sentinel.permission_cache(expires_at);
CREATE INDEX idx_perm_cache_key ON sentinel.permission_cache(cache_key);

-- Approval chain indexes
CREATE INDEX idx_access_requests_requester ON sentinel.access_requests(requester_id);
CREATE INDEX idx_access_requests_status ON sentinel.access_requests(status) WHERE status = 'pending';
CREATE INDEX idx_approvals_request ON sentinel.approvals(request_id);

-- Session management indexes
CREATE INDEX idx_password_reset_tokens_user ON sentinel.password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_tokens_hash ON sentinel.password_reset_tokens(token_hash);
CREATE INDEX idx_password_reset_tokens_expires ON sentinel.password_reset_tokens(expires_at);
CREATE INDEX idx_active_sessions_user ON sentinel.active_sessions(user_id);
CREATE INDEX idx_active_sessions_expires ON sentinel.active_sessions(expires_at);

-- =====================================================
-- FUNCTIONS AND TRIGGERS (Implementation Standard)  
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION sentinel.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to ALL tables with updated_at columns
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON sentinel.tenants
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON sentinel.users
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON sentinel.roles
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON sentinel.groups
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON sentinel.resources
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_permissions_updated_at BEFORE UPDATE ON sentinel.permissions
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

-- Relationship table triggers [IMPLEMENTATION ADDED]
CREATE TRIGGER update_user_roles_updated_at BEFORE UPDATE ON sentinel.user_roles
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_user_groups_updated_at BEFORE UPDATE ON sentinel.user_groups
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_group_roles_updated_at BEFORE UPDATE ON sentinel.group_roles
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_role_permissions_updated_at BEFORE UPDATE ON sentinel.role_permissions
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

-- Token and session table triggers [IMPLEMENTATION ADDED]
CREATE TRIGGER update_token_blacklist_updated_at BEFORE UPDATE ON sentinel.token_blacklist
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_refresh_tokens_updated_at BEFORE UPDATE ON sentinel.refresh_tokens
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_permission_cache_updated_at BEFORE UPDATE ON sentinel.permission_cache
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

-- UI and approval table triggers [IMPLEMENTATION ADDED]
CREATE TRIGGER update_menu_items_updated_at BEFORE UPDATE ON sentinel.menu_items
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_user_menu_customizations_updated_at BEFORE UPDATE ON sentinel.user_menu_customizations
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_access_requests_updated_at BEFORE UPDATE ON sentinel.access_requests
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_approval_chains_updated_at BEFORE UPDATE ON sentinel.approval_chains
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_approvals_updated_at BEFORE UPDATE ON sentinel.approvals
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_password_reset_tokens_updated_at BEFORE UPDATE ON sentinel.password_reset_tokens
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

-- Materialized path update for resources
CREATE OR REPLACE FUNCTION sentinel.update_resource_path()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.path = '/' || NEW.id::text || '/';
    ELSE
        SELECT r.path || NEW.id::text || '/'
        INTO NEW.path
        FROM sentinel.resources r
        WHERE r.id = NEW.parent_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_resource_path_trigger
    BEFORE INSERT OR UPDATE OF parent_id ON sentinel.resources
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_resource_path();

-- Clean expired tokens periodically
CREATE OR REPLACE FUNCTION sentinel.clean_expired_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM sentinel.token_blacklist WHERE expires_at < CURRENT_TIMESTAMP;
    DELETE FROM sentinel.refresh_tokens WHERE expires_at < CURRENT_TIMESTAMP;
    DELETE FROM sentinel.permission_cache WHERE expires_at < CURRENT_TIMESTAMP;
    DELETE FROM sentinel.password_reset_tokens WHERE expires_at < CURRENT_TIMESTAMP;
    DELETE FROM sentinel.active_sessions WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ language 'plpgsql';

-- =====================================================
-- USEFUL VIEWS (Implementation Standard)
-- =====================================================

-- User effective permissions view
CREATE OR REPLACE VIEW sentinel.user_effective_permissions AS
WITH RECURSIVE role_hierarchy AS (
    -- Direct roles
    SELECT ur.user_id, ur.role_id, r.tenant_id
    FROM sentinel.user_roles ur
    JOIN sentinel.roles r ON ur.role_id = r.id
    WHERE ur.is_active = true

    UNION

    -- Roles from groups
    SELECT ug.user_id, gr.role_id, r.tenant_id
    FROM sentinel.user_groups ug
    JOIN sentinel.group_roles gr ON ug.group_id = gr.group_id
    JOIN sentinel.roles r ON gr.role_id = r.id

    UNION

    -- Parent roles (inheritance)
    SELECT rh.user_id, r.parent_role_id, r.tenant_id
    FROM role_hierarchy rh
    JOIN sentinel.roles r ON rh.role_id = r.id
    WHERE r.parent_role_id IS NOT NULL
)
SELECT DISTINCT
    rh.user_id,
    rh.tenant_id,
    p.*
FROM role_hierarchy rh
JOIN sentinel.role_permissions rp ON rh.role_id = rp.role_id
JOIN sentinel.permissions p ON rp.permission_id = p.id
WHERE p.is_active = true;

-- Active sessions view
CREATE OR REPLACE VIEW sentinel.active_sessions_view AS
SELECT
    u.id as user_id,
    u.email,
    u.tenant_id,
    t.name as tenant_name,
    u.last_login,
    u.is_service_account,
    COUNT(DISTINCT rt.id) as active_refresh_tokens,
    COUNT(DISTINCT ast.id) as active_sessions
FROM sentinel.users u
JOIN sentinel.tenants t ON u.tenant_id = t.id
LEFT JOIN sentinel.refresh_tokens rt ON u.id = rt.user_id AND rt.expires_at > CURRENT_TIMESTAMP
LEFT JOIN sentinel.active_sessions ast ON u.id = ast.user_id AND ast.expires_at > CURRENT_TIMESTAMP
WHERE u.is_active = true
GROUP BY u.id, u.email, u.tenant_id, t.name, u.last_login, u.is_service_account;

-- =====================================================
-- INITIAL SYSTEM DATA (Implementation Standard)
-- =====================================================

-- Insert platform tenant
INSERT INTO sentinel.tenants (id, name, code, type, isolation_mode, settings)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'Sentinel Platform',
    'PLATFORM',
    'root',
    'dedicated',
    '{"is_platform_tenant": true}'
) ON CONFLICT (id) DO NOTHING;

-- Insert system roles
INSERT INTO sentinel.roles (tenant_id, name, display_name, description, type, priority)
VALUES
    ('00000000-0000-0000-0000-000000000000', 'super_admin', 'Super Administrator', 'Platform-wide administrator with full access', 'system', 1000),
    ('00000000-0000-0000-0000-000000000000', 'tenant_admin', 'Tenant Administrator', 'Tenant-level administrator', 'system', 900),
    ('00000000-0000-0000-0000-000000000000', 'user_manager', 'User Manager', 'Can manage users and roles within tenant', 'system', 800),
    ('00000000-0000-0000-0000-000000000000', 'viewer', 'Viewer', 'Read-only access to assigned resources', 'system', 100)
ON CONFLICT (tenant_id, name) DO NOTHING;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON SCHEMA sentinel IS 'Contains all tables, types, and functions for the Sentinel Access Platform - Implementation Standard v2.0';
COMMENT ON TABLE sentinel.tenants IS 'Multi-tenant organizations with support for sub-tenants [Enhanced with code field]';
COMMENT ON TABLE sentinel.users IS 'Users and service accounts with tenant isolation [Enhanced with avatar and service account fields]';
COMMENT ON TABLE sentinel.roles IS 'Hierarchical roles with inheritance support';
COMMENT ON TABLE sentinel.groups IS 'User groups for bulk permission assignment';
COMMENT ON TABLE sentinel.permissions IS 'Granular permissions with ABAC conditions and field-level control';
COMMENT ON TABLE sentinel.resources IS 'Hierarchical resource definitions [Enhanced with code field]';
COMMENT ON TABLE sentinel.permission_cache IS 'RBAC performance optimization cache [Implementation added]';
COMMENT ON TABLE sentinel.audit_logs IS 'Comprehensive audit trail for compliance and debugging';

-- =====================================================
-- VERSION INFORMATION
-- =====================================================

-- Schema version tracking
CREATE TABLE IF NOT EXISTS sentinel.schema_version (
    version VARCHAR(20) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100)
);

INSERT INTO sentinel.schema_version (version, description, applied_by)
VALUES 
    ('2.0.0', 'Implementation Standard Schema - Reflects actual database state as of 2025-08-08', 'schema_audit_tool')
ON CONFLICT (version) DO NOTHING;