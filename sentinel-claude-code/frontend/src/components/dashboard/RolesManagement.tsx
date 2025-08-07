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
import { Search, Plus, MoreHorizontal, Shield, Users } from 'lucide-react';

// Mock data for demonstration
const mockRoles = [
  {
    id: '1',
    name: 'super_admin',
    display_name: 'Super Administrator',
    description: 'Full system access with all permissions',
    type: 'system' as const,
    priority: 100,
    is_assignable: true,
    user_count: 2,
    tenant_id: 'system',
  },
  {
    id: '2',
    name: 'tenant_admin',
    display_name: 'Tenant Administrator',
    description: 'Manage users and settings within the organization',
    type: 'system' as const,
    priority: 90,
    is_assignable: true,
    user_count: 5,
    tenant_id: 'system',
  },
  {
    id: '3',
    name: 'user',
    display_name: 'Standard User',
    description: 'Basic access to application features',
    type: 'system' as const,
    priority: 10,
    is_assignable: true,
    user_count: 28,
    tenant_id: 'system',
  },
  {
    id: '4',
    name: 'hr_manager',
    display_name: 'HR Manager',
    description: 'Manage employee data and HR processes',
    type: 'custom' as const,
    priority: 50,
    is_assignable: true,
    user_count: 3,
    tenant_id: '1',
  },
];

export function RolesManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const { userRole } = useAuthStore();

  const canManageRoles = userRole === 'super_admin' || userRole === 'tenant_admin';

  const filteredRoles = mockRoles.filter(role =>
    `${role.display_name} ${role.description} ${role.name}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  const getRoleTypeColor = (type: string) => {
    switch (type) {
      case 'system':
        return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
      case 'custom':
        return 'bg-green-100 text-green-800 hover:bg-green-100';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
    }
  };

  const getPriorityColor = (priority: number) => {
    if (priority >= 90) return 'bg-red-100 text-red-800 hover:bg-red-100';
    if (priority >= 50) return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100';
    return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Role Management</h1>
          <p className="text-gray-600">
            Manage roles and their permissions across your organization
          </p>
        </div>
        {canManageRoles && (
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="mr-2 h-4 w-4" />
            Create Role
          </Button>
        )}
      </div>

      {/* Search and filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Roles</CardTitle>
              <CardDescription>
                {filteredRoles.length} role{filteredRoles.length !== 1 ? 's' : ''} found
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search roles..."
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
                  <TableHead>Role</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Users</TableHead>
                  <TableHead>Status</TableHead>
                  {canManageRoles && (
                    <TableHead className="w-[50px]">Actions</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRoles.map((role) => (
                  <TableRow key={role.id}>
                    <TableCell>
                      <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Shield className="h-4 w-4 text-blue-600" />
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{role.display_name}</div>
                        <div className="text-sm text-gray-500">{role.description}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          ID: {role.name}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={getRoleTypeColor(role.type)}
                      >
                        {role.type === 'system' ? 'System' : 'Custom'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={getPriorityColor(role.priority)}
                      >
                        {role.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center text-sm">
                        <Users className="mr-1 h-3 w-3 text-gray-400" />
                        {role.user_count}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={role.is_assignable ? "default" : "secondary"}
                        className={
                          role.is_assignable
                            ? "bg-green-100 text-green-800 hover:bg-green-100"
                            : "bg-gray-100 text-gray-800 hover:bg-gray-100"
                        }
                      >
                        {role.is_assignable ? 'Assignable' : 'System Only'}
                      </Badge>
                    </TableCell>
                    {canManageRoles && (
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              System Roles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockRoles.filter(r => r.type === 'system').length}
            </div>
            <p className="text-xs text-gray-500">Built-in roles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Custom Roles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockRoles.filter(r => r.type === 'custom').length}
            </div>
            <p className="text-xs text-gray-500">Organization-specific</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Assignments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockRoles.reduce((sum, role) => sum + role.user_count, 0)}
            </div>
            <p className="text-xs text-gray-500">Role assignments</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}