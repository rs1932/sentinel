# Frontend Integration Guide

## Overview

This guide shows how to integrate the Resources API with your React/TypeScript frontend application.

## Installation & Setup

Ensure your API client is configured with the Resources API base URL and authentication:

```typescript
// lib/api/client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

class ApiClient {
  constructor() {
    this.baseUrl = `${API_BASE_URL}${API_PREFIX}`;
  }
  
  setToken(token: string) {
    this.token = token;
  }
  
  // ... existing implementation
}
```

## TypeScript Interfaces

Define the response types in your frontend:

```typescript
// types/resource.ts
export interface ResourceTreeNode {
  id: string;
  type: 'product_family' | 'app' | 'capability' | 'service' | 'entity' | 'page' | 'api';
  name: string;
  code: string;
  attributes: Record<string, any>;
  is_active: boolean;
  children: ResourceTreeNode[];
}

export interface ResourceTreeResponse {
  tree: ResourceTreeNode | ResourceTreeNode[];
  total_nodes: number;
  max_depth: number;
}

export interface ResourceStatistics {
  total_resources: number;
  by_type: Record<string, number>;
  active_resources: number;
  inactive_resources: number;
  max_hierarchy_depth: number;
  total_root_resources: number;
}

export interface ResourceListResponse {
  items: Resource[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface Resource {
  id: string;
  tenant_id: string;
  type: string;
  name: string;
  code: string;
  parent_id?: string;
  path: string;
  attributes: Record<string, any>;
  workflow_enabled: boolean;
  workflow_config: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

## React Query Integration

### Basic Resource Tree Hook

```typescript
// hooks/useResourceTree.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useResourceTree(params?: {
  root_id?: string;
  max_depth?: number;
}) {
  return useQuery({
    queryKey: ['resources', 'tree', params],
    queryFn: () => apiClient.resources.getTree(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}
```

### Resource Statistics Hook

```typescript
// hooks/useResourceStatistics.ts
export function useResourceStatistics() {
  return useQuery({
    queryKey: ['resources', 'statistics'],
    queryFn: () => apiClient.resources.getStatistics(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}
```

### Resource List Hook with Search

```typescript
// hooks/useResourceList.ts
export function useResourceList(params?: {
  type?: string;
  parent_id?: string;
  is_active?: boolean;
  search?: string;
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}) {
  return useQuery({
    queryKey: ['resources', 'list', params],
    queryFn: () => apiClient.resources.list(params),
    keepPreviousData: true,
  });
}
```

## React Components

### Resource Tree Component

```typescript
// components/ResourceTree.tsx
import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useResourceTree } from '@/hooks/useResourceTree';
import { ResourceTreeNode } from '@/types/resource';

interface ResourceTreeProps {
  onResourceSelect?: (resource: ResourceTreeNode) => void;
}

export function ResourceTree({ onResourceSelect }: ResourceTreeProps) {
  const { data: resourceTree, isLoading, error } = useResourceTree();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-600">
        <p>Error loading resource tree: {error.message}</p>
      </div>
    );
  }

  if (!resourceTree?.tree) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No resources found</p>
      </div>
    );
  }

  const renderNodes = (nodes: ResourceTreeNode[], level = 0) => {
    const nodeArray = Array.isArray(nodes) ? nodes : [nodes];
    
    return nodeArray.map((node) => (
      <ResourceTreeNodeComponent
        key={node.id}
        node={node}
        level={level}
        onSelect={onResourceSelect}
      />
    ));
  };

  return (
    <div className="space-y-1">
      {renderNodes(resourceTree.tree as ResourceTreeNode[])}
    </div>
  );
}

interface ResourceTreeNodeProps {
  node: ResourceTreeNode;
  level: number;
  onSelect?: (resource: ResourceTreeNode) => void;
}

function ResourceTreeNodeComponent({ node, level, onSelect }: ResourceTreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(level < 2);
  const hasChildren = node.children && node.children.length > 0;

  const getTypeIcon = (type: string) => {
    const icons = {
      product_family: '📦',
      app: '🎯',
      capability: '⚡',
      service: '🔧',
      entity: '📋',
      page: '📄',
      api: '🔌',
    };
    return icons[type as keyof typeof icons] || '📂';
  };

  const getTypeColor = (type: string) => {
    const colors = {
      product_family: 'bg-blue-100 text-blue-800',
      app: 'bg-green-100 text-green-800',
      capability: 'bg-purple-100 text-purple-800',
      service: 'bg-orange-100 text-orange-800',
      entity: 'bg-pink-100 text-pink-800',
      page: 'bg-yellow-100 text-yellow-800',
      api: 'bg-red-100 text-red-800',
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="relative">
      <div 
        className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
        style={{ paddingLeft: `${level * 20 + 12}px` }}
        onClick={() => onSelect?.(node)}
      >
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="w-4 h-4 flex items-center justify-center"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        ) : (
          <div className="w-4 h-4" />
        )}

        <span className="text-lg">{getTypeIcon(node.type)}</span>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 truncate">{node.name}</span>
            <span className={`px-2 py-1 text-xs rounded ${getTypeColor(node.type)}`}>
              {node.type.replace('_', ' ')}
            </span>
            {!node.is_active && (
              <span className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded">
                Inactive
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 truncate">{node.code}</p>
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child) => (
            <ResourceTreeNodeComponent
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

### Resource Statistics Cards

```typescript
// components/ResourceStatistics.tsx
import { Database, TreePine, Shield, Package } from 'lucide-react';
import { useResourceStatistics } from '@/hooks/useResourceStatistics';

export function ResourceStatistics() {
  const { data: stats, isLoading } = useResourceStatistics();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 bg-gray-200 animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        title="Total Resources"
        value={stats.total_resources}
        subtitle={`${stats.active_resources} active`}
        icon={<Database className="h-4 w-4 text-muted-foreground" />}
      />
      
      <StatCard
        title="Max Depth"
        value={stats.max_hierarchy_depth}
        subtitle="hierarchy levels"
        icon={<TreePine className="h-4 w-4 text-muted-foreground" />}
      />
      
      <StatCard
        title="Root Resources"
        value={stats.total_root_resources}
        subtitle="top-level items"
        icon={<Package className="h-4 w-4 text-muted-foreground" />}
      />
      
      <StatCard
        title="Resource Types"
        value={Object.keys(stats.by_type).length}
        subtitle="different types"
        icon={<Shield className="h-4 w-4 text-muted-foreground" />}
      />
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  subtitle: string;
  icon: React.ReactNode;
}

function StatCard({ title, value, subtitle, icon }: StatCardProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow border">
      <div className="flex items-center justify-between space-y-0 pb-2">
        <h3 className="text-sm font-medium">{title}</h3>
        {icon}
      </div>
      <div>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </div>
    </div>
  );
}
```

### Resource Creation Form

```typescript
// components/CreateResourceDialog.tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface CreateResourceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  parentId?: string;
}

const RESOURCE_TYPES = [
  { value: 'product_family', label: 'Product Family' },
  { value: 'app', label: 'Application' },
  { value: 'capability', label: 'Capability' },
  { value: 'service', label: 'Service' },
  { value: 'entity', label: 'Entity' },
  { value: 'page', label: 'Page' },
  { value: 'api', label: 'API' },
];

export function CreateResourceDialog({ open, onOpenChange, parentId }: CreateResourceDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    type: '',
    description: '',
  });

  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: typeof formData & { parent_id?: string }) =>
      apiClient.resources.create(data),
    onSuccess: () => {
      // Invalidate and refetch resource queries
      queryClient.invalidateQueries({ queryKey: ['resources'] });
      onOpenChange(false);
      resetForm();
    },
    onError: (error) => {
      console.error('Failed to create resource:', error);
    },
  });

  const resetForm = () => {
    setFormData({
      name: '',
      code: '',
      type: '',
      description: '',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const submitData = {
      ...formData,
      attributes: formData.description ? { description: formData.description } : {},
      ...(parentId && { parent_id: parentId }),
    };

    createMutation.mutate(submitData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Resource</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Resource Type</label>
            <Select
              value={formData.type}
              onValueChange={(value) => setFormData(prev => ({ ...prev, type: value }))}
            >
              {RESOURCE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                name: e.target.value,
                code: prev.code || e.target.value.toLowerCase().replace(/\s+/g, '-')
              }))}
              placeholder="Resource name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Code</label>
            <Input
              value={formData.code}
              onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value }))}
              placeholder="resource-code"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <Input
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Resource description"
            />
          </div>

          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? 'Creating...' : 'Create Resource'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

## Permission-Based UI

### Checking Resource Access

```typescript
// hooks/useResourcePermission.ts
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';

export function useResourcePermission(resourceType: string, resourceId: string, action: string) {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['permissions', 'check', resourceType, resourceId, action],
    queryFn: async () => {
      // This would be a custom permission check endpoint
      // For now, check user scopes
      if (!user?.scopes) return { allowed: false };
      
      const globalScope = `${resourceType}:global`;
      const specificScope = `${resourceType}:${action}`;
      
      return {
        allowed: user.scopes.includes(globalScope) || user.scopes.includes(specificScope)
      };
    },
    enabled: !!user,
  });
}
```

### Conditional Rendering Based on Permissions

```typescript
// components/ResourceActions.tsx
interface ResourceActionsProps {
  resource: Resource;
}

export function ResourceActions({ resource }: ResourceActionsProps) {
  const canEdit = useResourcePermission('resource', resource.id, 'write');
  const canDelete = useResourcePermission('resource', resource.id, 'admin');

  return (
    <div className="flex gap-2">
      {canEdit.data?.allowed && (
        <Button variant="outline" size="sm">
          Edit
        </Button>
      )}
      
      {canDelete.data?.allowed && (
        <Button variant="outline" size="sm" className="text-red-600">
          Delete
        </Button>
      )}
    </div>
  );
}
```

## Error Handling

### Global Error Boundary for Resource Operations

```typescript
// components/ResourceErrorBoundary.tsx
import { QueryErrorResetBoundary } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';

function ResourceErrorFallback({ error, resetErrorBoundary }: any) {
  if (error.status === 403) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Access Denied</h3>
        <p className="text-gray-600 mb-4">
          You don't have permission to view this resource.
        </p>
        <Button onClick={resetErrorBoundary}>Try Again</Button>
      </div>
    );
  }

  return (
    <div className="text-center py-12">
      <h3 className="text-lg font-medium text-gray-900 mb-2">Something went wrong</h3>
      <p className="text-gray-600 mb-4">{error.message}</p>
      <Button onClick={resetErrorBoundary}>Try Again</Button>
    </div>
  );
}

