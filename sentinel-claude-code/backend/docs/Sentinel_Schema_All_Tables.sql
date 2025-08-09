-- =================================================================
-- Sentinel Platform - Consolidated Database Schema
--
-- This script combines the core, AI, and approval chain schemas
-- into a single file and organizes all objects under the
-- 'sentinel' schema.
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
-- CORE TABLES
-- =====================================================

-- Tenants table (supports multi-tenancy with sub-tenants)
CREATE TABLE sentinel.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL, -- Short identifier like 'GSC-001'
    type sentinel.tenant_type NOT NULL DEFAULT 'root',
    parent_tenant_id UUID REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    isolation_mode sentinel.isolation_mode NOT NULL DEFAULT 'shared',
    settings JSONB DEFAULT '{}', -- Tenant configuration including terminology mapping
    features TEXT[] DEFAULT '{}', -- Enabled features for this tenant
    tenant_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_parent_tenant CHECK (
        (type = 'root' AND parent_tenant_id IS NULL) OR
        (type = 'sub_tenant' AND parent_tenant_id IS NOT NULL)
    )
);

-- Users table
CREATE TABLE sentinel.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    password_hash VARCHAR(255), -- NULL for SSO users
    is_service_account BOOLEAN DEFAULT false,
    service_account_key VARCHAR(255) UNIQUE, -- For M2M authentication
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

-- Roles table
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

-- Groups table (optional but recommended for better organization)
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

-- Resource definitions table
CREATE TABLE sentinel.resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
    type sentinel.resource_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(100) NOT NULL, -- Unique identifier within type
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

-- Permissions table
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

-- Field definitions for three-tier model
CREATE TABLE sentinel.field_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES sentinel.tenants(id) ON DELETE CASCADE, -- NULL for platform-wide fields
    entity_type VARCHAR(100) NOT NULL, -- e.g., 'vessel', 'container'
    field_name VARCHAR(100) NOT NULL,
    field_type VARCHAR(50) NOT NULL, -- 'core', 'platform_dynamic', 'tenant_specific'
    data_type VARCHAR(50) NOT NULL, -- 'string', 'number', 'date', etc.
    storage_column VARCHAR(100), -- For core fields
    storage_path VARCHAR(255), -- JSON path for dynamic fields
    display_name VARCHAR(255),
    description TEXT,
    validation_rules JSONB DEFAULT '{}',
    default_visibility sentinel.field_permission DEFAULT 'read',
    is_indexed BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_field_definition UNIQUE(COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), entity_type, field_name),
    CONSTRAINT check_field_type_storage CHECK (
        (field_type = 'core' AND storage_column IS NOT NULL) OR
        (field_type IN ('platform_dynamic', 'tenant_specific') AND storage_path IS NOT NULL)
    )
);

-- =====================================================
-- RELATIONSHIP TABLES
-- =====================================================

-- User-Role assignments
CREATE TABLE sentinel.user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES sentinel.roles(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES sentinel.users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    CONSTRAINT unique_user_role UNIQUE(user_id, role_id)
);

-- User-Group memberships
CREATE TABLE sentinel.user_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES sentinel.groups(id) ON DELETE CASCADE,
    added_by UUID REFERENCES sentinel.users(id),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_group UNIQUE(user_id, group_id)
);

-- Group-Role assignments
CREATE TABLE sentinel.group_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES sentinel.groups(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES sentinel.roles(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES sentinel.users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_group_role UNIQUE(group_id, role_id)
);

-- Role-Permission assignments
CREATE TABLE sentinel.role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES sentinel.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES sentinel.permissions(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES sentinel.users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_role_permission UNIQUE(role_id, permission_id)
);

-- =====================================================
-- SESSION & TOKEN MANAGEMENT
-- =====================================================

-- JWT token blacklist (for revoked tokens)
CREATE TABLE sentinel.token_blacklist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jti VARCHAR(255) UNIQUE NOT NULL, -- JWT ID
    user_id UUID REFERENCES sentinel.users(id) ON DELETE CASCADE,
    token_type VARCHAR(50) NOT NULL, -- 'access', 'refresh'
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_by UUID REFERENCES sentinel.users(id),
    reason TEXT
);

-- Refresh tokens (for token rotation)
CREATE TABLE sentinel.refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- AUDIT & COMPLIANCE
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

-- Permission check cache (optional, for performance analytics)
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
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- =====================================================
-- NAVIGATION & UI CUSTOMIZATION
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
    CONSTRAINT unique_user_menu UNIQUE(user_id, menu_item_id)
);

