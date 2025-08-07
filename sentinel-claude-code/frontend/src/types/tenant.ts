export interface Tenant {
  id: string;
  name: string;
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

export interface TenantListResponse {
  items: Tenant[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateTenantData {
  name: string;
  code: string;
  type?: 'root' | 'sub_tenant';
  parent_tenant_id?: string;
  isolation_mode?: 'shared' | 'dedicated';
  settings?: Record<string, any>;
  features?: string[];
  metadata?: Record<string, any>;
}

export interface UpdateTenantData {
  name?: string;
  settings?: Record<string, any>;
  features?: string[];
  metadata?: Record<string, any>;
  is_active?: boolean;
}

// Available features from the API documentation
export const AVAILABLE_FEATURES = [
  { value: 'multi_factor_auth', label: 'Multi-Factor Authentication' },
  { value: 'advanced_audit', label: 'Advanced Audit Logging' },
  { value: 'ai_insights', label: 'AI-Powered Analytics' },
  { value: 'custom_workflows', label: 'Custom Workflow Builder' },
  { value: 'api_access', label: 'REST API Access' },
  { value: 'sso', label: 'Single Sign-On Integration' },
  { value: 'field_encryption', label: 'Field-Level Encryption' },
  { value: 'compliance_reporting', label: 'Compliance Reporting' },
];

export const FEATURE_LABELS: Record<string, string> = {
  multi_factor_auth: 'MFA',
  advanced_audit: 'Audit',
  ai_insights: 'AI',
  custom_workflows: 'Workflows',
  api_access: 'API',
  sso: 'SSO',
  field_encryption: 'Encryption',
  compliance_reporting: 'Compliance',
};