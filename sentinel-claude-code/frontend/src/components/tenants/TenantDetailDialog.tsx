'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { TenantDetail, FEATURE_LABELS } from '@/types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Building2, 
  Users, 
  GitBranch, 
  Shield, 
  Calendar,
  Settings,
  Info,
  Database,
  Loader2
} from 'lucide-react';

interface TenantDetailDialogProps {
  isOpen: boolean;
  tenantId: string;
  onClose: () => void;
}

export function TenantDetailDialog({ isOpen, tenantId, onClose }: TenantDetailDialogProps) {
  const {
    data: tenant,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['tenant-detail', tenantId],
    queryFn: () => apiClient.tenants.get(tenantId),
    enabled: isOpen && !!tenantId,
  });

  const {
    data: hierarchy,
    isLoading: hierarchyLoading,
  } = useQuery({
    queryKey: ['tenant-hierarchy', tenantId],
    queryFn: () => apiClient.tenants.getHierarchy(tenantId),
    enabled: isOpen && !!tenantId,
  });

  if (isLoading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
              <p className="text-gray-600">Loading tenant details...</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (error || !tenant) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <div className="text-center py-12">
            <p className="text-red-600">Failed to load tenant details</p>
            <Button variant="outline" className="mt-2" onClick={onClose}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  const tenantDetail = tenant as TenantDetail;
  const renderHierarchyNode = (item: any, level: number = 0) => {
    const isCurrentTenant = item.id === tenantId;
    
    return (
      <div key={item.id} className={`mb-2 ${level > 0 ? 'ml-6' : ''}`}>
        <div className={`p-3 rounded-lg border ${isCurrentTenant ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'}`}>
          <div className="flex items-center gap-2 mb-2">
            {item.type === 'root' ? (
              <Building2 className="h-4 w-4 text-green-600" />
            ) : (
              <GitBranch className="h-4 w-4 text-yellow-600" />
            )}
            <span className="font-medium">{item.name}</span>
            <Badge variant="outline" className="text-xs">
              {item.code}
            </Badge>
            {isCurrentTenant && (
              <Badge variant="default" className="text-xs bg-blue-600">
                Current
              </Badge>
            )}
          </div>
          <div className="text-sm text-gray-600">
            <span className="capitalize">{item.type.replace('_', ' ')}</span> • 
            <span className="ml-1 capitalize">{item.isolation_mode}</span> • 
            <span className="ml-1">{item.is_active ? 'Active' : 'Inactive'}</span>
          </div>
        </div>
        
        {/* Render children if any */}
        {hierarchy && hierarchy.filter((child: any) => child.parent_tenant_id === item.id).map((child: any) => 
          renderHierarchyNode(child, level + 1)
        )}
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {tenantDetail.name}
          </DialogTitle>
          <DialogDescription>
            Detailed information and configuration for this tenant
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[70vh] pr-4">
          <div className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-1">
                    <Info className="h-4 w-4" />
                    Basic Info
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div>
                    <span className="text-sm font-medium">Code:</span>
                    <p className="text-sm text-gray-600">{tenantDetail.code}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium">Type:</span>
                    <p className="text-sm text-gray-600 capitalize">{tenantDetail.type.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium">Isolation:</span>
                    <p className="text-sm text-gray-600 capitalize">{tenantDetail.isolation_mode}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium">Status:</span>
                    <Badge variant={tenantDetail.is_active ? "default" : "secondary"} className="text-xs">
                      {tenantDetail.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-1">
                    <Database className="h-4 w-4" />
                    Statistics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Users className="h-3 w-3 text-gray-400" />
                    <span className="text-sm">Users: {tenantDetail.users_count || 0}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-3 w-3 text-gray-400" />
                    <span className="text-sm">Sub-tenants: {tenantDetail.sub_tenants_count || 0}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Shield className="h-3 w-3 text-gray-400" />
                    <span className="text-sm">Features: {tenantDetail.features.length}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    Timestamps
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div>
                    <span className="text-sm font-medium">Created:</span>
                    <p className="text-sm text-gray-600">{new Date(tenantDetail.created_at).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium">Updated:</span>
                    <p className="text-sm text-gray-600">{new Date(tenantDetail.updated_at).toLocaleDateString()}</p>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Separator />

            {/* Features */}
            <div className="space-y-3">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Enabled Features
              </h3>
              <div className="flex flex-wrap gap-2">
                {tenantDetail.features.length > 0 ? (
                  tenantDetail.features.map((feature) => (
                    <Badge key={feature} variant="outline" className="flex items-center gap-1">
                      <Shield className="h-3 w-3" />
                      {FEATURE_LABELS[feature] || feature}
                    </Badge>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No features enabled</p>
                )}
              </div>
            </div>

            <Separator />

            {/* Settings */}
            <div className="space-y-3">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Configuration
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Settings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-sm bg-gray-50 p-3 rounded-md overflow-auto max-h-32">
                      {JSON.stringify(tenantDetail.settings, null, 2)}
                    </pre>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Metadata</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-sm bg-gray-50 p-3 rounded-md overflow-auto max-h-32">
                      {JSON.stringify(tenantDetail.metadata, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Hierarchy */}
            {hierarchy && hierarchy.length > 0 && (
              <>
                <Separator />
                <div className="space-y-3">
                  <h3 className="text-lg font-medium flex items-center gap-2">
                    <GitBranch className="h-5 w-5" />
                    Tenant Hierarchy
                  </h3>
                  <Card>
                    <CardHeader>
                      <CardDescription>
                        {hierarchyLoading ? 'Loading hierarchy...' : 'Complete tenant hierarchy tree'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {hierarchyLoading ? (
                        <div className="flex items-center justify-center py-4">
                          <Loader2 className="h-4 w-4 animate-spin" />
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {/* Find and render root tenant first */}
                          {hierarchy
                            .filter((item: any) => !item.parent_tenant_id)
                            .map((rootItem: any) => renderHierarchyNode(rootItem))
                          }
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </>
            )}
          </div>
        </ScrollArea>

        <div className="flex justify-end pt-4">
          <Button onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}