-- =====================================================
-- Approval Chains Extension
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Individual approval records
CREATE TABLE sentinel.approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL REFERENCES sentinel.access_requests(id),
    approver_id UUID NOT NULL REFERENCES sentinel.users(id),
    approval_level INTEGER NOT NULL,
    decision VARCHAR(50), -- 'approved', 'denied', 'escalated'
    comments TEXT,
    decided_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Sentinel AI Database Schema Extensions
-- =====================================================

-- AI Models Registry
CREATE TABLE sentinel.ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) NOT NULL UNIQUE,
    model_type VARCHAR(100) NOT NULL, -- 'anomaly_detection', 'permission_prediction', 'nlp', 'compliance'
    version VARCHAR(50) NOT NULL,
    algorithm VARCHAR(100), -- 'isolation_forest', 'random_forest', 'lstm', 'transformer'
    status VARCHAR(50) DEFAULT 'inactive', -- 'training', 'active', 'inactive', 'failed'
    accuracy DECIMAL(5,4), -- 0.0000 to 1.0000
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    training_params JSONB DEFAULT '{}',
    model_storage_path TEXT, -- S3 or file path
    model_size_mb INTEGER,
    training_samples INTEGER,
    last_trained_at TIMESTAMP WITH TIME ZONE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Behavior Profiles
CREATE TABLE sentinel.user_behavior_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id) ON DELETE CASCADE,
    typical_access_hours JSONB DEFAULT '{}', -- {"weekday": ["09:00", "18:00"], "weekend": []}
    common_resources JSONB DEFAULT '[]', -- Most frequently accessed resources
    access_frequency JSONB DEFAULT '{}', -- {"daily_avg": 45, "weekly_avg": 225}
    location_patterns TEXT[] DEFAULT '{}', -- Common login locations
    device_fingerprints JSONB DEFAULT '[]', -- Known devices
    typing_cadence DECIMAL(6,4), -- Keystroke dynamics
    mouse_movement_pattern VARCHAR(100), -- Movement characteristics
    avg_session_duration INTEGER, -- In minutes
    risk_baseline DECIMAL(5,4) DEFAULT 0.1, -- Normal risk score
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_behavior UNIQUE(user_id)
);

-- Anomaly Detections
CREATE TABLE sentinel.anomaly_detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES sentinel.users(id),
    model_id UUID REFERENCES sentinel.ai_models(id),
    detection_type VARCHAR(100) NOT NULL, -- 'unusual_time', 'unusual_location', 'permission_abuse', etc.
    risk_score DECIMAL(5,4) NOT NULL, -- 0.0000 to 1.0000
    confidence DECIMAL(5,4) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    action_attempted VARCHAR(100),
    anomaly_details JSONB NOT NULL, -- Detailed detection information
    recommended_actions TEXT[] DEFAULT '{}', -- ['require_mfa', 'alert_security', 'block_access']
    actual_action_taken VARCHAR(100),
    false_positive BOOLEAN DEFAULT FALSE,
    feedback_by UUID REFERENCES sentinel.users(id),
    feedback_reason TEXT,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Permission Predictions
CREATE TABLE sentinel.permission_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id),
    model_id UUID REFERENCES sentinel.ai_models(id),
    predicted_resource_type VARCHAR(100) NOT NULL,
    predicted_resource_id VARCHAR(255),
    predicted_action VARCHAR(100) NOT NULL,
    probability DECIMAL(5,4) NOT NULL, -- Confidence of prediction
    predicted_need_time TIMESTAMP WITH TIME ZONE,
    reasoning TEXT, -- Why this was predicted
    auto_granted BOOLEAN DEFAULT FALSE,
    actual_used BOOLEAN, -- Was the prediction correct?
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Permission Optimization Suggestions
CREATE TABLE sentinel.permission_optimizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id),
    user_id UUID REFERENCES sentinel.users(id), -- NULL for tenant-wide suggestions
    suggestion_type VARCHAR(100) NOT NULL, -- 'remove_permission', 'consolidate_role', 'add_permission'
    current_state JSONB NOT NULL, -- Current permission/role state
    suggested_state JSONB NOT NULL, -- Suggested changes
    reason TEXT NOT NULL,
    impact_analysis JSONB DEFAULT '{}', -- {"users_affected": 10, "risk_reduction": "25%"}
    confidence DECIMAL(5,4) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'implemented'
    reviewed_by UUID REFERENCES sentinel.users(id),
    implemented_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Natural Language Query Logs
