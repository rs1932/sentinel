// User and authentication types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  tenant_id: string;
  user_type: 'standard' | 'service_account';
  attributes?: Record<string, any>;
  preferences?: Record<string, any>;
  avatar_url?: string;
  is_active: boolean;
  roles: Role[];
  tenant: Tenant;
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

export interface Tenant {
  id: string;
  name: string;
  display_name: string;
  type: 'root' | 'sub_tenant';
  parent_tenant_id?: string;
  isolation_mode: 'shared' | 'dedicated';
  features: string[];
  settings: Record<string, any>;
  is_active: boolean;
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