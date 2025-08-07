'use client';

import { useState, useEffect } from 'react';
import { 
  Key,
  MoreHorizontal,
  Plus,
  Search,
  Settings,
  RefreshCw,
  Shield,
  ShieldOff,
  Trash2,
  Edit,
  Copy,
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
import { toast } from '@/hooks/use-toast';
import { useDebounce } from '@/hooks/useDebounce';
import { apiClient } from '@/lib/api';

interface ServiceAccount {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  attributes: { [key: string]: any };
  client_id: string;
  is_active: boolean;
  last_login?: string;
  login_count: number;
  created_at: string;
  updated_at: string;
}

interface ServiceAccountListProps {
  onCreateNew: () => void;
  onCountUpdate?: (count: number) => void;
}

export function ServiceAccountList({ onCreateNew, onCountUpdate }: ServiceAccountListProps) {
  const [serviceAccounts, setServiceAccounts] = useState<ServiceAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedAccount, setSelectedAccount] = useState<ServiceAccount | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [rotateDialogOpen, setRotateDialogOpen] = useState(false);
  const [newCredentials, setNewCredentials] = useState<{ client_id: string; client_secret: string } | null>(null);
  const [showSecret, setShowSecret] = useState(false);

  const debouncedSearch = useDebounce(search, 500);

  useEffect(() => {
    loadServiceAccounts();
  }, [debouncedSearch, statusFilter, sortBy, sortOrder, currentPage]);

  const loadServiceAccounts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '20',
        sort: sortBy,
        order: sortOrder,
      });

      if (debouncedSearch) {
        params.append('search', debouncedSearch);
      }

      if (statusFilter !== 'all') {
        params.append('is_active', statusFilter === 'active' ? 'true' : 'false');
      }

      const response = await apiClient.request(`/service-accounts?${params}`);
      
      setServiceAccounts(response.items || []);
      setTotalCount(response.total || 0);
      setTotalPages(response.pages || 1);
      
      // Update parent component with service account count
      onCountUpdate?.(response.total || 0);
    } catch (error) {
      console.error('Failed to load service accounts:', error);
      toast({
        title: 'Error',
        description: 'Failed to load service accounts',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (account: ServiceAccount) => {
    try {
      await apiClient.request(`/service-accounts/${account.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          is_active: !account.is_active
        })
      });

      await loadServiceAccounts();
      toast({
        title: 'Success',
        description: `Service account ${account.is_active ? 'deactivated' : 'activated'}`,
      });
    } catch (error) {
      console.error('Failed to toggle service account status:', error);
      toast({
        title: 'Error',
        description: 'Failed to update service account status',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async () => {
    if (!selectedAccount) return;

    try {
      await apiClient.request(`/service-accounts/${selectedAccount.id}`, {
        method: 'DELETE'
      });

      await loadServiceAccounts();
      setDeleteDialogOpen(false);
      setSelectedAccount(null);
      toast({
        title: 'Success',
        description: 'Service account deleted successfully',
      });
    } catch (error) {
      console.error('Failed to delete service account:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete service account',
        variant: 'destructive',
      });
    }
  };

  const handleRotateCredentials = async () => {
    if (!selectedAccount) return;

    try {
      const response = await apiClient.request(`/service-accounts/${selectedAccount.id}/rotate-credentials`, {
        method: 'POST'
      });

      setNewCredentials(response);
      setRotateDialogOpen(false);
      setSelectedAccount(null);
      await loadServiceAccounts();
      
      toast({
        title: 'Success',
        description: 'Credentials rotated successfully',
      });
    } catch (error) {
      console.error('Failed to rotate credentials:', error);
      toast({
        title: 'Error',
        description: 'Failed to rotate credentials',
        variant: 'destructive',
      });
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: `${label} copied to clipboard`,
    });
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search service accounts..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>

            <Select value={`${sortBy}-${sortOrder}`} onValueChange={(value) => {
              const [field, order] = value.split('-');
              setSortBy(field);
              setSortOrder(order as 'asc' | 'desc');
            }}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="created_at-desc">Newest First</SelectItem>
                <SelectItem value="created_at-asc">Oldest First</SelectItem>
                <SelectItem value="name-asc">Name A-Z</SelectItem>
                <SelectItem value="name-desc">Name Z-A</SelectItem>
                <SelectItem value="last_login-desc">Recently Active</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline" size="sm" onClick={loadServiceAccounts}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Service Accounts Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Service Accounts ({totalCount})</span>
            <div className="text-sm font-normal text-muted-foreground">
              Page {currentPage} of {totalPages}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : serviceAccounts.length === 0 ? (
            <div className="text-center p-8">
              <Key className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No service accounts</h3>
              <p className="text-muted-foreground mb-4">
                Create your first service account to get started
              </p>
              <Button onClick={onCreateNew}>
                <Plus className="h-4 w-4 mr-2" />
                Create Service Account
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Client ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Usage</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {serviceAccounts.map((account) => (
                    <TableRow key={account.id}>
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          <Avatar className="h-10 w-10">
                            <AvatarFallback>
                              <Key className="h-4 w-4" />
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">{account.name}</div>
                            {account.description && (
                              <div className="text-sm text-muted-foreground">
                                {account.description}
                              </div>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <code className="bg-muted px-2 py-1 rounded text-xs">
                            {account.client_id.slice(0, 8)}...
                          </code>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(account.client_id, 'Client ID')}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <Badge
                          variant={account.is_active ? 'default' : 'secondary'}
                          className={account.is_active ? 'bg-green-100 text-green-800' : ''}
                        >
                          {account.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      
                      <TableCell>
                        <div className="space-y-1">
                          <div className="text-sm font-medium">
                            {account.login_count.toLocaleString()} requests
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Last: {formatDate(account.last_login)}
                          </div>
                        </div>
                      </TableCell>
                      
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(account.created_at)}
                      </TableCell>
                      
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => {/* TODO: Open edit dialog */}}>
                              <Edit className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => handleToggleStatus(account)}
                            >
                              {account.is_active ? (
                                <ShieldOff className="h-4 w-4 mr-2" />
                              ) : (
                                <Shield className="h-4 w-4 mr-2" />
                              )}
                              {account.is_active ? 'Deactivate' : 'Activate'}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedAccount(account);
                                setRotateDialogOpen(true);
                              }}
                            >
                              <RefreshCw className="h-4 w-4 mr-2" />
                              Rotate Credentials
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-red-600"
                              onClick={() => {
                                setSelectedAccount(account);
                                setDeleteDialogOpen(true);
                              }}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2">
          <Button
            variant="outline"
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
          >
            Previous
          </Button>
          
          <div className="flex items-center space-x-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const page = currentPage <= 3 ? i + 1 : currentPage - 2 + i;
              if (page > totalPages) return null;
              
              return (
                <Button
                  key={page}
                  variant={page === currentPage ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setCurrentPage(page)}
                >
                  {page}
                </Button>
              );
            })}
          </div>
          
          <Button
            variant="outline"
            disabled={currentPage >= totalPages}
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
          >
            Next
          </Button>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center space-x-2">
              <Trash2 className="h-5 w-5 text-red-600" />
              <span>Delete Service Account</span>
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete <strong>{selectedAccount?.name}</strong>?
              This action cannot be undone and will immediately revoke API access.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete Service Account
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Rotate Credentials Dialog */}
      <AlertDialog open={rotateDialogOpen} onOpenChange={setRotateDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center space-x-2">
              <RefreshCw className="h-5 w-5" />
              <span>Rotate Credentials</span>
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>
                This will generate new credentials for <strong>{selectedAccount?.name}</strong>.
              </p>
              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium">Warning:</p>
                    <p>The current credentials will be immediately invalidated. Update your applications with the new credentials.</p>
                  </div>
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRotateCredentials}>
              Rotate Credentials
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* New Credentials Dialog */}
      <AlertDialog open={!!newCredentials} onOpenChange={() => setNewCredentials(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span>New Credentials Generated</span>
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <p>Your new service account credentials have been generated. Please save them securely.</p>
              
              {newCredentials && (
                <div className="bg-muted p-4 rounded-lg space-y-3">
                  <div>
                    <label className="text-sm font-medium">Client ID</label>
                    <div className="flex items-center space-x-2 mt-1">
                      <code className="flex-1 bg-background p-2 rounded text-xs">
                        {newCredentials.client_id}
                      </code>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(newCredentials.client_id, 'Client ID')}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Client Secret</label>
                    <div className="flex items-center space-x-2 mt-1">
                      <code className="flex-1 bg-background p-2 rounded text-xs">
                        {showSecret ? newCredentials.client_secret : '••••••••••••••••'}
                      </code>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowSecret(!showSecret)}
                      >
                        {showSecret ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(newCredentials.client_secret, 'Client Secret')}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
                  <div className="text-sm text-red-800">
                    <p className="font-medium">Important:</p>
                    <p>This is the only time the client secret will be shown. Make sure to save it securely.</p>
                  </div>
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setNewCredentials(null)}>
              I've Saved the Credentials
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}