CREATE TABLE sentinel.nlp_query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id),
    query_text TEXT NOT NULL,
    interpreted_intent VARCHAR(100), -- 'grant_permission', 'check_access', 'list_users', etc.
    extracted_entities JSONB DEFAULT '{}', -- Entities extracted from query
    confidence DECIMAL(5,4),
    response_data JSONB,
    response_time_ms INTEGER,
    feedback_rating INTEGER CHECK (feedback_rating >= 1 AND feedback_rating <= 5),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI Training Jobs
CREATE TABLE sentinel.ai_training_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_type VARCHAR(100) NOT NULL,
    job_status VARCHAR(50) DEFAULT 'queued', -- 'queued', 'running', 'completed', 'failed'
    training_config JSONB NOT NULL, -- Algorithm parameters, data sources, etc.
    training_metrics JSONB DEFAULT '{}', -- Performance metrics during training
    data_source VARCHAR(255),
    samples_processed INTEGER DEFAULT 0,
    total_samples INTEGER,
    error_log TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES sentinel.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Compliance Monitoring Results
CREATE TABLE sentinel.compliance_monitoring (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sentinel.tenants(id),
    regulation VARCHAR(100) NOT NULL, -- 'GDPR', 'SOX', 'HIPAA', 'ISPS'
    check_type VARCHAR(100) NOT NULL, -- 'automated', 'manual', 'ai_suggested'
    compliance_score DECIMAL(5,4) NOT NULL, -- 0.0000 to 1.0000
    status VARCHAR(50) NOT NULL, -- 'compliant', 'warning', 'violation'
    findings JSONB DEFAULT '[]', -- Array of compliance issues found
    recommendations JSONB DEFAULT '[]', -- AI-generated recommendations
    evidence JSONB DEFAULT '{}', -- Supporting data for findings
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    next_check_due TIMESTAMP WITH TIME ZONE,
    reviewed_by UUID REFERENCES sentinel.users(id),
    remediation_status VARCHAR(50) DEFAULT 'pending'
);

-- AI Decision Explanations
CREATE TABLE sentinel.ai_decision_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_type VARCHAR(100) NOT NULL, -- 'access_denied', 'anomaly_detected', 'permission_suggested'
    user_id UUID REFERENCES sentinel.users(id),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    decision VARCHAR(255) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    explanation_factors JSONB NOT NULL, -- Factors that led to decision
    model_id UUID REFERENCES sentinel.ai_models(id),
    override_available BOOLEAN DEFAULT TRUE,
    was_overridden BOOLEAN DEFAULT FALSE,
    override_by UUID REFERENCES sentinel.users(id),
    override_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Behavioral Biometrics
CREATE TABLE sentinel.behavioral_biometrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES sentinel.users(id),
    session_id UUID NOT NULL,
    keystroke_dynamics JSONB DEFAULT '{}', -- Typing rhythm patterns
    mouse_patterns JSONB DEFAULT '{}', -- Mouse movement characteristics
    navigation_sequence TEXT[], -- Page navigation patterns
    interaction_timing JSONB DEFAULT '{}', -- Time spent on different actions
    deviation_score DECIMAL(5,4), -- Deviation from normal behavior
    is_authenticated BOOLEAN DEFAULT TRUE, -- Did biometrics match?
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI Agent Communications
CREATE TABLE sentinel.ai_agent_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_agent VARCHAR(100) NOT NULL,
    to_agent VARCHAR(100) NOT NULL,
    message_type VARCHAR(50) NOT NULL, -- 'alert', 'query', 'response', 'coordination'
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'critical'
    content JSONB NOT NULL,
    correlation_id UUID, -- For tracking related messages
    processed BOOLEAN DEFAULT FALSE,
    response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Pre-computed Features for ML
CREATE TABLE sentinel.ml_feature_store (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_set VARCHAR(100) NOT NULL, -- 'user_access_patterns', 'resource_usage', etc.
    entity_type VARCHAR(50) NOT NULL, -- 'user', 'role', 'resource'
    entity_id UUID NOT NULL,
    features JSONB NOT NULL, -- Pre-computed features for ML models
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_feature_entity UNIQUE(feature_set, entity_type, entity_id)
);


-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Tenant indexes
CREATE INDEX idx_tenants_parent ON sentinel.tenants(parent_tenant_id) WHERE parent_tenant_id IS NOT NULL;
CREATE INDEX idx_tenants_active ON sentinel.tenants(is_active) WHERE is_active = true;

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

