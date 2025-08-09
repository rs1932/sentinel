'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
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
import { Badge } from '@/components/ui/badge';
import { toast } from '@/hooks/use-toast';
import { 
  MoreHorizontal, 
  Trash2, 
  Power, 
  PowerOff, 
  Copy,
  AlertTriangle 
} from 'lucide-react';

interface BulkPermissionActionsProps {
  selectedPermissions: string[];
  onComplete: () => void;
}

type BulkAction = 'activate' | 'deactivate' | 'delete' | 'duplicate';

export function BulkPermissionActions({ selectedPermissions, onComplete }: BulkPermissionActionsProps) {
  const [pendingAction, setPendingAction] = useState<BulkAction | null>(null);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);

  const bulkMutation = useMutation({
    mutationFn: async ({ action, permissionIds }: { action: BulkAction; permissionIds: string[] }) => {
      switch (action) {
        case 'activate':
        case 'deactivate':
          // Update each permission individually
          const isActive = action === 'activate';
          await Promise.all(
            permissionIds.map(id => 
              apiClient.permissions.update(id, { is_active: isActive })
            )
          );
          break;
        case 'delete':
          // Delete each permission individually
          await Promise.all(
            permissionIds.map(id => apiClient.permissions.delete(id))
          );
          break;
        case 'duplicate':
          // This would require fetching each permission and creating duplicates
          // For now, we'll show a toast saying it's not implemented
          throw new Error('Duplicate functionality not yet implemented');
        default:
          throw new Error(`Unknown action: ${action}`);
      }
    },
    onSuccess: (_, variables) => {
      const actionLabels = {
        activate: 'activated',
        deactivate: 'deactivated', 
        delete: 'deleted',
        duplicate: 'duplicated'
      };
      
      toast({
        title: 'Success',
        description: `${selectedPermissions.length} permission${selectedPermissions.length !== 1 ? 's' : ''} ${actionLabels[variables.action]}.`,
      });
      onComplete();
      setConfirmDialogOpen(false);
      setPendingAction(null);
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to perform bulk action.',
        variant: 'destructive',
      });
      setConfirmDialogOpen(false);
      setPendingAction(null);
    },
  });

  const handleBulkAction = (action: BulkAction) => {
    setPendingAction(action);
    if (action === 'delete') {
      setConfirmDialogOpen(true);
    } else {
      bulkMutation.mutate({ action, permissionIds: selectedPermissions });
    }
  };

  const confirmDelete = () => {
    if (pendingAction === 'delete') {
      bulkMutation.mutate({ action: 'delete', permissionIds: selectedPermissions });
    }
  };

  const getActionInfo = () => {
    switch (pendingAction) {
      case 'delete':
        return {
          title: 'Delete Permissions',
          description: `Are you sure you want to delete ${selectedPermissions.length} permission${selectedPermissions.length !== 1 ? 's' : ''}? This action cannot be undone.`,
          icon: <Trash2 className="w-5 h-5 text-red-600" />,
          confirmText: 'Delete Permissions',
          confirmClass: 'bg-red-600 hover:bg-red-700'
        };
      default:
        return {
          title: 'Confirm Action',
          description: 'Are you sure you want to perform this action?',
          icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
          confirmText: 'Confirm',
          confirmClass: 'bg-blue-600 hover:bg-blue-700'
        };
    }
  };

  const actionInfo = getActionInfo();

  return (
    <>
      <div className="flex items-center gap-2">
        <Badge variant="secondary" className="bg-blue-100 text-blue-800">
          {selectedPermissions.length} selected
        </Badge>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" disabled={bulkMutation.isPending}>
              <MoreHorizontal className="mr-2 h-4 w-4" />
              Bulk Actions
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleBulkAction('activate')}>
              <Power className="mr-2 h-4 w-4 text-green-600" />
              Activate All
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleBulkAction('deactivate')}>
              <PowerOff className="mr-2 h-4 w-4 text-gray-600" />
              Deactivate All
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => handleBulkAction('duplicate')}>
              <Copy className="mr-2 h-4 w-4 text-blue-600" />
              Duplicate All
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              onClick={() => handleBulkAction('delete')}
              className="text-red-600 focus:text-red-600"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete All
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <AlertDialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                {actionInfo.icon}
              </div>
              <div>
                <AlertDialogTitle>{actionInfo.title}</AlertDialogTitle>
                <AlertDialogDescription>
                  {actionInfo.description}
                </AlertDialogDescription>
              </div>
            </div>
          </AlertDialogHeader>

          {pendingAction === 'delete' && (
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h5 className="font-medium text-red-900">Warning</h5>
                  <p className="text-sm text-red-800 mt-1">
                    This will permanently delete {selectedPermissions.length} permission{selectedPermissions.length !== 1 ? 's' : ''}. 
                    Users and roles that depend on these permissions will lose access immediately.
                  </p>
                </div>
              </div>
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              disabled={bulkMutation.isPending}
              className={actionInfo.confirmClass}
            >
              {bulkMutation.isPending ? 'Processing...' : actionInfo.confirmText}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}