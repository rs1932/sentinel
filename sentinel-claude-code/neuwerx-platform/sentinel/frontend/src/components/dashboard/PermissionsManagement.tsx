'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Search, 
  Plus, 
  MoreHorizontal, 
  Lock, 
  Database, 
  Globe, 
  Layers, 
  Edit,
  Trash2,
  Copy,
  Eye,
  Filter,
  Grid3X3,
  FileText,
  BarChart3,
  Settings,
  Zap
} from 'lucide-react';
import { Permission } from '@/types';
import { CreatePermissionDialog } from '@/components/permissions/CreatePermissionDialog';
import { EditPermissionDialog } from '@/components/permissions/EditPermissionDialog';
import { DeletePermissionDialog } from '@/components/permissions/DeletePermissionDialog';
import { PermissionPreviewDialog } from '@/components/permissions/PermissionPreviewDialog';
import { PermissionMatrixView } from '@/components/permissions/PermissionMatrixView';
import { BulkPermissionActions } from '@/components/permissions/BulkPermissionActions';
import { RolePermissionMatrix } from '@/components/rbac/RolePermissionMatrix';

export function PermissionsManagement() {
  const [activeTab, setActiveTab] = useState('list');
  const [searchTerm, setSearchTerm] = useState('');
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [actionFilter, setActionFilter] = useState<string>('all');
  
  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  
  // Selected permission for operations
  const [selectedPermission, setSelectedPermission] = useState<Permission | null>(null);
  
  // Bulk selection
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [showBulkActions, setShowBulkActions] = useState(false);

  const { userRole } = useAuthStore();
  const canManagePermissions = userRole === 'super_admin' || userRole === 'tenant_admin';

  // Fetch permissions from API
  const {
    data: permissionsResponse,
    isLoading,
    error,
    refetch: refetchPermissions,
  } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => apiClient.permissions.list(),
    retry: 1,
  });

  // Fetch resources for better display
  const { data: resourcesResponse } = useQuery({
    queryKey: ['resources', 'list'],
    queryFn: () => apiClient.resources.list({ limit: 1000 }),
  });

  const permissions: Permission[] = permissionsResponse?.items || permissionsResponse || [];
  const resources = resourcesResponse?.items || [];

  // Create resource lookup map
  const resourceMap = resources.reduce((acc: any, resource: any) => {
    acc[resource.id] = resource;
    return acc;
  }, {});

  const filteredPermissions = permissions.filter((permission: Permission) => {
    const matchesSearch = `${permission.name} ${permission.resource_type} ${permission.resource_path || permission.resource_id || ''}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    
    const matchesResourceType = resourceTypeFilter === 'all' || permission.resource_type === resourceTypeFilter;
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'active' && permission.is_active) ||
      (statusFilter === 'inactive' && !permission.is_active);
    
    const matchesAction = actionFilter === 'all' || (permission.actions && permission.actions.includes(actionFilter as any));
    
    return matchesSearch && matchesResourceType && matchesStatus && matchesAction;
  });

  // Handle bulk selection
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedPermissions(filteredPermissions.map(p => p.id));
    } else {
      setSelectedPermissions([]);
    }
  };

  const handleSelectPermission = (permissionId: string, checked: boolean) => {
    if (checked) {
      setSelectedPermissions(prev => [...prev, permissionId]);
    } else {
      setSelectedPermissions(prev => prev.filter(id => id !== permissionId));
    }
  };

  useEffect(() => {
    setShowBulkActions(selectedPermissions.length > 0);
  }, [selectedPermissions]);

  const handleEdit = (permission: Permission) => {
    setSelectedPermission(permission);
    setEditDialogOpen(true);
  };

  const handleDelete = (permission: Permission) => {
    setSelectedPermission(permission);
    setDeleteDialogOpen(true);
  };

  const handlePreview = (permission: Permission) => {
    setSelectedPermission(permission);
    setPreviewDialogOpen(true);
  };

  const handleCopy = async (permission: Permission) => {
    // Copy permission details to clipboard
    const permissionText = `Permission: ${permission.name}\nType: ${permission.resource_type}\nActions: ${permission.actions.join(', ')}\nResource: ${permission.resource_path || permission.resource_id || 'Global'}`;
    await navigator.clipboard.writeText(permissionText);
  };

  const refreshData = () => {
    refetchPermissions();
    setSelectedPermissions([]);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Permission Management</h1>
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
            <h1 className="text-2xl font-semibold text-gray-900">Permission Management</h1>
            <p className="text-gray-600">Unable to load permissions</p>
          </div>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <p className="text-red-600">Failed to load permissions. Please try again.</p>
              <p className="text-gray-500 mt-2">Error: {error?.message || 'Unknown error'}</p>
              <Button onClick={() => refetchPermissions()} className="mt-4">
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getResourceTypeIcon = (resourceType: string) => {
    switch (resourceType) {
      case 'product_family': return <FileText className="h-4 w-4 text-teal-600" />;
      case 'app': return <Settings className="h-4 w-4 text-indigo-600" />;
      case 'capability': return <Zap className="h-4 w-4 text-pink-600" />;
      case 'service': return <BarChart3 className="h-4 w-4 text-orange-600" />;
      case 'entity': return <Database className="h-4 w-4 text-blue-600" />;
      case 'api': return <Globe className="h-4 w-4 text-green-600" />;
      case 'page': return <Layers className="h-4 w-4 text-purple-600" />;
      default: return <Lock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getResourceTypeColor = (resourceType: string) => {
    switch (resourceType) {
      case 'product_family': return 'bg-teal-100 text-teal-800 hover:bg-teal-100';
      case 'app': return 'bg-indigo-100 text-indigo-800 hover:bg-indigo-100';
      case 'capability': return 'bg-pink-100 text-pink-800 hover:bg-pink-100';
      case 'service': return 'bg-orange-100 text-orange-800 hover:bg-orange-100';
      case 'entity': return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
      case 'api': return 'bg-green-100 text-green-800 hover:bg-green-100';
      case 'page': return 'bg-purple-100 text-purple-800 hover:bg-purple-100';
      default: return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'read': return 'bg-green-100 text-green-700';
      case 'write':
      case 'update': return 'bg-blue-100 text-blue-700';
      case 'create': return 'bg-purple-100 text-purple-700';
      case 'delete': return 'bg-red-100 text-red-700';
      case 'execute': return 'bg-orange-100 text-orange-700';
      case 'approve': return 'bg-emerald-100 text-emerald-700';
      case 'reject': return 'bg-rose-100 text-rose-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getResourceDisplay = (permission: Permission) => {
    if (permission.resource_id && resourceMap[permission.resource_id]) {
      const resource = resourceMap[permission.resource_id];
      return (
        <div>
          <div className="font-medium text-sm">{resource.name}</div>
          <div className="text-xs text-gray-500">{resource.code}</div>
        </div>
      );
    } else if (permission.resource_path) {
      return (
        <span className="font-mono bg-gray-100 px-2 py-1 rounded text-xs">
          {permission.resource_path}
        </span>
      );
    } else if (permission.resource_id) {
      return (
        <span className="text-gray-600 text-xs">ID: {permission.resource_id}</span>
      );
    } else {
      return <span className="text-gray-400 italic text-xs">Global</span>;
    }
  };

  const allActions = Array.from(new Set(permissions.flatMap(p => p.actions)));

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Permission Management</h1>
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

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Permissions</CardTitle>
            <Lock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{permissions.length}</div>
            <p className="text-xs text-muted-foreground">All permissions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <Badge className="bg-green-100 text-green-800" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {permissions.filter((p: Permission) => p.is_active).length}
            </div>
            <p className="text-xs text-muted-foreground">Currently active</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resource Types</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(permissions.map((p: Permission) => p.resource_type)).size}
            </div>
            <p className="text-xs text-muted-foreground">Unique types</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Actions</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{allActions.length}</div>
            <p className="text-xs text-muted-foreground">Different actions</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="list">Permission List</TabsTrigger>
          <TabsTrigger value="matrix">Role-Permission Matrix</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="list">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Permissions</CardTitle>
                  <CardDescription>
                    {filteredPermissions.length} permission{filteredPermissions.length !== 1 ? 's' : ''} found
                    {selectedPermissions.length > 0 && ` (${selectedPermissions.length} selected)`}
                  </CardDescription>
                </div>
                
                {/* Bulk Actions */}
                {showBulkActions && (
                  <BulkPermissionActions
                    selectedPermissions={selectedPermissions}
                    onComplete={refreshData}
                  />
                )}
              </div>

              {/* Filters */}
              <div className="flex items-center gap-4 flex-wrap">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search permissions..."
                    className="pl-10 w-64"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>

                <Select value={resourceTypeFilter} onValueChange={setResourceTypeFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Resource Type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Resource Types</SelectItem>
                    <SelectItem value="product_family">Product Family</SelectItem>
                    <SelectItem value="app">Application</SelectItem>
                    <SelectItem value="capability">Capability</SelectItem>
                    <SelectItem value="service">Service</SelectItem>
                    <SelectItem value="entity">Entity</SelectItem>
                    <SelectItem value="page">Page</SelectItem>
                    <SelectItem value="api">API</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={actionFilter} onValueChange={setActionFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Action" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Actions</SelectItem>
                    {allActions.map(action => (
                      <SelectItem key={action} value={action}>{action}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]">
                        <Checkbox
                          checked={selectedPermissions.length === filteredPermissions.length && filteredPermissions.length > 0}
                          onCheckedChange={handleSelectAll}
                        />
                      </TableHead>
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
                          <Checkbox
                            checked={selectedPermissions.includes(permission.id)}
                            onCheckedChange={(checked) => handleSelectPermission(permission.id, checked as boolean)}
                          />
                        </TableCell>
                        <TableCell>
                          <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                            {getResourceTypeIcon(permission.resource_type)}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{permission.name}</div>
                            <div className="text-xs text-gray-400 mt-1">
                              ID: {permission.id.slice(0, 8)}...
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
                            {getResourceDisplay(permission)}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {permission.actions.slice(0, 3).map((action, index) => (
                              <Badge
                                key={index}
                                variant="outline"
                                className={`text-xs ${getActionColor(action)}`}
                              >
                                {action}
                              </Badge>
                            ))}
                            {permission.actions.length > 3 && (
                              <Badge variant="outline" className="text-xs bg-gray-100 text-gray-700">
                                +{permission.actions.length - 3}
                              </Badge>
                            )}
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
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handlePreview(permission)}>
                                  <Eye className="mr-2 h-4 w-4" />
                                  Preview
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleEdit(permission)}>
                                  <Edit className="mr-2 h-4 w-4" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleCopy(permission)}>
                                  <Copy className="mr-2 h-4 w-4" />
                                  Copy Details
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem 
                                  onClick={() => handleDelete(permission)}
                                  className="text-red-600"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {filteredPermissions.length === 0 && (
                  <div className="text-center py-12">
                    <Lock className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium mb-2">No permissions found</h3>
                    <p className="text-gray-500 mb-4">
                      {searchTerm || resourceTypeFilter !== 'all' || statusFilter !== 'all' || actionFilter !== 'all'
                        ? 'Try adjusting your filters or search terms.'
                        : 'Get started by creating your first permission.'
                      }
                    </p>
                    {canManagePermissions && (
                      <Button onClick={() => setCreateDialogOpen(true)}>
                        <Plus className="mr-2 h-4 w-4" />
                        Create Permission
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="matrix">
          <RolePermissionMatrix />
        </TabsContent>

        <TabsContent value="analytics">
          <Card>
            <CardHeader>
              <CardTitle>Permission Analytics</CardTitle>
              <CardDescription>
                Insights and statistics about your permission system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <BarChart3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p>Analytics coming soon...</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <CreatePermissionDialog 
        open={createDialogOpen} 
        onOpenChange={setCreateDialogOpen}
        onSuccess={refreshData}
      />

      {selectedPermission && (
        <>
          <EditPermissionDialog
            open={editDialogOpen}
            onOpenChange={setEditDialogOpen}
            permission={selectedPermission}
            onSuccess={refreshData}
          />

          <DeletePermissionDialog
            open={deleteDialogOpen}
            onOpenChange={setDeleteDialogOpen}
            permission={selectedPermission}
            onSuccess={refreshData}
          />

          <PermissionPreviewDialog
            open={previewDialogOpen}
            onOpenChange={setPreviewDialogOpen}
            permission={selectedPermission}
          />
        </>
      )}
    </div>
  );
}