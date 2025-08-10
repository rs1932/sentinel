'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Search, 
  Grid3X3, 
  Shield, 
  Users, 
  RefreshCw,
  Info
} from 'lucide-react';

export function PermissionMatrixView() {
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch roles
  const { data: rolesResponse, isLoading: rolesLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => apiClient.roles.list({ limit: 100 }),
  });

  // Fetch permissions
  const { data: permissionsResponse, isLoading: permissionsLoading } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => apiClient.permissions.list(),
  });

  // Fetch role-permission relationships for each role
  const roles = rolesResponse?.items || rolesResponse || [];
  const permissions = permissionsResponse?.items || permissionsResponse || [];

  // Filter permissions based on search
  const filteredPermissions = permissions.filter((permission: any) =>
    permission.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    permission.resource_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const isLoading = rolesLoading || permissionsLoading;

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getResourceTypeColor = (resourceType: string) => {
    switch (resourceType) {
      case 'product_family': return 'bg-teal-100 text-teal-800';
      case 'app': return 'bg-indigo-100 text-indigo-800';
      case 'capability': return 'bg-pink-100 text-pink-800';
      case 'service': return 'bg-orange-100 text-orange-800';
      case 'entity': return 'bg-blue-100 text-blue-800';
      case 'api': return 'bg-green-100 text-green-800';
      case 'page': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Grid3X3 className="h-5 w-5 text-blue-600" />
              <div>
                <CardTitle>Role-Permission Matrix</CardTitle>
                <CardDescription>
                  Visual matrix showing which roles have which permissions
                </CardDescription>
              </div>
            </div>
            <Button variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>

          {/* Search */}
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search permissions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="text-sm text-gray-600">
              {roles.length} roles × {filteredPermissions.length} permissions
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {roles.length === 0 || filteredPermissions.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Grid3X3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium mb-2">No data available</h3>
              <p>
                {roles.length === 0 
                  ? 'No roles found. Create some roles first.'
                  : 'No permissions found matching your search.'
                }
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Info message */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900">Matrix View</h4>
                    <p className="text-sm text-blue-800 mt-1">
                      This view shows which roles have which permissions. Check marks indicate active permissions.
                      This is a read-only view - use the individual role or permission pages to make changes.
                    </p>
                  </div>
                </div>
              </div>

              {/* Matrix Table */}
              <div className="border rounded-lg overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="min-w-[300px] sticky left-0 bg-white z-10">
                        Permission
                      </TableHead>
                      {roles.map((role: any) => (
                        <TableHead key={role.id} className="text-center min-w-[120px]">
                          <div className="flex flex-col items-center gap-1">
                            <Shield className="h-4 w-4 text-gray-500" />
                            <span className="text-xs font-medium">{role.display_name || role.name}</span>
                            <Badge variant="outline" className="text-xs">
                              {role.type}
                            </Badge>
                          </div>
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredPermissions.map((permission: any) => (
                      <TableRow key={permission.id}>
                        <TableCell className="sticky left-0 bg-white z-10 border-r">
                          <div className="space-y-1">
                            <div className="font-medium text-sm">{permission.name}</div>
                            <div className="flex items-center gap-2">
                              <Badge 
                                variant="outline" 
                                className={getResourceTypeColor(permission.resource_type)}
                              >
                                {permission.resource_type.replace('_', ' ')}
                              </Badge>
                              <div className="flex gap-1">
                                {permission.actions.slice(0, 2).map((action: string, idx: number) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    {action}
                                  </Badge>
                                ))}
                                {permission.actions.length > 2 && (
                                  <Badge variant="outline" className="text-xs bg-gray-100">
                                    +{permission.actions.length - 2}
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-gray-500">
                              {permission.resource_path || permission.resource_id || 'Global'}
                            </div>
                          </div>
                        </TableCell>
                        {roles.map((role: any) => (
                          <TableCell key={role.id} className="text-center">
                            {/* This is a simplified view - in a real implementation, 
                                you would query the role-permission relationships */}
                            <div className="flex justify-center">
                              <Checkbox 
                                checked={false} // This should be based on actual role-permission data
                                disabled
                                className="cursor-not-allowed"
                              />
                            </div>
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Legend */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Legend</h4>
                <div className="flex items-center gap-6 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <Checkbox checked disabled />
                    <span>Permission assigned</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox disabled />
                    <span>Permission not assigned</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Note: This is a read-only matrix view. To assign or remove permissions, 
                  use the individual role management or permission management pages.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}