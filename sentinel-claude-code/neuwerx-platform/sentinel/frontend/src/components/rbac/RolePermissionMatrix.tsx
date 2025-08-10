'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Shield, Lock, Search, Filter, Save, RotateCcw,
  ChevronDown, ChevronRight, Users, Settings, CheckCircle,
  AlertTriangle, Info, Package, Database, Globe
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Permission {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  resource_type: string;
  action: string;
  is_active: boolean;
  created_at: string;
}

interface Role {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  type: 'system' | 'custom';
  is_active: boolean;
  permissions?: Array<{
    id: string;
    name: string;
    display_name: string;
  }>;
}

interface RolePermissionMapping {
  [roleId: string]: string[]; // Array of permission IDs
}

export function RolePermissionMatrix() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedResourceType, setSelectedResourceType] = useState<string>('all');
  const [selectedRoleType, setSelectedRoleType] = useState<string>('all');
  const [expandedResources, setExpandedResources] = useState<string[]>([]);
  const [rolePermissions, setRolePermissions] = useState<RolePermissionMapping>({});
  const [pendingChanges, setPendingChanges] = useState<RolePermissionMapping>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch roles
  const { data: rolesResponse, isLoading: rolesLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => apiClient.roles.list({
      limit: 100,
      sort_by: 'display_name',
      sort_order: 'asc'
    })
  });

  // Fetch permissions
  const { data: permissionsResponse, isLoading: permissionsLoading } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => apiClient.permissions.list({
      limit: 1000, // Get all permissions
      resource_type: selectedResourceType === 'all' ? undefined : selectedResourceType
    })
  });

  // Save changes mutation
  const saveChangesMutation = useMutation({
    mutationFn: async (changes: RolePermissionMapping) => {
      const promises = [];
      
      for (const [roleId, permissionIds] of Object.entries(changes)) {
        // Get current permissions for this role
        const currentPermissions = rolePermissions[roleId] || [];
        
        // Determine permissions to add and remove
        const toAdd = permissionIds.filter(id => !currentPermissions.includes(id));
        const toRemove = currentPermissions.filter(id => !permissionIds.includes(id));
        
        // Add new permissions
        if (toAdd.length > 0) {
          promises.push(
            apiClient.permissions.assignToRole(roleId, 
              toAdd.map(permissionId => ({ permission_id: permissionId }))
            )
          );
        }
        
        // Remove permissions
        for (const permissionId of toRemove) {
          promises.push(apiClient.permissions.removeFromRole(roleId, permissionId));
        }
      }
      
      await Promise.all(promises);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      queryClient.invalidateQueries({ queryKey: ['permissions'] });
      setPendingChanges({});
      setError(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to save changes');
    }
  });

  const roles = rolesResponse?.data || [];
  const permissions = permissionsResponse?.data || [];

  // Filter roles based on search and type
  const filteredRoles = roles.filter((role: any) => {
    if (selectedRoleType !== 'all' && role.type !== selectedRoleType) return false;
    if (searchTerm) {
      return role.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
             role.name.toLowerCase().includes(searchTerm.toLowerCase());
    }
    return true;
  });

  // Group permissions by resource type
  const permissionsByResource = permissions.reduce((acc: any, permission: any) => {
    const resourceType = permission.resource_type || 'other';
    if (!acc[resourceType]) {
      acc[resourceType] = [];
    }
    acc[resourceType].push(permission);
    return acc;
  }, {} as Record<string, Permission[]>);

  // Get unique resource types for filtering
  const resourceTypes = Array.from(new Set(permissions.map((p: any) => p.resource_type || 'other'))) as string[];

  // Initialize role permissions from API data
  useEffect(() => {
    const mapping: RolePermissionMapping = {};
    roles.forEach((role: any) => {
      mapping[role.id] = role.permissions?.map((p: any) => p.id) || [];
    });
    setRolePermissions(mapping);
    setPendingChanges(mapping);
  }, [roles]);

  const handlePermissionToggle = (roleId: string, permissionId: string, checked: boolean) => {
    setPendingChanges(prev => {
      const rolePerms = prev[roleId] || [];
      const newPerms = checked
        ? [...rolePerms, permissionId]
        : rolePerms.filter(id => id !== permissionId);
      
      return {
        ...prev,
        [roleId]: newPerms
      };
    });
  };

  const handleResourceToggle = (resourceType: string) => {
    setExpandedResources(prev => 
      prev.includes(resourceType)
        ? prev.filter(r => r !== resourceType)
        : [...prev, resourceType]
    );
  };

  const resetChanges = () => {
    setPendingChanges({ ...rolePermissions });
    setError(null);
  };

  const saveChanges = async () => {
    setLoading(true);
    try {
      await saveChangesMutation.mutateAsync(pendingChanges);
    } finally {
      setLoading(false);
    }
  };

  const hasChanges = () => {
    return JSON.stringify(rolePermissions) !== JSON.stringify(pendingChanges);
  };

  const getRolePermissionCount = (roleId: string) => {
    return pendingChanges[roleId]?.length || 0;
  };

  const getResourceIcon = (resourceType: string) => {
    switch (resourceType) {
      case 'user': return Users;
      case 'role': return Shield;
      case 'permission': return Lock;
      case 'resource': return Package;
      case 'tenant': return Database;
      case 'system': return Settings;
      default: return Globe;
    }
  };

  const isLoading = rolesLoading || permissionsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading role-permission matrix...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
            <Shield className="h-6 w-6" />
            <span>Role-Permission Matrix</span>
          </h1>
          <p className="text-gray-600">
            Manage role-permission assignments across your organization
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {hasChanges() && (
            <>
              <Button variant="outline" onClick={resetChanges} disabled={loading}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Reset
              </Button>
              <Button onClick={saveChanges} disabled={loading}>
                <Save className="mr-2 h-4 w-4" />
                {loading ? 'Saving...' : 'Save Changes'}
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters & Search</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search roles..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {/* Role Type Filter */}
            <Select value={selectedRoleType} onValueChange={setSelectedRoleType}>
              <SelectTrigger>
                <SelectValue placeholder="Role Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Role Types</SelectItem>
                <SelectItem value="system">System Roles</SelectItem>
                <SelectItem value="custom">Custom Roles</SelectItem>
              </SelectContent>
            </Select>

            {/* Resource Type Filter */}
            <Select value={selectedResourceType} onValueChange={setSelectedResourceType}>
              <SelectTrigger>
                <SelectValue placeholder="Resource Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Resource Types</SelectItem>
                {resourceTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      {hasChanges() && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            You have unsaved changes. {Object.keys(pendingChanges).length} role(s) will be updated.
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Matrix */}
      <Tabs defaultValue="matrix" className="space-y-4">
        <TabsList>
          <TabsTrigger value="matrix">Permission Matrix</TabsTrigger>
          <TabsTrigger value="summary">Role Summary</TabsTrigger>
        </TabsList>

        <TabsContent value="matrix">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Role-Permission Assignment Matrix</CardTitle>
              <CardDescription>
                Toggle checkboxes to assign or remove permissions from roles
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {Object.entries(permissionsByResource).map(([resourceType, resourcePermissions]) => {
                  const ResourceIcon = getResourceIcon(resourceType);
                  const isExpanded = expandedResources.includes(resourceType);
                  
                  return (
                    <div key={resourceType} className="border rounded-lg">
                      {/* Resource Type Header */}
                      <div 
                        className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                        onClick={() => handleResourceToggle(resourceType)}
                      >
                        <div className="flex items-center space-x-3">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                          <ResourceIcon className="h-5 w-5 text-blue-600" />
                          <span className="font-medium capitalize">
                            {resourceType.replace('_', ' ')} Permissions
                          </span>
                          <Badge variant="outline" className="text-xs">
                            {(resourcePermissions as any[]).length}
                          </Badge>
                        </div>
                      </div>

                      {/* Permission Matrix */}
                      {isExpanded && (
                        <div className="p-4">
                          <ScrollArea className="h-96">
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead className="w-1/3">Permission</TableHead>
                                  {filteredRoles.map((role: any) => (
                                    <TableHead key={role.id} className="text-center min-w-[120px]">
                                      <div className="space-y-1">
                                        <div className="font-medium text-xs">
                                          {role.display_name}
                                        </div>
                                        <Badge variant="outline" className="text-xs">
                                          {role.type}
                                        </Badge>
                                      </div>
                                    </TableHead>
                                  ))}
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {(resourcePermissions as any[]).map((permission: any) => (
                                  <TableRow key={permission.id}>
                                    <TableCell>
                                      <div className="space-y-1">
                                        <div className="font-medium text-sm">
                                          {permission.display_name}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                          {permission.description}
                                        </div>
                                        <Badge variant="outline" className="text-xs">
                                          {permission.action}
                                        </Badge>
                                      </div>
                                    </TableCell>
                                    {filteredRoles.map((role: any) => (
                                      <TableCell key={role.id} className="text-center">
                                        <Checkbox
                                          checked={pendingChanges[role.id]?.includes(permission.id) || false}
                                          onCheckedChange={(checked) =>
                                            handlePermissionToggle(role.id, permission.id, checked as boolean)
                                          }
                                        />
                                      </TableCell>
                                    ))}
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </ScrollArea>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="summary">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredRoles.map((role: any) => (
              <Card key={role.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{role.display_name}</CardTitle>
                    <Badge variant={role.type === 'system' ? 'default' : 'secondary'}>
                      {role.type}
                    </Badge>
                  </div>
                  <CardDescription>{role.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Permission count */}
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Total Permissions</span>
                      <Badge variant="outline">
                        {getRolePermissionCount(role.id)}
                      </Badge>
                    </div>

                    {/* Permission breakdown by resource */}
                    <div className="space-y-2">
                      <span className="text-sm font-medium">By Resource Type</span>
                      {Object.entries(permissionsByResource).map(([resourceType, resourcePermissions]) => {
                        const count = (resourcePermissions as any[]).filter((p: any) => 
                          pendingChanges[role.id]?.includes(p.id)
                        ).length;
                        
                        if (count === 0) return null;
                        
                        const ResourceIcon = getResourceIcon(resourceType);
                        
                        return (
                          <div key={resourceType} className="flex items-center justify-between text-sm">
                            <div className="flex items-center space-x-2">
                              <ResourceIcon className="h-3 w-3" />
                              <span className="capitalize">{resourceType.replace('_', ' ')}</span>
                            </div>
                            <span>{count}</span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Status indicator */}
                    <div className="pt-2 border-t">
                      {hasChanges() && Object.keys(pendingChanges).includes(role.id) ? (
                        <div className="flex items-center space-x-2 text-yellow-600">
                          <AlertTriangle className="h-4 w-4" />
                          <span className="text-xs">Pending changes</span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2 text-green-600">
                          <CheckCircle className="h-4 w-4" />
                          <span className="text-xs">Up to date</span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}