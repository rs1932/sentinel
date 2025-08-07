'use client';

import { useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Search, Plus, MoreHorizontal, Building2, Users, Settings } from 'lucide-react';

// Mock data for demonstration
const mockTenants = [
  {
    id: '1',
    name: 'acme-corp',
    display_name: 'ACME Corporation',
    type: 'root' as const,
    parent_tenant_id: null,
    isolation_mode: 'shared' as const,
    features: ['users', 'roles', 'reports'],
    settings: { theme: 'blue', locale: 'en-US' },
    is_active: true,
    user_count: 45,
    created_at: '2024-01-15',
  },
  {
    id: '2',
    name: 'acme-hr',
    display_name: 'ACME HR Department',
    type: 'sub_tenant' as const,
    parent_tenant_id: '1',
    isolation_mode: 'shared' as const,
    features: ['users', 'reports'],
    settings: { theme: 'green', locale: 'en-US' },
    is_active: true,
    user_count: 12,
    created_at: '2024-01-20',
  },
  {
    id: '3',
    name: 'techstart-inc',
    display_name: 'TechStart Inc',
    type: 'root' as const,
    parent_tenant_id: null,
    isolation_mode: 'dedicated' as const,
    features: ['users', 'roles', 'reports', 'api'],
    settings: { theme: 'purple', locale: 'en-US' },
    is_active: true,
    user_count: 28,
    created_at: '2024-02-01',
  },
  {
    id: '4',
    name: 'global-solutions',
    display_name: 'Global Solutions Ltd',
    type: 'root' as const,
    parent_tenant_id: null,
    isolation_mode: 'shared' as const,
    features: ['users', 'roles'],
    settings: { theme: 'red', locale: 'en-GB' },
    is_active: false,
    user_count: 8,
    created_at: '2024-01-10',
  },
];

export function TenantsManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const { userRole } = useAuthStore();

  const canManageTenants = userRole === 'super_admin';

  const filteredTenants = mockTenants.filter(tenant =>
    `${tenant.display_name} ${tenant.name}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  const getTenantTypeColor = (type: string) => {
    switch (type) {
      case 'root':
        return 'bg-purple-100 text-purple-800 hover:bg-purple-100';
      case 'sub_tenant':
        return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
    }
  };

  const getIsolationColor = (mode: string) => {
    switch (mode) {
      case 'dedicated':
        return 'bg-orange-100 text-orange-800 hover:bg-orange-100';
      case 'shared':
        return 'bg-green-100 text-green-800 hover:bg-green-100';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tenant Management</h1>
          <p className="text-gray-600">
            Manage organizations and their configurations across the platform
          </p>
        </div>
        {canManageTenants && (
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="mr-2 h-4 w-4" />
            Create Tenant
          </Button>
        )}
      </div>

      {canManageTenants ? (
        <>
          {/* Search and filters */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Tenants</CardTitle>
                  <CardDescription>
                    {filteredTenants.length} tenant{filteredTenants.length !== 1 ? 's' : ''} found
                  </CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search tenants..."
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
                      <TableHead>Organization</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Isolation</TableHead>
                      <TableHead>Users</TableHead>
                      <TableHead>Features</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[50px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTenants.map((tenant) => (
                      <TableRow key={tenant.id}>
                        <TableCell>
                          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                            <Building2 className="h-4 w-4 text-blue-600" />
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{tenant.display_name}</div>
                            <div className="text-sm text-gray-500">{tenant.name}</div>
                            <div className="text-xs text-gray-400 mt-1">
                              Created: {new Date(tenant.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={getTenantTypeColor(tenant.type)}
                          >
                            {tenant.type === 'root' ? 'Root' : 'Sub-tenant'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={getIsolationColor(tenant.isolation_mode)}
                          >
                            {tenant.isolation_mode}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center text-sm">
                            <Users className="mr-1 h-3 w-3 text-gray-400" />
                            {tenant.user_count}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {tenant.features.slice(0, 2).map((feature, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {feature}
                              </Badge>
                            ))}
                            {tenant.features.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{tenant.features.length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={tenant.is_active ? "default" : "secondary"}
                            className={
                              tenant.is_active
                                ? "bg-green-100 text-green-800 hover:bg-green-100"
                                : "bg-red-100 text-red-800 hover:bg-red-100"
                            }
                          >
                            {tenant.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </TableCell>
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
                  Total Tenants
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockTenants.length}</div>
                <p className="text-xs text-gray-500">All organizations</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Active Tenants
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {mockTenants.filter(t => t.is_active).length}
                </div>
                <p className="text-xs text-gray-500">Currently active</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Root Tenants
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {mockTenants.filter(t => t.type === 'root').length}
                </div>
                <p className="text-xs text-gray-500">Primary organizations</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Total Users
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {mockTenants.reduce((sum, tenant) => sum + tenant.user_count, 0)}
                </div>
                <p className="text-xs text-gray-500">Across all tenants</p>
              </CardContent>
            </Card>
          </div>
        </>
      ) : (
        /* Access denied for non-super-admin users */
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Building2 className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Access Restricted</h3>
            <p className="text-gray-600 text-center">
              Tenant management is only available to Super Administrators.
              <br />
              Contact your system administrator for access.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}