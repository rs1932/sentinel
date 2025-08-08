'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Search, Plus, MoreHorizontal, Lock, Database, Globe, Layers } from 'lucide-react';
import { Permission } from '@/types';
import { CreatePermissionDialog } from '@/components/permissions/CreatePermissionDialog';

export function PermissionsManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const { userRole } = useAuthStore();

  const canManagePermissions = userRole === 'super_admin' || userRole === 'tenant_admin';

  // Fetch permissions from API
  const {
    data: permissionsResponse,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => apiClient.permissions.list(),
    retry: 1,
  });

  const permissions: Permission[] = permissionsResponse?.items || permissionsResponse || [];

  const filteredPermissions = permissions.filter((permission: Permission) => {
    const matchesSearch = `${permission.name} ${permission.resource_type} ${permission.resource_path || permission.resource_id || ''}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    
    const matchesResourceType = resourceTypeFilter === 'all' || permission.resource_type === resourceTypeFilter;
    
    return matchesSearch && matchesResourceType;
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Permission Management</h1>
            <p className="text-gray-600">Loading permissions...</p>
          </div>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Permission Management</h1>
            <p className="text-gray-600">Unable to load permissions</p>
          </div>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <p className="text-red-600">Failed to load permissions. Please try again.</p>
              <p className="text-gray-500 mt-2">Error: {error?.message || 'Unknown error'}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getResourceTypeIcon = (resourceType: string) => {
    switch (resourceType) {
      case 'entity':
        return <Database className="h-4 w-4 text-blue-600" />;
      case 'api':
        return <Globe className="h-4 w-4 text-green-600" />;
      case 'page':
        return <Layers className="h-4 w-4 text-purple-600" />;
      default:
        return <Lock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getResourceTypeColor = (resourceType: string) => {
    switch (resourceType) {
      case 'entity':
        return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
      case 'api':
        return 'bg-green-100 text-green-800 hover:bg-green-100';
      case 'page':
        return 'bg-purple-100 text-purple-800 hover:bg-purple-100';
      case 'service':
        return 'bg-orange-100 text-orange-800 hover:bg-orange-100';
      case 'app':
        return 'bg-indigo-100 text-indigo-800 hover:bg-indigo-100';
      case 'capability':
        return 'bg-pink-100 text-pink-800 hover:bg-pink-100';
      case 'product_family':
        return 'bg-teal-100 text-teal-800 hover:bg-teal-100';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'read':
        return 'bg-green-100 text-green-700';
      case 'write':
      case 'update':
        return 'bg-blue-100 text-blue-700';
      case 'create':
        return 'bg-purple-100 text-purple-700';
      case 'delete':
        return 'bg-red-100 text-red-700';
      case 'execute':
        return 'bg-orange-100 text-orange-700';
      case 'approve':
        return 'bg-emerald-100 text-emerald-700';
      case 'reject':
        return 'bg-rose-100 text-rose-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Permission Management</h1>
          <p className="text-gray-600">
            Define and manage permissions for resources and actions
          </p>
        </div>
        {canManagePermissions && (
          <Button 
            className="bg-blue-600 hover:bg-blue-700"
            onClick={() => setCreateDialogOpen(true)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Permission
          </Button>
        )}
      </div>

      {/* Search and filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Permissions</CardTitle>
              <CardDescription>
                {filteredPermissions.length} permission{filteredPermissions.length !== 1 ? 's' : ''} found
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Select value={resourceTypeFilter} onValueChange={setResourceTypeFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by resource type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Resource Types</SelectItem>
                  <SelectItem value="entity">Entity</SelectItem>
                  <SelectItem value="api">API</SelectItem>
                  <SelectItem value="page">Page</SelectItem>
                  <SelectItem value="service">Service</SelectItem>
                  <SelectItem value="app">App</SelectItem>
                  <SelectItem value="capability">Capability</SelectItem>
                  <SelectItem value="product_family">Product Family</SelectItem>
                </SelectContent>
              </Select>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search permissions..."
                  className="pl-10 w-64"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]"></TableHead>
                  <TableHead>Permission</TableHead>
                  <TableHead>Resource Type</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Actions</TableHead>
                  <TableHead>Status</TableHead>
                  {canManagePermissions && (
                    <TableHead className="w-[50px]">Actions</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPermissions.map((permission) => (
                  <TableRow key={permission.id}>
                    <TableCell>
                      <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                        {getResourceTypeIcon(permission.resource_type)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{permission.name}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          ID: {permission.id}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={getResourceTypeColor(permission.resource_type)}
                      >
                        {permission.resource_type.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {permission.resource_path ? (
                          <span className="font-mono bg-gray-100 px-2 py-1 rounded text-xs">
                            {permission.resource_path}
                          </span>
                        ) : permission.resource_id ? (
                          <span className="text-gray-600">ID: {permission.resource_id}</span>
                        ) : (
                          <span className="text-gray-400 italic">Global</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {permission.actions.map((action, index) => (
                          <Badge
                            key={index}
                            variant="outline"
                            className={`text-xs ${getActionColor(action)}`}
                          >
                            {action}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={permission.is_active ? "default" : "secondary"}
                        className={
                          permission.is_active
                            ? "bg-green-100 text-green-800 hover:bg-green-100"
                            : "bg-gray-100 text-gray-800 hover:bg-gray-100"
                        }
                      >
                        {permission.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    {canManagePermissions && (
                      <TableCell>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Permissions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {permissions.length}
            </div>
            <p className="text-xs text-gray-500">All permissions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Active Permissions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {permissions.filter((p: Permission) => p.is_active).length}
            </div>
            <p className="text-xs text-gray-500">Currently active</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Resource Types
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(permissions.map((p: Permission) => p.resource_type)).size}
            </div>
            <p className="text-xs text-gray-500">Unique types</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Entity Permissions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {permissions.filter((p: Permission) => p.resource_type === 'entity').length}
            </div>
            <p className="text-xs text-gray-500">Entity-based</p>
          </CardContent>
        </Card>
      </div>

      {/* Dialogs */}
      <CreatePermissionDialog 
        open={createDialogOpen} 
        onOpenChange={setCreateDialogOpen} 
      />
    </div>
  );
}