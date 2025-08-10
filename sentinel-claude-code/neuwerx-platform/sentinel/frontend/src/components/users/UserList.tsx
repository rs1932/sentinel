'use client';

import { useState, useEffect, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  MoreHorizontal, 
  Users, 
  UserCheck, 
  UserX, 
  Eye,
  Edit,
  Trash2,
  Shield,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Building,
  Key
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
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
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { apiClient } from '@/lib/api';
import { useDebounce } from '@/hooks/useDebounce';
import { useAuthStore } from '@/store/auth';
import { UserDetailDialog } from './UserDetailDialog';
import { EditUserDialog } from './EditUserDialog';
import { DeleteUserDialog } from './DeleteUserDialog';
import { PasswordResetDialog } from './PasswordResetDialog';
import { BulkActionsBar } from './BulkActionsBar';
import { useBulkOperations } from './BulkOperationsProvider';

interface User {
  id: string;
  email: string;
  username?: string;
  attributes: {
    department?: string;
    location?: string;
    [key: string]: any;
  };
  tenant?: {
    id: string;
    name: string;
    code: string;
  };
  is_active: boolean;
  last_login?: string;
  login_count: number;
  created_at: string;
  updated_at: string;
}

interface UserListResponse {
  items: User[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

interface UserListProps {
  onCountUpdate?: (count: number) => void;
}

export function UserList({ onCountUpdate }: UserListProps = {}) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { userRole } = useAuthStore();
  const isSuperAdmin = userRole === 'super_admin';
  
  const {
    selectedUsers,
    isSelecting,
    selectUser,
    deselectUser,
    selectAll,
    clearSelection,
    toggleSelecting,
    performBulkAction,
  } = useBulkOperations();
  
  // Filters and pagination
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [tenantFilter, setTenantFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [pagination, setPagination] = useState({
    total: 0,
    pages: 0
  });

  // Tenant data for filtering
  const [tenants, setTenants] = useState<any[]>([]);
  const [loadingTenants, setLoadingTenants] = useState(false);

  // Dialogs
  const [showUserDetail, setShowUserDetail] = useState<User | null>(null);
  const [showEditUser, setShowEditUser] = useState<User | null>(null);
  const [showDeleteUser, setShowDeleteUser] = useState<User | null>(null);
  const [showPasswordReset, setShowPasswordReset] = useState<User | null>(null);

  const debouncedSearch = useDebounce(searchTerm, 300);

  // Load tenants for super admin
  useEffect(() => {
    if (isSuperAdmin) {
      loadTenants();
    }
  }, [isSuperAdmin]);

  // Load users effect
  useEffect(() => {
    loadUsers();
  }, [debouncedSearch, statusFilter, tenantFilter, sortBy, sortOrder, currentPage, pageSize]);

  // Listen for refresh events
  useEffect(() => {
    const handleRefresh = () => loadUsers();
    window.addEventListener('refreshUsers', handleRefresh);
    return () => window.removeEventListener('refreshUsers', handleRefresh);
  }, []);

  const loadTenants = async () => {
    try {
      setLoadingTenants(true);
      const response = await apiClient.tenants.list();
      setTenants(response.items || []);
    } catch (err: any) {
      console.error('Failed to load tenants:', err);
    } finally {
      setLoadingTenants(false);
    }
  };

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: Record<string, any> = {
        page: currentPage,
        limit: pageSize,
        sort: sortBy,
        order: sortOrder
      };

      if (debouncedSearch) {
        params.search = debouncedSearch;
      }

      if (statusFilter !== 'all') {
        params.is_active = statusFilter === 'active';
      }

      if (isSuperAdmin && tenantFilter !== 'all') {
        params.tenant_id = tenantFilter;
        console.log('🔍 Filtering users by tenant:', tenantFilter);
      }

      console.log('📡 API request params:', params);
      const response = await apiClient.users.list(params);
      console.log('📥 API response:', { total: response.total, itemCount: response.items?.length });
      
      setUsers(response.items);
      setPagination({
        total: response.total,
        pages: response.pages
      });
      
      // Update parent component with user count
      onCountUpdate?.(response.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectUser = (userId: string, checked: boolean) => {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    if (checked) {
      selectUser(user);
    } else {
      deselectUser(userId);
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      selectAll(users);
    } else {
      clearSelection();
    }
  };

  const handleBulkAction = async (action: string, userIds: string[]) => {
    await performBulkAction(action, userIds);
    loadUsers(); // Refresh the user list
  };

  const formatLastLogin = (lastLogin?: string) => {
    if (!lastLogin) return 'Never';
    return new Date(lastLogin).toLocaleDateString();
  };

  const getInitials = (email: string, username?: string) => {
    const name = username || email;
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const selectedUsersData = useMemo(() => {
    const selectedIds = new Set(selectedUsers.map(u => u.id));
    return users.filter(user => selectedIds.has(user.id));
  }, [users, selectedUsers]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-600 mb-2">Error loading users</div>
          <div className="text-sm text-muted-foreground">{error}</div>
          <Button onClick={loadUsers} className="mt-4">Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-1 items-center space-x-2">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
            </SelectContent>
          </Select>

          {/* Tenant filter - only show for super admin */}
          {isSuperAdmin && (
            <Select value={tenantFilter} onValueChange={setTenantFilter} disabled={loadingTenants}>
              <SelectTrigger className="w-[180px]">
                <Building className="mr-2 h-4 w-4" />
                <SelectValue placeholder={loadingTenants ? "Loading..." : "Select Tenant"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tenants</SelectItem>
                {tenants.map((tenant) => (
                  <SelectItem key={tenant.id} value={tenant.id}>
                    <div className="flex items-center gap-2">
                      <span>{tenant.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {tenant.code}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          <Select value={`${sortBy}-${sortOrder}`} onValueChange={(value) => {
            const [sort, order] = value.split('-');
            setSortBy(sort);
            setSortOrder(order as 'asc' | 'desc');
          }}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="created_at-desc">Newest First</SelectItem>
              <SelectItem value="created_at-asc">Oldest First</SelectItem>
              <SelectItem value="email-asc">Email A-Z</SelectItem>
              <SelectItem value="email-desc">Email Z-A</SelectItem>
              <SelectItem value="last_login-desc">Recent Login</SelectItem>
              <SelectItem value="login_count-desc">Most Active</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          <span>
            {pagination.total} users
            {isSuperAdmin && tenantFilter !== 'all' && (
              <>
                {' '}in{' '}
                <Badge variant="outline" className="text-xs">
                  {tenants.find(t => t.id === tenantFilter)?.name || 'Selected Tenant'}
                </Badge>
              </>
            )}
            {isSuperAdmin && tenantFilter === 'all' && ' across all tenants'}
          </span>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedUsers.length > 0 && (
        <BulkActionsBar
          selectedCount={selectedUsers.length}
          selectedUsers={selectedUsers}
          onBulkAction={handleBulkAction}
          onClearSelection={clearSelection}
        />
      )}

      {/* Users Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">
                <Checkbox
                  checked={selectedUsers.length === users.length && users.length > 0}
                  onCheckedChange={handleSelectAll}
                />
              </TableHead>
              <TableHead>User</TableHead>
              {isSuperAdmin && <TableHead>Tenant</TableHead>}
              <TableHead>Department</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last Login</TableHead>
              <TableHead>Logins</TableHead>
              <TableHead>Joined</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell colSpan={isSuperAdmin ? 9 : 8}>
                    <div className="flex items-center space-x-3">
                      <div className="h-8 w-8 rounded-full bg-muted animate-pulse" />
                      <div className="space-y-2">
                        <div className="h-4 w-48 bg-muted animate-pulse rounded" />
                        <div className="h-3 w-32 bg-muted animate-pulse rounded" />
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={isSuperAdmin ? 9 : 8} className="text-center py-8">
                  <div className="flex flex-col items-center space-y-2">
                    <Users className="h-8 w-8 text-muted-foreground" />
                    <div className="font-medium">No users found</div>
                    <div className="text-sm text-muted-foreground">
                      {searchTerm || statusFilter !== 'all' || (isSuperAdmin && tenantFilter !== 'all')
                        ? 'Try adjusting your search or filters'
                        : 'Get started by creating your first user'
                      }
                    </div>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <Checkbox
                      checked={selectedUsers.some(u => u.id === user.id)}
                      onCheckedChange={(checked) => handleSelectUser(user.id, !!checked)}
                    />
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-3">
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={`/api/v1/users/${user.id}/avatar`} />
                        <AvatarFallback className="text-xs">
                          {getInitials(user.email, user.username)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="font-medium">{user.username || user.email}</div>
                        {user.username && (
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  {isSuperAdmin && (
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Building className="h-3 w-3 text-muted-foreground" />
                        <div className="text-sm">
                          {user.tenant?.name || 'Unknown'}
                        </div>
                      </div>
                      {user.tenant?.code && (
                        <div className="text-xs text-muted-foreground">
                          {user.tenant.code}
                        </div>
                      )}
                    </TableCell>
                  )}
                  <TableCell>
                    <div className="text-sm">
                      {user.attributes?.department || 'N/A'}
                    </div>
                    {user.attributes.location && (
                      <div className="text-xs text-muted-foreground">
                        {user.attributes.location}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant={user.is_active ? 'default' : 'secondary'}
                      className={user.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}
                    >
                      {user.is_active ? (
                        <>
                          <UserCheck className="h-3 w-3 mr-1" />
                          Active
                        </>
                      ) : (
                        <>
                          <UserX className="h-3 w-3 mr-1" />
                          Inactive
                        </>
                      )}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatLastLogin(user.last_login)}
                  </TableCell>
                  <TableCell className="text-sm">
                    {user.login_count.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-sm">
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
                        <DropdownMenuItem onClick={() => setShowUserDetail(user)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => setShowEditUser(user)}>
                          <Edit className="h-4 w-4 mr-2" />
                          Edit User
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => setShowPasswordReset(user)}>
                          <Key className="h-4 w-4 mr-2" />
                          Reset Password
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        {user.is_active ? (
                          <DropdownMenuItem>
                            <Shield className="h-4 w-4 mr-2" />
                            Deactivate
                          </DropdownMenuItem>
                        ) : (
                          <DropdownMenuItem>
                            <ShieldCheck className="h-4 w-4 mr-2" />
                            Activate
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => setShowDeleteUser(user)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete User
                        </DropdownMenuItem>
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
      {pagination.pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <p className="text-sm text-muted-foreground">
              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, pagination.total)} of {pagination.total} users
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <Select value={pageSize.toString()} onValueChange={(value) => {
              setPageSize(Number(value));
              setCurrentPage(1);
            }}>
              <SelectTrigger className="w-[70px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="25">25</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            
            <span className="text-sm">
              Page {currentPage} of {pagination.pages}
            </span>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(Math.min(pagination.pages, currentPage + 1))}
              disabled={currentPage === pagination.pages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Dialogs */}
      {showUserDetail && (
        <UserDetailDialog
          user={showUserDetail}
          open={!!showUserDetail}
          onOpenChange={() => setShowUserDetail(null)}
        />
      )}

      {showEditUser && (
        <EditUserDialog
          user={showEditUser}
          open={!!showEditUser}
          onOpenChange={() => setShowEditUser(null)}
          onSuccess={() => {
            setShowEditUser(null);
            loadUsers();
          }}
        />
      )}

      {showDeleteUser && (
        <DeleteUserDialog
          user={showDeleteUser}
          open={!!showDeleteUser}
          onOpenChange={() => setShowDeleteUser(null)}
          onSuccess={() => {
            setShowDeleteUser(null);
            loadUsers();
          }}
        />
      )}

      {showPasswordReset && (
        <PasswordResetDialog
          user={showPasswordReset}
          open={!!showPasswordReset}
          onOpenChange={() => setShowPasswordReset(null)}
          onSuccess={() => {
            setShowPasswordReset(null);
            loadUsers();
          }}
        />
      )}
    </div>
  );
}