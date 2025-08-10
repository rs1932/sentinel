// TypeScript interfaces for Groups API

export interface Group {
  id: string;
  tenant_id: string;
  name: string;
  display_name?: string | null;
  description?: string | null;
  parent_group_id?: string | null;
  metadata: Record<string, any>;
  is_active: boolean;
  created_at: string; // ISO date
  updated_at: string; // ISO date
}

export interface GroupCreate {
  name: string;
  display_name?: string;
  description?: string;
  parent_group_id?: string;
  metadata?: Record<string, any>;
  is_active?: boolean;
}

export interface GroupUpdate {
  display_name?: string;
  description?: string;
  parent_group_id?: string;
  metadata?: Record<string, any>;
  is_active?: boolean;
}

export interface GroupListResponse {
  items: Group[];
  total: number;
  skip: number;
  limit: number;
}

