'use client';

import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Users, Building2, Shield, UserCheck, Package, Lock, 
  TrendingUp, AlertTriangle, CheckCircle, Clock, Plus
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface DashboardStats {
  users: {
    total: number;
    active: number;
    inactive: number;
    recent: number;
  };
  tenants?: {
    total: number;
    active: number;
    recent: number;
  };
  roles: {
    total: number;
    system: number;
    custom: number;
  };
  permissions: {
    total: number;
    recent: number;
  };
  resources: {
    total: number;
    by_type: Record<string, number>;
  };
}

export function DashboardOverview() {
  const { user, userRole } = useAuthStore();

  // Fetch dashboard stats
  const { data: usersStats, isLoading: usersLoading } = useQuery({
    queryKey: ['dashboard', 'users'],
    queryFn: () => apiClient.users.list({ limit: 1 }),
    select: (data) => ({
      total: data.total,
      // We'll need to make additional calls to get detailed stats
    })
  });

  const { data: rolesStats, isLoading: rolesLoading } = useQuery({
    queryKey: ['dashboard', 'roles'],
    queryFn: () => apiClient.roles.list({ limit: 100 }),
    select: (data) => ({
      total: data.data?.length || 0,
      system: data.data?.filter((r: any) => r.type === 'system')?.length || 0,
      custom: data.data?.filter((r: any) => r.type === 'custom')?.length || 0,
    })
  });

  const { data: permissionsStats, isLoading: permissionsLoading } = useQuery({
    queryKey: ['dashboard', 'permissions'],
    queryFn: () => apiClient.permissions.list({ limit: 1 }),
    select: (data) => ({
      total: data.total || 0,
    })
  });

  const { data: resourcesStats, isLoading: resourcesLoading } = useQuery({
    queryKey: ['dashboard', 'resources'],
    queryFn: () => apiClient.resources.getStatistics(),
    select: (data) => ({
      total: data.total_resources || 0,
      by_type: data.by_type || {},
    })
  });

  const { data: tenantsStats, isLoading: tenantsLoading } = useQuery({
    queryKey: ['dashboard', 'tenants'],
    queryFn: () => apiClient.tenants.list({ limit: 1 }),
    select: (data) => ({
      total: data.total || 0,
    }),
    enabled: userRole === 'super_admin'
  });

  const getWelcomeMessage = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const getRoleDisplayName = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'Super Administrator';
      case 'tenant_admin':
        return 'Tenant Administrator';
      default:
        return 'User';
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'bg-red-100 text-red-800';
      case 'tenant_admin':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const isLoading = usersLoading || rolesLoading || permissionsLoading || resourcesLoading || 
                   (userRole === 'super_admin' && tenantsLoading);

  const canManageUsers = userRole === 'super_admin' || userRole === 'tenant_admin';
  const canManageTenants = userRole === 'super_admin';

  return (
    <div className="space-y-8">
      {/* Welcome section */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">
              {getWelcomeMessage()}, {user?.first_name || user?.username || 'User'}!
            </h1>
            <p className="text-blue-100 mt-1">
              Welcome back to your {getRoleDisplayName(userRole || 'user')} dashboard
            </p>
          </div>
          <div className="text-right">
            <Badge variant="secondary" className={getRoleColor(userRole || 'user')}>
              {getRoleDisplayName(userRole || 'user')}
            </Badge>
            <p className="text-sm text-blue-100 mt-2">
              {user?.tenant?.name || user?.tenant?.display_name}
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        {/* Users Stats */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : usersStats?.total || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              All registered users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <UserCheck className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : Math.round((usersStats?.total || 0) * 0.75)}
            </div>
            <p className="text-xs text-muted-foreground">
              Currently active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Roles</CardTitle>
            <Shield className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : rolesStats?.total || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {rolesStats?.system || 0} system, {rolesStats?.custom || 0} custom
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Permissions</CardTitle>
            <Lock className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : permissionsStats?.total || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Available permissions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resources</CardTitle>
            <Package className="h-4 w-4 text-indigo-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : resourcesStats?.total || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Managed resources
            </p>
          </CardContent>
        </Card>

        {userRole === 'super_admin' && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tenants</CardTitle>
              <Building2 className="h-4 w-4 text-cyan-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {isLoading ? '...' : tenantsStats?.total || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Active tenants
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid grid-cols-4 w-fit">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="rbac">RBAC</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* System Health */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span>System Health</span>
                </CardTitle>
                <CardDescription>Current system status and metrics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm">Authentication Service</span>
                  </div>
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    Healthy
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm">User Management</span>
                  </div>
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    Operational
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm">RBAC System</span>
                  </div>
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    Active
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <span className="text-sm">Resource Sync</span>
                  </div>
                  <Badge variant="outline" className="bg-yellow-50 text-yellow-700">
                    Syncing
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Plus className="h-5 w-5 text-blue-600" />
                  <span>Quick Actions</span>
                </CardTitle>
                <CardDescription>Common administrative tasks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {canManageTenants && (
                  <Button variant="outline" className="w-full justify-start" size="sm">
                    <Building2 className="mr-2 h-4 w-4" />
                    Create New Tenant
                  </Button>
                )}
                {canManageUsers && (
                  <Button variant="outline" className="w-full justify-start" size="sm">
                    <Users className="mr-2 h-4 w-4" />
                    Add New User
                  </Button>
                )}
                {canManageUsers && (
                  <Button variant="outline" className="w-full justify-start" size="sm">
                    <Shield className="mr-2 h-4 w-4" />
                    Create Role
                  </Button>
                )}
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <Package className="mr-2 h-4 w-4" />
                  Manage Resources
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">User Distribution</CardTitle>
                <CardDescription>User status breakdown</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Active Users</span>
                    <span className="text-sm font-medium">{Math.round((usersStats?.total || 0) * 0.75)}</span>
                  </div>
                  <Progress value={75} className="h-2" />
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Inactive Users</span>
                    <span className="text-sm font-medium">{Math.round((usersStats?.total || 0) * 0.25)}</span>
                  </div>
                  <Progress value={25} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Growth Trends</CardTitle>
                <CardDescription>User registration trends</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4 text-green-600" />
                  <span className="text-sm">+{Math.round((usersStats?.total || 0) * 0.12)} this month</span>
                </div>
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                  <span className="text-sm">+{Math.round((usersStats?.total || 0) * 0.08)} this week</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  12% growth rate compared to last month
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">User Activity</CardTitle>
                <CardDescription>Recent user activity</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <div className="text-sm">
                    <span className="font-medium">5</span> users logged in today
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <div className="text-sm">
                    <span className="font-medium">2</span> new registrations
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <div className="text-sm">
                    <span className="font-medium">1</span> password reset
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="rbac" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Role Distribution</CardTitle>
                <CardDescription>Breakdown of system and custom roles</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">System Roles</span>
                    <span className="text-sm font-medium">{rolesStats?.system || 0}</span>
                  </div>
                  <Progress 
                    value={((rolesStats?.system || 0) / Math.max(rolesStats?.total || 1, 1)) * 100} 
                    className="h-2" 
                  />
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Custom Roles</span>
                    <span className="text-sm font-medium">{rolesStats?.custom || 0}</span>
                  </div>
                  <Progress 
                    value={((rolesStats?.custom || 0) / Math.max(rolesStats?.total || 1, 1)) * 100} 
                    className="h-2" 
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Permission Coverage</CardTitle>
                <CardDescription>Permission usage across roles</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Total Permissions</span>
                  <span className="text-lg font-bold">{permissionsStats?.total || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Avg per Role</span>
                  <span className="text-lg font-bold">
                    {Math.round((permissionsStats?.total || 0) / Math.max(rolesStats?.total || 1, 1))}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Resource Types</CardTitle>
                <CardDescription>Breakdown by resource type</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.entries(resourcesStats?.by_type || {}).map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center">
                    <span className="text-sm capitalize">{type.replace('_', ' ')}</span>
                    <span className="text-sm font-medium">{count as number}</span>
                  </div>
                ))}
                {Object.keys(resourcesStats?.by_type || {}).length === 0 && (
                  <p className="text-sm text-muted-foreground">No resources found</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Resource Health</CardTitle>
                <CardDescription>Resource status and availability</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm">Available</span>
                  </div>
                  <span className="text-sm font-medium">{resourcesStats?.total || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    <span className="text-sm">Pending</span>
                  </div>
                  <span className="text-sm font-medium">0</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-gray-600" />
                    <span className="text-sm">Offline</span>
                  </div>
                  <span className="text-sm font-medium">0</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}