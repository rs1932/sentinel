'use client';

import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Permission } from '@/types';
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
import { Badge } from '@/components/ui/badge';
import { toast } from '@/hooks/use-toast';
import { Trash2, AlertTriangle } from 'lucide-react';

interface DeletePermissionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  permission: Permission;
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

export function DeletePermissionDialog({ open, onOpenChange, permission, onSuccess }: DeletePermissionDialogProps) {
  const deletePermissionMutation = useMutation({
    mutationFn: () => apiClient.permissions.delete(permission.id),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: `Permission "${permission.name}" has been deleted.`,
      });
      onSuccess();
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete permission.',
        variant: 'destructive',
      });
    },
  });

  const handleDelete = () => {
    deletePermissionMutation.mutate();
  };

  const typeInfo = RESOURCE_TYPE_INFO[permission.resource_type as keyof typeof RESOURCE_TYPE_INFO];

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="max-w-lg">
        <AlertDialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <Trash2 className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <AlertDialogTitle>Delete Permission</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the permission.
              </AlertDialogDescription>
            </div>
          </div>
        </AlertDialogHeader>

        <div className="space-y-4">
          {/* Permission Info */}
          <div className="p-4 border rounded-lg bg-gray-50">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{typeInfo?.emoji}</span>
              <div>
                <h4 className="font-semibold text-gray-900">{permission.name}</h4>
                <p className="text-sm text-gray-600">
                  {typeInfo?.label} • {permission.actions.length} action{permission.actions.length !== 1 ? 's' : ''}
                </p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {permission.actions.map((action, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {action}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="mt-3 pt-3 border-t">
              <div className="text-sm text-gray-600">
                <div><strong>Resource:</strong> {
                  permission.resource_path || permission.resource_id || 'Global'
                }</div>
                <div><strong>Status:</strong> {permission.is_active ? 'Active' : 'Inactive'}</div>
              </div>
            </div>
          </div>

          {/* Warning */}
          <div className="p-4 border border-red-200 rounded-lg bg-red-50">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h5 className="font-medium text-red-900">Permanent Action</h5>
                <p className="text-sm text-red-800 mt-1">
                  This will permanently delete the permission "{permission.name}" and cannot be undone.
                  Users and roles that depend on this permission will lose access.
                </p>
              </div>
            </div>
          </div>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={deletePermissionMutation.isPending}
            className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
          >
            {deletePermissionMutation.isPending ? 'Deleting...' : 'Delete Permission'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}