export function ResourceErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          FallbackComponent={ResourceErrorFallback}
        >
          {children}
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
```

## Complete Dashboard Example

```typescript
// pages/ResourcesDashboard.tsx
import { ResourceTree } from '@/components/ResourceTree';
import { ResourceStatistics } from '@/components/ResourceStatistics';
import { CreateResourceDialog } from '@/components/CreateResourceDialog';
import { ResourceErrorBoundary } from '@/components/ResourceErrorBoundary';

export function ResourcesDashboard() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedResource, setSelectedResource] = useState<ResourceTreeNode | null>(null);

  return (
    <ResourceErrorBoundary>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Resources</h1>
            <p className="text-gray-600">Manage your resource hierarchy</p>
          </div>
          <Button onClick={() => setCreateDialogOpen(true)}>
            Create Resource
          </Button>
        </div>

        <ResourceStatistics />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h2 className="text-lg font-medium">Resource Hierarchy</h2>
            <ResourceTree onResourceSelect={setSelectedResource} />
          </div>
          
          <div className="space-y-4">
            <h2 className="text-lg font-medium">Resource Details</h2>
            {selectedResource ? (
              <ResourceDetails resource={selectedResource} />
            ) : (
              <div className="text-center py-12 text-gray-500">
                Select a resource to view details
              </div>
            )}
          </div>
        </div>

        <CreateResourceDialog
          open={createDialogOpen}
          onOpenChange={setCreateDialogOpen}
        />
      </div>
    </ResourceErrorBoundary>
  );
}
```

This frontend integration guide provides everything your engineers need to build a complete resource management interface that works seamlessly with the Resources API.