'use client';

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Resource } from '@/types';
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
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from '@/hooks/use-toast';
import { AlertTriangle, Trash2 } from 'lucide-react';

interface DeleteResourceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resource: Resource;
  onSuccess: () => void;
}

const RESOURCE_TYPE_INFO = {
  product_family: { label: 'Product Family', emoji: '📦' },
  app: { label: 'Application', emoji: '🎯' },
  capability: { label: 'Capability', emoji: '⚡' },
  service: { label: 'Service', emoji: '🔧' },
  entity: { label: 'Entity', emoji: '📋' },
  page: { label: 'Page', emoji: '📄' },
  api: { label: 'API', emoji: '🔌' },
};

export function DeleteResourceDialog({ open, onOpenChange, resource, onSuccess }: DeleteResourceDialogProps) {
  const [cascadeDelete, setCascadeDelete] = useState(false);

  // Fetch child resources to show impact
  const { data: childResources } = useQuery({
    queryKey: ['resources', resource.id, 'children'],
    queryFn: () => apiClient.resources.getChildren(resource.id, { limit: 100 }),
    enabled: open,
  });

  // Fetch permissions associated with this resource
  const { data: resourcePermissions } = useQuery({
    queryKey: ['resources', resource.id, 'permissions'],
    queryFn: () => apiClient.resources.getPermissions(resource.id),
    enabled: open,
  });

  const deleteMutation = useMutation({
    mutationFn: () => {
      return apiClient.resources.delete(resource.id, cascadeDelete);
    },
    onSuccess: () => {
      toast({
        title: 'Success',
        description: `Resource "${resource.name}" has been deleted.`,
      });
      onSuccess();
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete resource.',
        variant: 'destructive',
      });
    },
  });

  const handleDelete = () => {
    deleteMutation.mutate();
  };

  const typeInfo = RESOURCE_TYPE_INFO[resource.type as keyof typeof RESOURCE_TYPE_INFO];
  const hasChildren = childResources?.data?.resources?.length > 0;
  const hasPermissions = resourcePermissions?.data?.permissions?.length > 0;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="max-w-lg">
        <AlertDialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <Trash2 className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <AlertDialogTitle>Delete Resource</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the resource.
              </AlertDialogDescription>
            </div>
          </div>
        </AlertDialogHeader>

        <div className="space-y-4">
          {/* Resource Info */}
          <div className="p-4 border rounded-lg bg-gray-50">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{typeInfo?.emoji}</span>
              <div>
                <h4 className="font-semibold text-gray-900">{resource.name}</h4>
                <p className="text-sm text-gray-600">{resource.code}</p>
                <Badge variant="outline" className="mt-1">
                  {typeInfo?.label}
                </Badge>
              </div>
            </div>
            {resource.description && (
              <p className="text-sm text-gray-600 mt-2">{resource.description}</p>
            )}
          </div>

          {/* Warning about children */}
          {hasChildren && (
            <div className="p-4 border border-amber-200 rounded-lg bg-amber-50">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h5 className="font-medium text-amber-900">Child Resources Found</h5>
                  <p className="text-sm text-amber-800 mt-1">
                    This resource has {childResources.data.resources.length} child resource(s). 
                    If you delete this resource:
                  </p>
                  <ul className="text-sm text-amber-800 mt-2 space-y-1">
                    <li>• Without cascade: Child resources will become orphaned</li>
                    <li>• With cascade: All child resources will also be deleted</li>
                  </ul>
                  
                  <div className="mt-3">
                    <h6 className="font-medium text-amber-900 mb-2">Child Resources:</h6>
                    <div className="space-y-1">
                      {childResources.data.resources.slice(0, 5).map((child: Resource) => (
                        <div key={child.id} className="flex items-center gap-2 text-sm">
                          <span>{RESOURCE_TYPE_INFO[child.type as keyof typeof RESOURCE_TYPE_INFO]?.emoji}</span>
                          <span>{child.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {child.type.replace('_', ' ')}
                          </Badge>
                        </div>
                      ))}
                      {childResources.data.resources.length > 5 && (
                        <p className="text-sm text-amber-800">
                          ... and {childResources.data.resources.length - 5} more
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 mt-4">
                    <Checkbox
                      id="cascade"
                      checked={cascadeDelete}
                      onCheckedChange={(checked) => setCascadeDelete(checked === true)}
                    />
                    <label 
                      htmlFor="cascade"
                      className="text-sm font-medium text-amber-900 cursor-pointer"
                    >
                      Delete all child resources (cascade delete)
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Warning about permissions */}
          {hasPermissions && (
            <div className="p-4 border border-blue-200 rounded-lg bg-blue-50">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h5 className="font-medium text-blue-900">Permissions Associated</h5>
                  <p className="text-sm text-blue-800 mt-1">
                    This resource has {resourcePermissions.data.permissions.length} permission(s) 
                    associated with it. These permissions will also be deleted.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Confirmation warning */}
          <div className="p-4 border border-red-200 rounded-lg bg-red-50">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h5 className="font-medium text-red-900">Permanent Action</h5>
                <p className="text-sm text-red-800 mt-1">
                  This will permanently delete the resource "{resource.name}" and cannot be undone.
                  {cascadeDelete && hasChildren && ' All child resources will also be permanently deleted.'}
                </p>
              </div>
            </div>
          </div>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete Resource'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}