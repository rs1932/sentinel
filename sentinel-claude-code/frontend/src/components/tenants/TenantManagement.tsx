'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { useT } from '@/components/terminology';
import { apiClient } from '@/lib/api';
import { Tenant, TenantDetail, FEATURE_LABELS } from '@/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
  Plus, 
  MoreHorizontal, 
  Building2, 
  Users, 
  Settings,
  Eye,
  Edit,
  Power,
  PowerOff,
  Trash2,
  GitBranch,
  Languages
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { CreateTenantDialog } from './CreateTenantDialog';
import { EditTenantDialog } from './EditTenantDialog';
import { TenantDetailDialog } from './TenantDetailDialog';
import TerminologyManagementDialog from './TerminologyManagementDialog';
import { useToast } from '@/hooks/use-toast';

export function TenantManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<'root' | 'sub_tenant' | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<boolean | 'all'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showTerminologyDialog, setShowTerminologyDialog] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);

  const { userRole } = useAuthStore();
  const t = useT(); // Terminology translation function
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const canManageTenants = userRole === 'super_admin';
  const canViewTenants = userRole === 'super_admin' || userRole === 'tenant_admin';
  const limit = 25;

  // Fetch tenants
  const {
    data: tenantsResponse,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['tenants', {
      search: searchTerm,
      type: typeFilter !== 'all' ? typeFilter : undefined,
      is_active: statusFilter !== 'all' ? statusFilter : undefined,
      offset: (currentPage - 1) * limit,
      limit
    }],
    queryFn: () => apiClient.tenants.list({
      name: searchTerm || undefined,
      type: typeFilter !== 'all' ? typeFilter : undefined,
      is_active: statusFilter !== 'all' ? statusFilter : undefined,
      offset: (currentPage - 1) * limit,
      limit
    }),
    retry: 1,
    enabled: canViewTenants,
  });

  const tenants = tenantsResponse?.items || [];
  const totalPages = Math.ceil((tenantsResponse?.total || 0) / limit);

  // Mutations
  const activateMutation = useMutation({
    mutationFn: (id: string) => apiClient.tenants.activate(id),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: `${t('tenant')} activated successfully`,
      });
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || `Failed to activate ${t('tenant').toLowerCase()}`,
        variant: 'destructive',
      });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => apiClient.tenants.deactivate(id),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: `${t('tenant')} deactivated successfully`,
      });
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || `Failed to deactivate ${t('tenant').toLowerCase()}`,
        variant: 'destructive',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.tenants.delete(id),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: `${t('tenant')} deleted successfully`,
      });
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || `Failed to delete ${t('tenant').toLowerCase()}`,
        variant: 'destructive',
      });
    },
  });

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setCurrentPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm, typeFilter, statusFilter]);

  const handleTenantAction = (action: string, tenant: Tenant) => {
    setSelectedTenant(tenant);
    
    switch (action) {
      case 'view':
        setShowDetailDialog(true);
        break;
      case 'edit':
        setShowEditDialog(true);
        break;
      case 'terminology':
        setShowTerminologyDialog(true);
        break;
      case 'activate':
        activateMutation.mutate(tenant.id);
        break;
      case 'deactivate':
        deactivateMutation.mutate(tenant.id);
        break;
      case 'delete':
        if (confirm(`Are you sure you want to delete this ${t('tenant').toLowerCase()}? This action cannot be undone.`)) {
          deleteMutation.mutate(tenant.id);
        }
        break;
    }
  };

  const getTenantTypeColor = (type: string) => {
    return type === 'root' 
      ? 'bg-green-100 text-green-800 hover:bg-green-100'
      : 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100';
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive
      ? 'bg-green-100 text-green-800 hover:bg-green-100'
      : 'bg-red-100 text-red-800 hover:bg-red-100';
  };

  const getIsolationColor = (mode: string) => {
    return mode === 'dedicated'
      ? 'bg-blue-100 text-blue-800 hover:bg-blue-100'
      : 'bg-gray-100 text-gray-800 hover:bg-gray-100';
  };

  if (!canViewTenants) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Building2 className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Access Denied</h3>
              <p className="mt-1 text-sm text-gray-500">
                You don't have permission to view {t('tenant').toLowerCase()} information.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('tenant_management')}</h1>
          <p className="text-gray-600">
            Manage organizations and their configurations
          </p>
        </div>
        {canManageTenants && (
          <Button 
            className="bg-blue-600 hover:bg-blue-700"
            onClick={() => setShowCreateDialog(true)}
          >
            <Plus className="mr-2 h-4 w-4" />
{t('create_tenant')}
          </Button>
        )}
      </div>

      {/* Search and filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{t('tenants')}</CardTitle>
              <CardDescription>
                {isLoading ? 'Loading...' : `${tenantsResponse?.total || 0} ${(tenantsResponse?.total || 0) !== 1 ? t('tenants').toLowerCase() : t('tenant').toLowerCase()} found`}
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder={`Search ${t('tenants').toLowerCase()}...`}
                  className="pl-10 w-64"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <Select value={typeFilter} onValueChange={(value) => setTypeFilter(value as 'root' | 'sub_tenant' | 'all')}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="root">Root</SelectItem>
                  <SelectItem value="sub_tenant">{t('sub_tenant')}</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter.toString()} onValueChange={(value) => setStatusFilter(value === 'all' ? 'all' : value === 'true')}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="true">Active</SelectItem>
                  <SelectItem value="false">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600">Failed to load {t('tenants').toLowerCase()}: {(error as any)?.message}</p>
              <Button variant="outline" className="mt-2" onClick={() => refetch()}>
                Try Again
              </Button>
            </div>
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]"></TableHead>
                      <TableHead>{t('tenant')}</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Isolation</TableHead>
                      <TableHead>{t('users')}</TableHead>
                      <TableHead>Features</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="w-[50px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tenants.map((tenant) => (
                      <TableRow key={tenant.id}>
                        <TableCell>
                          <div className={`w-8 h-8 ${tenant.type === 'root' ? 'bg-green-100' : 'bg-yellow-100'} rounded-lg flex items-center justify-center`}>
                            {tenant.type === 'root' ? (
                              <Building2 className="h-4 w-4 text-green-600" />
                            ) : (
                              <GitBranch className="h-4 w-4 text-yellow-600" />
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{tenant.name}</div>
                            <div className="text-sm text-gray-500">{tenant.code}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={getTenantTypeColor(tenant.type)}
                          >
                            {tenant.type === 'root' ? 'Root' : t('sub_tenant')}
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
                            {(tenant as TenantDetail).users_count || 0}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1 max-w-32">
                            {tenant.features.slice(0, 2).map((feature) => (
                              <Badge
                                key={feature}
                                variant="outline"
                                className="text-xs"
                              >
                                {FEATURE_LABELS[feature] || feature}
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
                            className={getStatusColor(tenant.is_active)}
                          >
                            {tenant.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm text-gray-500">
                            {new Date(tenant.created_at).toLocaleDateString()}
                          </div>
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
                              <DropdownMenuItem onClick={() => handleTenantAction('view', tenant)}>
                                <Eye className="mr-2 h-4 w-4" />
                                View Details
                              </DropdownMenuItem>
                              {canManageTenants && (
                                <>
                                  <DropdownMenuItem onClick={() => handleTenantAction('edit', tenant)}>
                                    <Edit className="mr-2 h-4 w-4" />
                                    Edit
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleTenantAction('terminology', tenant)}>
                                    <Languages className="mr-2 h-4 w-4" />
                                    Terminology
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  {tenant.is_active ? (
                                    <DropdownMenuItem onClick={() => handleTenantAction('deactivate', tenant)}>
                                      <PowerOff className="mr-2 h-4 w-4" />
                                      Deactivate
                                    </DropdownMenuItem>
                                  ) : (
                                    <DropdownMenuItem onClick={() => handleTenantAction('activate', tenant)}>
                                      <Power className="mr-2 h-4 w-4" />
                                      Activate
                                    </DropdownMenuItem>
                                  )}
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem 
                                    onClick={() => handleTenantAction('delete', tenant)}
                                    className="text-red-600"
                                  >
                                    <Trash2 className="mr-2 h-4 w-4" />
                                    Delete
                                  </DropdownMenuItem>
                                </>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-gray-500">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Statistics cards */}
      {tenantsResponse && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total {t('tenants')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{tenantsResponse.total}</div>
              <p className="text-xs text-gray-500">All organizations</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Root {t('tenants')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {tenants.filter(t => t.type === 'root').length}
              </div>
              <p className="text-xs text-gray-500">Primary organizations</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                {t('sub_tenants')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {tenants.filter(t => t.type === 'sub_tenant').length}
              </div>
              <p className="text-xs text-gray-500">Departments/divisions</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Active {t('tenants')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {tenants.filter(t => t.is_active).length}
              </div>
              <p className="text-xs text-gray-500">Currently active</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Dialogs */}
      {showCreateDialog && (
        <CreateTenantDialog
          isOpen={showCreateDialog}
          onClose={() => setShowCreateDialog(false)}
        />
      )}
      
      {showEditDialog && selectedTenant && (
        <EditTenantDialog
          isOpen={showEditDialog}
          tenant={selectedTenant}
          onClose={() => {
            setShowEditDialog(false);
            setSelectedTenant(null);
          }}
        />
      )}
      
      {showDetailDialog && selectedTenant && (
        <TenantDetailDialog
          isOpen={showDetailDialog}
          tenantId={selectedTenant.id}
          onClose={() => {
            setShowDetailDialog(false);
            setSelectedTenant(null);
          }}
        />
      )}
      
      {showTerminologyDialog && selectedTenant && (
        <TerminologyManagementDialog
          isOpen={showTerminologyDialog}
          tenant={selectedTenant}
          onClose={() => {
            setShowTerminologyDialog(false);
            setSelectedTenant(null);
          }}
        />
      )}
    </div>
  );
}