-- Permission indexes
CREATE INDEX idx_permissions_tenant ON sentinel.permissions(tenant_id);
CREATE INDEX idx_permissions_resource ON sentinel.permissions(resource_id) WHERE resource_id IS NOT NULL;
CREATE INDEX idx_permissions_resource_type ON sentinel.permissions(resource_type);
CREATE INDEX idx_permissions_resource_path ON sentinel.permissions USING gin(resource_path);

-- Field definition indexes
CREATE INDEX idx_field_defs_tenant ON sentinel.field_definitions(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX idx_field_defs_entity ON sentinel.field_definitions(entity_type);
CREATE INDEX idx_field_defs_type ON sentinel.field_definitions(field_type);

-- Relationship indexes
CREATE INDEX idx_user_roles_user ON sentinel.user_roles(user_id);
CREATE INDEX idx_user_roles_role ON sentinel.user_roles(role_id);
CREATE INDEX idx_user_groups_user ON sentinel.user_groups(user_id);
CREATE INDEX idx_user_groups_group ON sentinel.user_groups(group_id);
CREATE INDEX idx_group_roles_group ON sentinel.group_roles(group_id);
CREATE INDEX idx_role_permissions_role ON sentinel.role_permissions(role_id);

-- Audit indexes
CREATE INDEX idx_audit_tenant_created ON sentinel.audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_actor ON sentinel.audit_logs(actor_id) WHERE actor_id IS NOT NULL;
CREATE INDEX idx_audit_resource ON sentinel.audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_action ON sentinel.audit_logs(action);

-- Token indexes
CREATE INDEX idx_token_blacklist_expires ON sentinel.token_blacklist(expires_at);
CREATE INDEX idx_refresh_tokens_user ON sentinel.refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON sentinel.refresh_tokens(expires_at);

-- Permission cache indexes
CREATE INDEX idx_perm_cache_user ON sentinel.permission_cache(user_id);
CREATE INDEX idx_perm_cache_expires ON sentinel.permission_cache(expires_at);

-- Approval chain indexes
CREATE INDEX idx_access_requests_requester ON sentinel.access_requests(requester_id);
CREATE INDEX idx_access_requests_status ON sentinel.access_requests(status) WHERE status = 'pending';
CREATE INDEX idx_approvals_request ON sentinel.approvals(request_id);

-- Indexes for AI tables
CREATE INDEX idx_ai_models_type_status ON sentinel.ai_models(model_type, status);
CREATE INDEX idx_behavior_profiles_user ON sentinel.user_behavior_profiles(user_id);
CREATE INDEX idx_anomaly_user_time ON sentinel.anomaly_detections(user_id, detected_at DESC);
CREATE INDEX idx_anomaly_risk_score ON sentinel.anomaly_detections(risk_score) WHERE risk_score > 0.7;
CREATE INDEX idx_predictions_user_time ON sentinel.permission_predictions(user_id, predicted_need_time);
CREATE INDEX idx_optimizations_status ON sentinel.permission_optimizations(status) WHERE status = 'pending';
CREATE INDEX idx_nlp_queries_user ON sentinel.nlp_query_logs(user_id, created_at DESC);
CREATE INDEX idx_training_jobs_status ON sentinel.ai_training_jobs(job_status) WHERE job_status IN ('queued', 'running');
CREATE INDEX idx_compliance_tenant_regulation ON sentinel.compliance_monitoring(tenant_id, regulation);
CREATE INDEX idx_decision_logs_user ON sentinel.ai_decision_logs(user_id, created_at DESC);
CREATE INDEX idx_biometrics_user_session ON sentinel.behavioral_biometrics(user_id, session_id);
CREATE INDEX idx_agent_messages_unprocessed ON sentinel.ai_agent_messages(processed) WHERE processed = FALSE;
CREATE INDEX idx_feature_store_entity ON sentinel.ml_feature_store(entity_type, entity_id);

-- =====================================================
-- MATERIALIZED VIEWS
-- =====================================================

CREATE MATERIALIZED VIEW sentinel.anomaly_statistics AS
SELECT
    DATE_TRUNC('hour', detected_at) as hour,
    detection_type,
    COUNT(*) as detection_count,
    AVG(risk_score) as avg_risk_score,
    SUM(CASE WHEN false_positive = TRUE THEN 1 ELSE 0 END) as false_positives
FROM sentinel.anomaly_detections
WHERE detected_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', detected_at), detection_type;

CREATE INDEX idx_anomaly_stats_hour ON sentinel.anomaly_statistics(hour DESC);


-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION sentinel.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON sentinel.tenants
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON sentinel.users
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON sentinel.roles
    FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON sentinel.resources
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
END;
$$ language 'plpgsql';

-- Function to check if user needs approval for access
CREATE OR REPLACE FUNCTION sentinel.needs_approval(
    p_user_id UUID,
    p_resource_type VARCHAR,
    p_resource_id VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_chain_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1
        FROM sentinel.approval_chains ac
        WHERE ac.resource_type = p_resource_type
        AND p_resource_id LIKE ac.resource_pattern
        AND ac.is_active = true
    ) INTO v_chain_exists;

    RETURN v_chain_exists;
END;
$$ LANGUAGE plpgsql;

-- Function to update behavior profile
CREATE OR REPLACE FUNCTION sentinel.update_behavior_profile(
    p_user_id UUID,
    p_access_data JSONB
) RETURNS VOID AS $$
DECLARE
    v_existing_profile RECORD;
BEGIN
    SELECT * INTO v_existing_profile
    FROM sentinel.user_behavior_profiles
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        INSERT INTO sentinel.user_behavior_profiles (user_id, common_resources, access_frequency)
        VALUES (p_user_id, p_access_data->'resources', p_access_data->'frequency');
    ELSE
        -- Update with exponential moving average
        UPDATE sentinel.user_behavior_profiles
        SET common_resources = p_access_data->'resources',
            access_frequency = p_access_data->'frequency',
            last_updated = CURRENT_TIMESTAMP
        WHERE user_id = p_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate anomaly score
CREATE OR REPLACE FUNCTION sentinel.calculate_anomaly_score(
    p_user_id UUID,
    p_access_context JSONB
) RETURNS DECIMAL AS $$
DECLARE
    v_behavior_profile RECORD;
    v_time_score DECIMAL := 0;
    v_location_score DECIMAL := 0;
    v_resource_score DECIMAL := 0;
    v_total_score DECIMAL;
BEGIN
    SELECT * INTO v_behavior_profile
    FROM sentinel.user_behavior_profiles
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN 0.5; -- Neutral score for new users
    END IF;

    -- Simplified logic for demonstration
    IF NOT (p_access_context->>'access_hour')::INT = ANY((v_behavior_profile.typical_access_hours->'weekday')::jsonb) THEN
        v_time_score := 0.3;
    END IF;

    IF NOT (p_access_context->>'location') = ANY(v_behavior_profile.location_patterns) THEN
        v_location_score := 0.4;
    END IF;

    IF NOT v_behavior_profile.common_resources @> (p_access_context->'resource') THEN
        v_resource_score := 0.3;
    END IF;

    v_total_score := v_time_score + v_location_score + v_resource_score;

    RETURN LEAST(v_total_score, 1.0);
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-refresh materialized view
CREATE OR REPLACE FUNCTION sentinel.refresh_anomaly_statistics()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY sentinel.anomaly_statistics;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_refresh_anomaly_stats
AFTER INSERT ON sentinel.anomaly_detections
FOR EACH STATEMENT
EXECUTE FUNCTION sentinel.refresh_anomaly_statistics();

-- =====================================================
-- USEFUL VIEWS
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
CREATE OR REPLACE VIEW sentinel.active_sessions AS
SELECT
    u.id as user_id,
    u.email,
    u.tenant_id,
    t.name as tenant_name,
    u.last_login,
    u.is_service_account,
    COUNT(DISTINCT rt.id) as active_refresh_tokens
FROM sentinel.users u
JOIN sentinel.tenants t ON u.tenant_id = t.id
LEFT JOIN sentinel.refresh_tokens rt ON u.id = rt.user_id AND rt.expires_at > CURRENT_TIMESTAMP
WHERE u.is_active = true
GROUP BY u.id, u.email, u.tenant_id, t.name, u.last_login, u.is_service_account;

-- =====================================================
-- INITIAL SYSTEM DATA
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
);

