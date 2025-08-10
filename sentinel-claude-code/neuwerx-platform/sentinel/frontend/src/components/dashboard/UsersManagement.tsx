'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Search, Plus, MoreHorizontal, Mail, Phone, UserCheck, UserX, 
  Shield, Settings, Trash2, Edit, Lock, Unlock, Users, BarChart3,
  Filter, Download, Upload, ChevronDown
} from 'lucide-react';
import { CreateUserDialog } from '@/components/users/CreateUserDialog';
import { EditUserDialog } from '@/components/users/EditUserDialog';
import { UserDetailDialog } from '@/components/users/UserDetailDialog';
import { AssignRoleDialog } from '@/components/users/AssignRoleDialog';
import { BulkActionsDialog } from '@/components/users/BulkActionsDialog';
import { apiClient } from '@/lib/api';

interface User {
  id: string;
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_service_account: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
  roles?: Array<{
    id: string;
    name: string;
    display_name: string;
  }>;
  groups?: Array<{
    id: string;
    name: string;
    display_name: string;
  }>;
  attributes?: Record<string, any>;
}

interface UserStats {
  total: number;
  active: number;
  inactive: number;
  admin_users: number;
  service_accounts: number;
  recent_signups: number;
}

export function UsersManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  
  // Dialog states
  const [createUserOpen, setCreateUserOpen] = useState(false);
  const [editUserOpen, setEditUserOpen] = useState(false);
  const [userDetailOpen, setUserDetailOpen] = useState(false);
  const [assignRoleOpen, setAssignRoleOpen] = useState(false);
  const [bulkActionsOpen, setBulkActionsOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  
  // Selected user for operations
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  
  const { userRole, user: currentUser } = useAuthStore();
  const queryClient = useQueryClient();

  const canManageUsers = userRole === 'super_admin' || userRole === 'tenant_admin';
  const canViewUsers = userRole === 'super_admin' || userRole === 'tenant_admin';

  // Fetch users
  const {
    data: usersResponse,
    isLoading: usersLoading,
    error: usersError,
    refetch: refetchUsers
  } = useQuery({
    queryKey: ['users', page, pageSize, searchTerm, statusFilter, roleFilter],
    queryFn: () => apiClient.users.list({
      page,
      limit: pageSize,
      search: searchTerm || undefined,
      is_active: statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined,
      sort: 'created_at',
      order: 'desc'
    }),
    enabled: canViewUsers
  });

  // Fetch roles for filtering
  const { data: rolesResponse } = useQuery({
    queryKey: ['roles'],
    queryFn: () => apiClient.roles.list(),
    enabled: canViewUsers
  });

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (userId: string) => apiClient.users.delete(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setDeleteConfirmOpen(false);
      setUserToDelete(null);
    }
  });

  // Bulk operations mutation
  const bulkOperationMutation = useMutation({
    mutationFn: ({ action, userIds }: { action: string; userIds: string[] }) => 
      apiClient.users.bulk(action, userIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setSelectedUsers([]);
    }
  });

  const users = usersResponse?.data || [];
  const totalUsers = usersResponse?.total || 0;
  const roles = rolesResponse?.data || [];

  const getUserInitials = (firstName?: string, lastName?: string) => {
    if (!firstName && !lastName) return 'U';
    return `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase();
  };

  const getUserDisplayName = (user: User) => {
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return user.username || user.email.split('@')[0];
  };

  const handleSelectUser = (userId: string, checked: boolean) => {
    if (checked) {
      setSelectedUsers([...selectedUsers, userId]);
    } else {
      setSelectedUsers(selectedUsers.filter(id => id !== userId));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedUsers(users.map((user: any) => user.id));
    } else {
      setSelectedUsers([]);
    }
  };

  const handleUserAction = (user: User, action: string) => {
    setSelectedUser(user);
    switch (action) {
      case 'edit':
        setEditUserOpen(true);
        break;
      case 'detail':
        setUserDetailOpen(true);
        break;
      case 'assign-role':
        setAssignRoleOpen(true);
        break;
      case 'delete':
        setUserToDelete(user);
        setDeleteConfirmOpen(true);
        break;
    }
  };

  const calculateStats = (): UserStats => {
    const total = totalUsers;
    const activeUsers = users.filter((u: any) => u.is_active);
    const adminUsers = users.filter((u: any) => 
      u.roles?.some((r: any) => r.name.toLowerCase().includes('admin'))
    );
    const serviceAccounts = users.filter((u: any) => u.is_service_account);
    
    // Calculate recent signups (last 30 days)
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const recentSignups = users.filter((u: any) => 
      new Date(u.created_at) > thirtyDaysAgo
    );

    return {
      total,
      active: activeUsers.length,
      inactive: total - activeUsers.length,
      admin_users: adminUsers.length,
      service_accounts: serviceAccounts.length,
      recent_signups: recentSignups.length
    };
  };

  const stats = calculateStats();

  if (!canViewUsers) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Shield className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Access Denied</h3>
          <p className="text-gray-600">You don't have permission to view user management.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-600">
            Manage users and their permissions across your organization
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {canManageUsers && selectedUsers.length > 0 && (
            <Button 
              variant="outline" 
              onClick={() => setBulkActionsOpen(true)}
            >
              <Settings className="mr-2 h-4 w-4" />
              Bulk Actions ({selectedUsers.length})
            </Button>
          )}
          {canManageUsers && (
            <Button 
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => setCreateUserOpen(true)}
            >
              <Plus className="mr-2 h-4 w-4" />
              Add User
            </Button>
          )}
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Users className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Total</p>
                <p className="text-lg font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <UserCheck className="h-4 w-4 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Active</p>
                <p className="text-lg font-bold">{stats.active}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <UserX className="h-4 w-4 text-red-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Inactive</p>
                <p className="text-lg font-bold">{stats.inactive}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Shield className="h-4 w-4 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Admins</p>
                <p className="text-lg font-bold">{stats.admin_users}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Settings className="h-4 w-4 text-orange-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Service</p>
                <p className="text-lg font-bold">{stats.service_accounts}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <BarChart3 className="h-4 w-4 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Recent</p>
                <p className="text-lg font-bold">{stats.recent_signups}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Users</CardTitle>
              <CardDescription>
                {totalUsers} user{totalUsers !== 1 ? 's' : ''} found
              </CardDescription>
            </div>
            <div className="flex items-center space-x-3">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search users..."
                  className="pl-10 w-64"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              {/* Status filter */}
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

              {/* Role filter */}
              <Select value={roleFilter} onValueChange={setRoleFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Roles</SelectItem>
                  {roles.map((role: any) => (
                    <SelectItem key={role.id} value={role.id}>
                      {role.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {usersError && (
            <Alert className="mb-4" variant="destructive">
              <AlertDescription>
                Failed to load users: {usersError.message}
              </AlertDescription>
            </Alert>
          )}

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  {canManageUsers && (
                    <TableHead className="w-[50px]">
                      <Checkbox
                        checked={selectedUsers.length === users.length && users.length > 0}
                        onCheckedChange={handleSelectAll}
                      />
                    </TableHead>
                  )}
                  <TableHead className="w-[50px]"></TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Roles</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-[50px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usersLoading ? (
                  <TableRow>
                    <TableCell colSpan={canManageUsers ? 9 : 8} className="text-center py-8">
                      Loading users...
                    </TableCell>
                  </TableRow>
                ) : users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={canManageUsers ? 9 : 8} className="text-center py-8">
                      No users found
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user: any) => (
                    <TableRow key={user.id}>
                      {canManageUsers && (
                        <TableCell>
                          <Checkbox
                            checked={selectedUsers.includes(user.id)}
                            onCheckedChange={(checked) => 
                              handleSelectUser(user.id, checked as boolean)
                            }
                          />
                        </TableCell>
                      )}
                      <TableCell>
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={`https://avatar.vercel.sh/${user.email}`} />
                          <AvatarFallback className="text-xs">
                            {getUserInitials(user.first_name, user.last_name)}
                          </AvatarFallback>
                        </Avatar>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">
                          {getUserDisplayName(user)}
                        </div>
                        <div className="text-sm text-gray-500">
                          {user.is_service_account && (
                            <Badge variant="outline" className="text-xs mr-1">
                              Service
                            </Badge>
                          )}
                          ID: {user.id.substring(0, 8)}...
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center text-sm">
                          <Mail className="mr-1 h-3 w-3 text-gray-400" />
                          {user.email}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {user.roles?.map((role: any) => (
                            <Badge key={role.id} variant="secondary" className="text-xs">
                              {role.display_name}
                            </Badge>
                          )) || (
                            <span className="text-xs text-gray-500">No roles</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={user.is_active ? "default" : "secondary"}
                          className={
                            user.is_active
                              ? "bg-green-100 text-green-800 hover:bg-green-100"
                              : "bg-red-100 text-red-800 hover:bg-red-100"
                          }
                        >
                          {user.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {user.last_login 
                          ? new Date(user.last_login).toLocaleDateString()
                          : 'Never'
                        }
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {new Date(user.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem onClick={() => handleUserAction(user, 'detail')}>
                              <Users className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            {canManageUsers && (
                              <>
                                <DropdownMenuItem onClick={() => handleUserAction(user, 'edit')}>
                                  <Edit className="mr-2 h-4 w-4" />
                                  Edit User
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleUserAction(user, 'assign-role')}>
                                  <Shield className="mr-2 h-4 w-4" />
                                  Assign Roles
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                {user.is_active ? (
                                  <DropdownMenuItem>
                                    <Lock className="mr-2 h-4 w-4" />
                                    Deactivate
                                  </DropdownMenuItem>
                                ) : (
                                  <DropdownMenuItem>
                                    <Unlock className="mr-2 h-4 w-4" />
                                    Activate
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuSeparator />
                                <DropdownMenuItem 
                                  className="text-red-600"
                                  onClick={() => handleUserAction(user, 'delete')}
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete User
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalUsers > pageSize && (
            <div className="flex items-center justify-between pt-4">
              <div className="text-sm text-gray-500">
                Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, totalUsers)} of {totalUsers} users
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page * pageSize >= totalUsers}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialogs */}
      <CreateUserDialog
        open={createUserOpen}
        onOpenChange={setCreateUserOpen}
        onSuccess={() => {
          refetchUsers();
          setCreateUserOpen(false);
        }}
      />

      {selectedUser && (
        <EditUserDialog
          open={editUserOpen}
          onOpenChange={setEditUserOpen}
          user={selectedUser as any}
          onSuccess={() => {
            refetchUsers();
            setEditUserOpen(false);
          }}
        />
      )}

      {selectedUser && (
        <UserDetailDialog
          open={userDetailOpen}
          onOpenChange={setUserDetailOpen}
          user={selectedUser as any}
        />
      )}

      {selectedUser && (
        <AssignRoleDialog
          open={assignRoleOpen}
          onOpenChange={setAssignRoleOpen}
          user={selectedUser as any}
          onSuccess={() => {
            refetchUsers();
            setAssignRoleOpen(false);
          }}
        />
      )}

      <BulkActionsDialog
        open={bulkActionsOpen}
        onOpenChange={setBulkActionsOpen}
        selectedUsers={selectedUsers}
        users={users}
        onSuccess={() => {
          refetchUsers();
          setBulkActionsOpen(false);
        }}
      />

      {/* Delete confirmation dialog */}
      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete {userToDelete?.first_name} {userToDelete?.last_name}?
              This action cannot be undone and will remove all user data and access permissions.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => userToDelete && deleteUserMutation.mutate(userToDelete.id)}
              disabled={deleteUserMutation.isPending}
            >
              {deleteUserMutation.isPending ? 'Deleting...' : 'Delete User'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}