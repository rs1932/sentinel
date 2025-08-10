// User and authentication types
export interface User {
  id: string;
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  tenant_id: string;
  user_type?: 'standard' | 'service_account';
  attributes?: Record<string, any>;
  preferences?: Record<string, any>;
  avatar_url?: string;
  is_active: boolean;
  roles?: Role[];
  tenant?: Tenant;
}

export interface Role {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  type: 'system' | 'custom';
  priority: number;
  tenant_id: string;
  parent_role_id?: string;
  is_assignable: boolean;
  role_metadata?: Record<string, any>;
}

export interface Group {
  id: string;
  tenant_id: string;
  name: string;
  display_name?: string;
  description?: string;
  parent_group_id?: string;
  metadata: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  tenant_id: string;
  name: string;
  resource_type: 'product_family' | 'app' | 'capability' | 'service' | 'entity' | 'page' | 'api';
  resource_id?: string;
  resource_path?: string;
  actions: Array<'create' | 'read' | 'write' | 'update' | 'delete' | 'execute' | 'approve' | 'reject'>;
  conditions: Record<string, any>;
  field_permissions: Record<string, Array<'read' | 'write' | 'hidden'>>;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RolePermission {
  role_id: string;
  permission: Permission;
  granted_by?: string;
}

export interface Tenant {
  id: string;
  name: string;
  display_name?: string;
  code: string;
  type: 'root' | 'sub_tenant';
  parent_tenant_id?: string;
  isolation_mode: 'shared' | 'dedicated';
  settings: Record<string, any>;
  features: string[];
  metadata: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TenantDetail extends Tenant {
  sub_tenants_count: number;
  users_count: number;
  hierarchy: Tenant[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

// User role types for UI permissions
export type UserRole = 'super_admin' | 'tenant_admin' | 'user';

// Navigation and UI types
export interface MenuItem {
  id: string;
  label: string;
  icon: React.ComponentType<any>;
  path: string;
  roles: UserRole[];
  children?: MenuItem[];
}

export interface DashboardStats {
  total_users: number;
  active_users: number;
  total_tenants: number;
  active_tenants: number;
  total_roles: number;
}

// Resource types
export interface Resource {
  id: string;
  tenant_id: string;
  type: 'product_family' | 'app' | 'capability' | 'service' | 'entity' | 'page' | 'api';
  name: string;
  code: string;
  description?: string;
  parent_id?: string;
  path: string;
  level: number;
  metadata: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResourceHierarchy extends Resource {
  children?: ResourceHierarchy[];
  permission_count?: number;
}

export interface ResourceStatistics {
  total_resources: number;
  active_resources: number;
  resources_by_type: Record<string, number>;
  max_depth: number;
  total_permissions: number;
}

// Terminology types
export interface TerminologyConfig {
  terminology: Record<string, string>;
  is_inherited: boolean;
  inherited_from?: string;
  local_config: Record<string, string>;
  last_updated?: string;
  template_applied?: string;
  tenant_id: string;
  tenant_name: string;
  tenant_code: string;
}

export interface UpdateTerminologyRequest {
  terminology: Record<string, string>;
  inherit_parent?: boolean;
  apply_to_children?: boolean;
  template_name?: string;
  metadata?: Record<string, any>;
}

export interface TerminologyValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// Re-export tenant types
export * from './tenant';