-- Insert system roles
INSERT INTO sentinel.roles (tenant_id, name, display_name, description, type, priority)
VALUES
    ('00000000-0000-0000-0000-000000000000', 'super_admin', 'Super Administrator', 'Platform-wide administrator with full access', 'system', 1000),
    ('00000000-0000-0000-0000-000000000000', 'tenant_admin', 'Tenant Administrator', 'Tenant-level administrator', 'system', 900),
    ('00000000-0000-0000-0000-000000000000', 'user_manager', 'User Manager', 'Can manage users and roles within tenant', 'system', 800),
    ('00000000-0000-0000-0000-000000000000', 'viewer', 'Viewer', 'Read-only access to assigned resources', 'system', 100);

-- Example approval chain for terminal access
INSERT INTO sentinel.approval_chains (tenant_id, name, resource_type, resource_pattern, approval_levels)
VALUES (
    '00000000-0000-0000-0000-000000000000', -- Using the platform tenant ID for this example
    'Example Terminal Access Approval',
    'terminal',
    'terminal:*',
    '[
        {
            "level": 1,
            "approver_role": "terminal_manager",
            "timeout_hours": 24,
            "escalate_to_level": 2
        },
        {
            "level": 2,
            "approver_role": "port_director",
            "timeout_hours": 48,
            "final": true
        }
    ]'::jsonb
);

