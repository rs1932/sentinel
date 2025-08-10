# 🎨 Frontend Integration Guide - Tenant Management

## React Integration Examples

### 1. Tenant Service Setup

```typescript
// services/tenantService.ts
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

class TenantService {
    private baseUrl = 'http://localhost:8000/api/v1';
    private getHeaders() {
        const token = localStorage.getItem('access_token');
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        };
    }

    async listTenants(params?: {
        name?: string;
        code?: string;
        type?: string;
        is_active?: boolean;
        limit?: number;
        offset?: number;
    }): Promise<TenantListResponse> {
        const searchParams = new URLSearchParams();
        
        Object.entries(params || {}).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                searchParams.append(key, String(value));
            }
        });

        const response = await fetch(`${this.baseUrl}/tenants/?${searchParams}`, {
            headers: this.getHeaders(),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch tenants: ${response.statusText}`);
        }
        
        return response.json();
    }

    async getTenant(id: string): Promise<TenantDetail> {
        const response = await fetch(`${this.baseUrl}/tenants/${id}`, {
            headers: this.getHeaders(),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch tenant: ${response.statusText}`);
        }
        
        return response.json();
    }

    async getTenantByCode(code: string): Promise<Tenant> {
        const response = await fetch(`${this.baseUrl}/tenants/code/${code}`, {
            headers: this.getHeaders(),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch tenant by code: ${response.statusText}`);
        }
        
        return response.json();
    }

    async createTenant(data: {
        name: string;
        code: string;
        type?: 'root' | 'sub_tenant';
        parent_tenant_id?: string;
        isolation_mode?: 'shared' | 'dedicated';
        settings?: Record<string, any>;
        features?: string[];
        metadata?: Record<string, any>;
    }): Promise<Tenant> {
        const response = await fetch(`${this.baseUrl}/tenants/`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to create tenant: ${response.statusText}`);
        }
        
        return response.json();
    }

    async updateTenant(id: string, data: {
        name?: string;
        settings?: Record<string, any>;
        features?: string[];
        metadata?: Record<string, any>;
        is_active?: boolean;
    }): Promise<Tenant> {
        const response = await fetch(`${this.baseUrl}/tenants/${id}`, {
            method: 'PATCH',
            headers: this.getHeaders(),
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to update tenant: ${response.statusText}`);
        }
        
        return response.json();
    }

    async deleteTenant(id: string): Promise<void> {
        const response = await fetch(`${this.baseUrl}/tenants/${id}`, {
            method: 'DELETE',
            headers: this.getHeaders(),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to delete tenant: ${response.statusText}`);
        }
    }

    async createSubTenant(parentId: string, data: {
        name: string;
        code: string;
        isolation_mode?: 'shared' | 'dedicated';
        settings?: Record<string, any>;
        features?: string[];
        metadata?: Record<string, any>;
    }): Promise<Tenant> {
        const response = await fetch(`${this.baseUrl}/tenants/${parentId}/sub-tenants`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to create sub-tenant: ${response.statusText}`);
        }
        
        return response.json();
    }

    async getTenantHierarchy(id: string): Promise<Tenant[]> {
        const response = await fetch(`${this.baseUrl}/tenants/${id}/hierarchy`, {
            headers: this.getHeaders(),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch tenant hierarchy: ${response.statusText}`);
        }
        
        return response.json();
    }

    async activateTenant(id: string): Promise<Tenant> {
        const response = await fetch(`${this.baseUrl}/tenants/${id}/activate`, {
            method: 'POST',
            headers: this.getHeaders(),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to activate tenant: ${response.statusText}`);
        }
        
        return response.json();
    }

    async deactivateTenant(id: string): Promise<Tenant> {
        const response = await fetch(`${this.baseUrl}/tenants/${id}/deactivate`, {
            method: 'POST',
            headers: this.getHeaders(),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to deactivate tenant: ${response.statusText}`);
        }
        
        return response.json();
    }
}

export const tenantService = new TenantService();
```

### 2. React Context for Tenant Management

```tsx
// contexts/TenantContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { Tenant, TenantDetail, tenantService } from '../services/tenantService';

interface TenantContextType {
    currentTenant: TenantDetail | null;
    tenantList: Tenant[];
    loading: boolean;
    error: string | null;
    switchTenant: (tenantId: string) => Promise<void>;
    refreshTenants: () => Promise<void>;
    createTenant: (data: any) => Promise<void>;
    updateTenant: (id: string, data: any) => Promise<void>;
    deleteTenant: (id: string) => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const useTenants = () => {
    const context = useContext(TenantContext);
    if (!context) {
        throw new Error('useTenants must be used within TenantProvider');
    }
    return context;
};

export const TenantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [currentTenant, setCurrentTenant] = useState<TenantDetail | null>(null);
    const [tenantList, setTenantList] = useState<Tenant[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const switchTenant = async (tenantId: string) => {
        setLoading(true);
        setError(null);
        
        try {
            const tenant = await tenantService.getTenant(tenantId);
            setCurrentTenant(tenant);
            localStorage.setItem('current_tenant_id', tenantId);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to switch tenant');
        } finally {
            setLoading(false);
        }
    };

    const refreshTenants = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await tenantService.listTenants();
            setTenantList(response.items);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch tenants');
        } finally {
            setLoading(false);
        }
    };

    const createTenant = async (data: any) => {
        setLoading(true);
        setError(null);
        
        try {
            await tenantService.createTenant(data);
            await refreshTenants();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create tenant');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const updateTenant = async (id: string, data: any) => {
        setLoading(true);
        setError(null);
        
        try {
            await tenantService.updateTenant(id, data);
            if (currentTenant?.id === id) {
                await switchTenant(id);
            }
            await refreshTenants();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update tenant');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const deleteTenant = async (id: string) => {
        setLoading(true);
        setError(null);
        
        try {
            await tenantService.deleteTenant(id);
            if (currentTenant?.id === id) {
                setCurrentTenant(null);
                localStorage.removeItem('current_tenant_id');
            }
            await refreshTenants();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete tenant');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    // Initialize tenant context
    useEffect(() => {
        const initializeTenant = async () => {
            const savedTenantId = localStorage.getItem('current_tenant_id');
            if (savedTenantId) {
                await switchTenant(savedTenantId);
            }
            await refreshTenants();
        };

        initializeTenant();
    }, []);

    return (
        <TenantContext.Provider
            value={{
                currentTenant,
                tenantList,
                loading,
                error,
                switchTenant,
                refreshTenants,
                createTenant,
                updateTenant,
                deleteTenant,
            }}
        >
            {children}
        </TenantContext.Provider>
    );
};
```

### 3. Tenant List Component

```tsx
// components/TenantList.tsx
import React, { useState, useEffect } from 'react';
import { useTenants } from '../contexts/TenantContext';
import { Tenant } from '../services/tenantService';

export const TenantList: React.FC = () => {
    const { tenantList, loading, error, switchTenant, currentTenant } = useTenants();
    const [searchTerm, setSearchTerm] = useState('');
    const [filterActive, setFilterActive] = useState<boolean | null>(null);
    const [filteredTenants, setFilteredTenants] = useState<Tenant[]>([]);

    useEffect(() => {
        let filtered = tenantList;
        
        if (searchTerm) {
            filtered = filtered.filter(tenant => 
                tenant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                tenant.code.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }
        
        if (filterActive !== null) {
            filtered = filtered.filter(tenant => tenant.is_active === filterActive);
        }
        
        setFilteredTenants(filtered);
    }, [tenantList, searchTerm, filterActive]);

    const handleTenantClick = async (tenant: Tenant) => {
        if (currentTenant?.id !== tenant.id) {
            await switchTenant(tenant.id);
        }
    };

    const getFeatureBadges = (features: string[]) => {
        const featureMap: Record<string, string> = {
            'api_access': 'API',
            'sso': 'SSO',
            'multi_factor_auth': 'MFA',
            'advanced_audit': 'Audit',
            'ai_insights': 'AI',
            'custom_workflows': 'Workflows',
            'field_encryption': 'Encryption',
            'compliance_reporting': 'Compliance'
        };

        return features.map(feature => (
            <span 
                key={feature}
                className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full mr-1"
            >
                {featureMap[feature] || feature}
            </span>
        ));
    };

    if (loading) return <div className="text-center py-4">Loading tenants...</div>;
    if (error) return <div className="text-red-600 py-4">Error: {error}</div>;

    return (
        <div className="space-y-4">
            {/* Search and Filter */}
            <div className="flex gap-4 mb-4">
                <input
                    type="text"
                    placeholder="Search tenants..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                />
                <select
                    value={filterActive === null ? '' : filterActive.toString()}
                    onChange={(e) => setFilterActive(
                        e.target.value === '' ? null : e.target.value === 'true'
                    )}
                    className="px-3 py-2 border border-gray-300 rounded-md"
                >
                    <option value="">All Status</option>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                </select>
            </div>

            {/* Tenant Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredTenants.map((tenant) => (
                    <div
                        key={tenant.id}
                        onClick={() => handleTenantClick(tenant)}
                        className={`
                            p-4 border rounded-lg cursor-pointer transition-colors
                            ${currentTenant?.id === tenant.id 
                                ? 'border-blue-500 bg-blue-50' 
                                : 'border-gray-200 hover:border-gray-300'}
                            ${!tenant.is_active ? 'opacity-60' : ''}
                        `}
                    >
                        <div className="flex justify-between items-start mb-2">
                            <h3 className="font-medium text-lg">{tenant.name}</h3>
                            <div className="flex items-center gap-2">
                                <span className={`
                                    px-2 py-1 text-xs rounded-full
                                    ${tenant.type === 'root' 
                                        ? 'bg-green-100 text-green-800' 
                                        : 'bg-yellow-100 text-yellow-800'}
                                `}>
                                    {tenant.type === 'root' ? 'Root' : 'Sub'}
                                </span>
                                <span className={`
                                    px-2 py-1 text-xs rounded-full
                                    ${tenant.is_active 
                                        ? 'bg-green-100 text-green-800' 
                                        : 'bg-red-100 text-red-800'}
                                `}>
                                    {tenant.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </div>
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-2">Code: {tenant.code}</p>
                        
                        <div className="mb-2">
                            <p className="text-sm font-medium mb-1">Features:</p>
                            <div className="flex flex-wrap gap-1">
                                {getFeatureBadges(tenant.features)}
                            </div>
                        </div>
                        
                        <div className="text-xs text-gray-500">
                            <p>Isolation: {tenant.isolation_mode}</p>
                            <p>Created: {new Date(tenant.created_at).toLocaleDateString()}</p>
                        </div>
                    </div>
                ))}
            </div>

            {filteredTenants.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                    No tenants found matching your criteria.
                </div>
            )}
        </div>
    );
};
```

### 4. Tenant Creation Form

```tsx
// components/TenantCreateForm.tsx
import React, { useState } from 'react';
import { useTenants } from '../contexts/TenantContext';

const AVAILABLE_FEATURES = [
    { value: 'api_access', label: 'API Access' },
    { value: 'sso', label: 'Single Sign-On' },
    { value: 'multi_factor_auth', label: 'Multi-Factor Auth' },
    { value: 'advanced_audit', label: 'Advanced Audit' },
    { value: 'ai_insights', label: 'AI Insights' },
    { value: 'custom_workflows', label: 'Custom Workflows' },
    { value: 'field_encryption', label: 'Field Encryption' },
    { value: 'compliance_reporting', label: 'Compliance Reporting' },
];

export const TenantCreateForm: React.FC<{ 
    onClose: () => void;
    parentTenant?: string; 
}> = ({ onClose, parentTenant }) => {
    const { createTenant, createSubTenant } = useTenants();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        code: '',
        type: parentTenant ? 'sub_tenant' : 'root',
        isolation_mode: 'shared',
        features: [] as string[],
        settings: {},
        metadata: {},
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const tenantData = {
                ...formData,
                parent_tenant_id: parentTenant || undefined,
            };

            if (parentTenant) {
                await createSubTenant(parentTenant, tenantData);
            } else {
                await createTenant(tenantData);
            }
            
            onClose();
        } catch (error) {
            console.error('Failed to create tenant:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleFeatureToggle = (feature: string) => {
        setFormData(prev => ({
            ...prev,
            features: prev.features.includes(feature)
                ? prev.features.filter(f => f !== feature)
                : [...prev.features, feature]
        }));
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto p-6">
                <h2 className="text-xl font-bold mb-4">
                    Create {parentTenant ? 'Sub-Tenant' : 'Tenant'}
                </h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Name *</label>
                        <input
                            type="text"
                            required
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({...prev, name: e.target.value}))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            placeholder="Enter tenant name"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">Code *</label>
                        <input
                            type="text"
                            required
                            value={formData.code}
                            onChange={(e) => setFormData(prev => ({
                                ...prev, 
                                code: e.target.value.toUpperCase()
                            }))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            placeholder="TENANT-CODE"
                            pattern="^[A-Z0-9][A-Z0-9-]*$"
                            title="Code must contain only uppercase letters, numbers, and hyphens"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">Isolation Mode</label>
                        <select
                            value={formData.isolation_mode}
                            onChange={(e) => setFormData(prev => ({
                                ...prev, 
                                isolation_mode: e.target.value as 'shared' | 'dedicated'
                            }))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        >
                            <option value="shared">Shared</option>
                            <option value="dedicated">Dedicated</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">Features</label>
                        <div className="space-y-2 max-h-32 overflow-y-auto">
                            {AVAILABLE_FEATURES.map((feature) => (
                                <label key={feature.value} className="flex items-center">
                                    <input
                                        type="checkbox"
                                        checked={formData.features.includes(feature.value)}
                                        onChange={() => handleFeatureToggle(feature.value)}
                                        className="mr-2"
                                    />
                                    <span className="text-sm">{feature.label}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="flex gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                        >
                            {loading ? 'Creating...' : 'Create'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
```

### 5. Tenant Hierarchy Component

```tsx
// components/TenantHierarchy.tsx
import React, { useState, useEffect } from 'react';
import { tenantService, Tenant } from '../services/tenantService';
import { useTenants } from '../contexts/TenantContext';

export const TenantHierarchy: React.FC<{ rootTenantId: string }> = ({ rootTenantId }) => {
    const [hierarchy, setHierarchy] = useState<Tenant[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { switchTenant, currentTenant } = useTenants();

    useEffect(() => {
        const loadHierarchy = async () => {
            setLoading(true);
            setError(null);
            
            try {
                const data = await tenantService.getTenantHierarchy(rootTenantId);
                setHierarchy(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load hierarchy');
            } finally {
                setLoading(false);
            }
        };

        loadHierarchy();
    }, [rootTenantId]);

    const renderTenantNode = (tenant: Tenant, level: number = 0) => {
        const children = hierarchy.filter(t => t.parent_tenant_id === tenant.id);
        const isActive = currentTenant?.id === tenant.id;

        return (
            <div key={tenant.id} className="mb-2">
                <div 
                    onClick={() => switchTenant(tenant.id)}
                    className={`
                        flex items-center p-2 rounded cursor-pointer transition-colors
                        ${isActive ? 'bg-blue-100 border-blue-300' : 'hover:bg-gray-50'}
                    `}
                    style={{ marginLeft: `${level * 20}px` }}
                >
                    <div className="flex-1">
                        <div className="flex items-center gap-2">
                            <span className="font-medium">{tenant.name}</span>
                            <span className="text-sm text-gray-500">({tenant.code})</span>
                            <span className={`
                                px-2 py-1 text-xs rounded
                                ${tenant.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}
                            `}>
                                {tenant.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                        <div className="text-xs text-gray-600 mt-1">
                            {tenant.features.length} features • {tenant.isolation_mode} isolation
                        </div>
                    </div>
                </div>
                
                {children.map(child => renderTenantNode(child, level + 1))}
            </div>
        );
    };

    if (loading) return <div className="text-center py-4">Loading hierarchy...</div>;
    if (error) return <div className="text-red-600 py-4">Error: {error}</div>;

    const rootTenant = hierarchy.find(t => t.id === rootTenantId);
    if (!rootTenant) return <div className="text-gray-500 py-4">Tenant not found</div>;

    return (
        <div className="space-y-2">
            <h3 className="font-bold text-lg mb-4">Tenant Hierarchy</h3>
            {renderTenantNode(rootTenant)}
        </div>
    );
};
```

## Vue.js Integration Examples

### 1. Tenant Composable

```typescript
// composables/useTenants.ts
import { ref, reactive, computed } from 'vue';
import { tenantService, Tenant, TenantDetail } from '../services/tenantService';

export const useTenants = () => {
    const currentTenant = ref<TenantDetail | null>(null);
    const tenantList = ref<Tenant[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    const isCurrentTenant = computed(() => (tenantId: string) => 
        currentTenant.value?.id === tenantId
    );

    const switchTenant = async (tenantId: string) => {
        loading.value = true;
        error.value = null;
        
        try {
            const tenant = await tenantService.getTenant(tenantId);
            currentTenant.value = tenant;
            localStorage.setItem('current_tenant_id', tenantId);
        } catch (err) {
            error.value = err instanceof Error ? err.message : 'Failed to switch tenant';
            throw err;
        } finally {
            loading.value = false;
        }
    };

    const loadTenants = async (params?: any) => {
        loading.value = true;
        error.value = null;
        
        try {
            const response = await tenantService.listTenants(params);
            tenantList.value = response.items;
            return response;
        } catch (err) {
            error.value = err instanceof Error ? err.message : 'Failed to load tenants';
            throw err;
        } finally {
            loading.value = false;
        }
    };

    return {
        currentTenant,
        tenantList,
        loading,
        error,
        isCurrentTenant,
        switchTenant,
        loadTenants,
    };
};
```

### 2. Vue Tenant List Component

```vue
<!-- components/TenantList.vue -->
<template>
  <div class="space-y-4">
    <!-- Search and Filters -->
    <div class="flex gap-4">
      <input 
        v-model="searchTerm" 
        type="text" 
        placeholder="Search tenants..."
        class="flex-1 px-3 py-2 border border-gray-300 rounded-md"
      />
      <select 
        v-model="activeFilter" 
        class="px-3 py-2 border border-gray-300 rounded-md"
      >
        <option :value="null">All Status</option>
        <option :value="true">Active</option>
        <option :value="false">Inactive</option>
      </select>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-4">Loading tenants...</div>
    
    <!-- Error State -->
    <div v-else-if="error" class="text-red-600 py-4">Error: {{ error }}</div>
    
    <!-- Tenant Cards -->
    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div 
        v-for="tenant in filteredTenants" 
        :key="tenant.id"
        @click="handleTenantClick(tenant)"
        :class="{
          'border-blue-500 bg-blue-50': isCurrentTenant(tenant.id),
          'border-gray-200 hover:border-gray-300': !isCurrentTenant(tenant.id),
          'opacity-60': !tenant.is_active
        }"
        class="p-4 border rounded-lg cursor-pointer transition-colors"
      >
        <div class="flex justify-between items-start mb-2">
          <h3 class="font-medium text-lg">{{ tenant.name }}</h3>
          <div class="flex items-center gap-2">
            <span 
              :class="tenant.type === 'root' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'"
              class="px-2 py-1 text-xs rounded-full"
            >
              {{ tenant.type === 'root' ? 'Root' : 'Sub' }}
            </span>
            <span 
              :class="tenant.is_active 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'"
              class="px-2 py-1 text-xs rounded-full"
            >
              {{ tenant.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </div>
        
        <p class="text-sm text-gray-600 mb-2">Code: {{ tenant.code }}</p>
        
        <div class="mb-2">
          <p class="text-sm font-medium mb-1">Features:</p>
          <div class="flex flex-wrap gap-1">
            <span 
              v-for="feature in tenant.features" 
              :key="feature"
              class="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
            >
              {{ getFeatureLabel(feature) }}
            </span>
          </div>
        </div>
        
        <div class="text-xs text-gray-500">
          <p>Isolation: {{ tenant.isolation_mode }}</p>
          <p>Created: {{ formatDate(tenant.created_at) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useTenants } from '../composables/useTenants';
import { Tenant } from '../services/tenantService';

const { 
  currentTenant, 
  tenantList, 
  loading, 
  error, 
  isCurrentTenant, 
  switchTenant, 
  loadTenants 
} = useTenants();

const searchTerm = ref('');
const activeFilter = ref<boolean | null>(null);

const filteredTenants = computed(() => {
  let filtered = tenantList.value;
  
  if (searchTerm.value) {
    filtered = filtered.filter(tenant => 
      tenant.name.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
      tenant.code.toLowerCase().includes(searchTerm.value.toLowerCase())
    );
  }
  
  if (activeFilter.value !== null) {
    filtered = filtered.filter(tenant => tenant.is_active === activeFilter.value);
  }
  
  return filtered;
});

const handleTenantClick = async (tenant: Tenant) => {
  if (!isCurrentTenant.value(tenant.id)) {
    await switchTenant(tenant.id);
  }
};

const getFeatureLabel = (feature: string) => {
  const featureMap: Record<string, string> = {
    'api_access': 'API',
    'sso': 'SSO',
    'multi_factor_auth': 'MFA',
    'advanced_audit': 'Audit',
    'ai_insights': 'AI',
    'custom_workflows': 'Workflows',
    'field_encryption': 'Encryption',
    'compliance_reporting': 'Compliance'
  };
  return featureMap[feature] || feature;
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString();
};

onMounted(() => {
  loadTenants();
});
</script>
```

## Error Handling Examples

### Frontend Error Handler

```typescript
// utils/errorHandler.ts
export interface APIError {
    message: string;
    status_code: number;
    details?: any[];
    path?: string;
    method?: string;
}

export class TenantAPIError extends Error {
    public statusCode: number;
    public details?: any[];
    
    constructor(error: APIError) {
        super(error.message);
        this.statusCode = error.status_code;
        this.details = error.details;
        this.name = 'TenantAPIError';
    }
}

export const handleTenantError = (error: any): string => {
    if (error instanceof TenantAPIError) {
        switch (error.statusCode) {
            case 403:
                return 'You do not have permission to perform this action. Please check your tenant access rights.';
            case 404:
                return 'The requested tenant was not found or you do not have access to it.';
            case 409:
                return 'A tenant with this code already exists. Please choose a different code.';
            case 422:
                if (error.details && error.details.length > 0) {
                    return `Validation error: ${error.details.map(d => d.message).join(', ')}`;
                }
                return 'Invalid data provided. Please check your input.';
            default:
                return error.message || 'An unexpected error occurred.';
        }
    }
    
    return error.message || 'An unexpected error occurred.';
};
```

## Best Practices Summary

### 1. State Management
- Use React Context or Vue composables for tenant state
- Cache current tenant in localStorage
- Implement optimistic updates for better UX

### 2. Error Handling  
- Provide specific error messages for common scenarios
- Implement retry mechanisms for transient failures
- Show loading states during operations

### 3. Security
- Always validate tenant access on sensitive operations
- Include tenant context in all API calls
- Implement proper token refresh mechanisms

### 4. Performance
- Implement pagination for tenant lists
- Use debounced search for better performance
- Cache tenant hierarchies when possible

### 5. User Experience
- Provide clear visual indicators for active tenant
- Support tenant switching with confirmation dialogs
- Display feature availability per tenant

---

*Last updated: 2025-08-07*  
*Frontend Integration Version: 1.0.0*