-- =====================================================
-- GRANT PERMISSIONS (adjust as needed)
-- =====================================================

-- Example: Create an application user and grant permissions to the sentinel schema
-- CREATE USER sentinel_app WITH PASSWORD 'change_me_in_production';
-- GRANT USAGE ON SCHEMA sentinel TO sentinel_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sentinel TO sentinel_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sentinel TO sentinel_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA sentinel TO sentinel_app;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON SCHEMA sentinel IS 'Contains all tables, types, and functions for the Sentinel Access Platform.';
COMMENT ON TABLE sentinel.tenants IS 'Multi-tenant organizations with support for sub-tenants and industry-specific terminology mapping';

-- =====================================================
-- TERMINOLOGY MAPPING IMPLEMENTATION NOTES
-- =====================================================
/*
INDUSTRY TERMINOLOGY MAPPING:
The tenant.settings JSONB field stores terminology configuration to enable 
industry-specific UI labels without database schema changes.

Example settings structure:
{
  "terminology_config": {
    "tenant": "Maritime Authority",
    "sub_tenant": "Port Organization", 
    "user": "Maritime Stakeholder",
    "role": "Stakeholder Type",
    "permission": "Service Clearance",
    "create_tenant": "Register Maritime Organization",
    "user_management": "Stakeholder Management"
  },
  "terminology_metadata": {
    "is_inherited": true,
    "inherited_from": "parent_tenant_id",
    "last_updated": "2025-08-09T10:00:00Z",
    "template_applied": "maritime_v1"
  }
}

INHERITANCE LOGIC:
- Child tenants automatically inherit parent terminology
- Children can override specific terms while inheriting others
- Terminology resolves up the hierarchy until found or defaults used

API IMPACT:
- NO BREAKING CHANGES: All existing APIs work unchanged
- NEW ENDPOINTS: GET/PUT /tenants/{id}/terminology (additive only)
- ENHANCED ENDPOINTS: PATCH /tenants/{id} accepts terminology in settings

IMPLEMENTATION DATE: 2025-08-09
REASON: Enable Sentinel to serve multiple industries (Maritime, Healthcare, 
Finance) with domain-specific terminology while maintaining platform neutrality
*/
COMMENT ON TABLE sentinel.users IS 'Users and service accounts with tenant isolation';
COMMENT ON TABLE sentinel.roles IS 'Hierarchical roles with inheritance support';
COMMENT ON TABLE sentinel.groups IS 'User groups for bulk permission assignment';
COMMENT ON TABLE sentinel.permissions IS 'Granular permissions with ABAC conditions and field-level control';
COMMENT ON TABLE sentinel.resources IS 'Hierarchical resource definitions (Product Family > App > Capability > Service)';
COMMENT ON TABLE sentinel.field_definitions IS 'Three-tier field model: core, platform_dynamic, tenant_specific';
COMMENT ON TABLE sentinel.audit_logs IS 'Comprehensive audit trail for compliance and debugging';
COMMENT ON TABLE sentinel.permission_cache IS 'Optional cache for permission evaluation performance analysis';
COMMENT ON TABLE sentinel.access_requests IS 'Tracks requests for roles, permissions, or resource access that require approval.';
COMMENT ON TABLE sentinel.approval_chains IS 'Defines the multi-level approval workflows for specific resources.';
COMMENT ON TABLE sentinel.ai_models IS 'Registry for all machine learning models used in the platform.';
COMMENT ON TABLE sentinel.anomaly_detections IS 'Logs all detected anomalies in user behavior.';

