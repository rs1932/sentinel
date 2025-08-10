'use client';

import { useState } from 'react';
import { 
  Users, 
  UserCheck, 
  UserX, 
  Trash2, 
  Shield, 
  ShieldOff,
  X,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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

interface User {
  id: string;
  email: string;
  username?: string;
  is_active: boolean;
}

interface BulkActionsBarProps {
  selectedCount: number;
  selectedUsers: User[];
  onBulkAction: (action: string, userIds: string[]) => Promise<void>;
  onClearSelection: () => void;
}

interface BulkAction {
  value: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  variant: 'default' | 'destructive' | 'secondary';
  requiresConfirmation: boolean;
  description: string;
}

const bulkActions: BulkAction[] = [
  {
    value: 'activate',
    label: 'Activate Users',
    icon: UserCheck,
    variant: 'default',
    requiresConfirmation: true,
    description: 'Allow selected users to sign in and access the system'
  },
  {
    value: 'deactivate',
    label: 'Deactivate Users', 
    icon: UserX,
    variant: 'secondary',
    requiresConfirmation: true,
    description: 'Prevent selected users from signing in (they can be reactivated later)'
  },
  {
    value: 'delete',
    label: 'Delete Users',
    icon: Trash2,
    variant: 'destructive',
    requiresConfirmation: true,
    description: 'Permanently remove selected users from the system (this cannot be undone)'
  }
];

export function BulkActionsBar({ 
  selectedCount, 
  selectedUsers, 
  onBulkAction, 
  onClearSelection 
}: BulkActionsBarProps) {
  const [selectedAction, setSelectedAction] = useState('');
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [loading, setLoading] = useState(false);

  const currentAction = bulkActions.find(action => action.value === selectedAction);

  const handleActionSelect = (actionValue: string) => {
    setSelectedAction(actionValue);
    const action = bulkActions.find(a => a.value === actionValue);
    if (action?.requiresConfirmation) {
      setShowConfirmation(true);
    } else {
      executeAction(actionValue);
    }
  };

  const executeAction = async (actionValue: string) => {
    try {
      setLoading(true);
      const userIds = selectedUsers.map(user => user.id);
      await onBulkAction(actionValue, userIds);
    } catch (error) {
      console.error('Bulk action failed:', error);
    } finally {
      setLoading(false);
      setSelectedAction('');
      setShowConfirmation(false);
    }
  };

  const getActionStats = () => {
    if (!currentAction || !selectedUsers.length) return null;

    const stats = {
      active: selectedUsers.filter(u => u.is_active).length,
      inactive: selectedUsers.filter(u => !u.is_active).length
    };

    return stats;
  };

  const stats = getActionStats();

  return (
    <>
      <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-blue-200 bg-blue-50">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Users className="h-4 w-4 text-blue-600" />
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              {selectedCount} selected
            </Badge>
          </div>
          
          <div className="hidden sm:flex items-center space-x-1 text-sm text-muted-foreground">
            {stats && (
              <>
                <span className="flex items-center space-x-1">
                  <UserCheck className="h-3 w-3" />
                  <span>{stats.active} active</span>
                </span>
                <span className="mx-2">•</span>
                <span className="flex items-center space-x-1">
                  <UserX className="h-3 w-3" />
                  <span>{stats.inactive} inactive</span>
                </span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Select value={selectedAction} onValueChange={handleActionSelect}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Choose action..." />
            </SelectTrigger>
            <SelectContent>
              {bulkActions.map(action => {
                const Icon = action.icon;
                return (
                  <SelectItem key={action.value} value={action.value}>
                    <div className="flex items-center space-x-2">
                      <Icon className="h-4 w-4" />
                      <span>{action.label}</span>
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            onClick={onClearSelection}
            className="flex items-center space-x-1"
          >
            <X className="h-3 w-3" />
            <span className="hidden sm:inline">Clear</span>
          </Button>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirmation} onOpenChange={setShowConfirmation}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center space-x-2">
              {currentAction && (
                <>
                  <currentAction.icon className="h-5 w-5" />
                  <span>Confirm {currentAction.label}</span>
                </>
              )}
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-3">
              <p>{currentAction?.description}</p>
              
              <div className="bg-muted p-3 rounded-md">
                <p className="font-medium text-sm mb-2">This action will affect:</p>
                <div className="space-y-1">
                  {selectedUsers.slice(0, 5).map(user => (
                    <div key={user.id} className="text-xs flex items-center space-x-2">
                      <span className="truncate">{user.username || user.email}</span>
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${user.is_active ? 'border-green-500 text-green-700' : 'border-gray-500 text-gray-700'}`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  ))}
                  {selectedUsers.length > 5 && (
                    <div className="text-xs text-muted-foreground">
                      + {selectedUsers.length - 5} more users
                    </div>
                  )}
                </div>
              </div>

              {currentAction?.variant === 'destructive' && (
                <div className="flex items-start space-x-2 p-3 bg-red-50 border border-red-200 rounded-md">
                  <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
                  <div className="text-sm text-red-800">
                    <p className="font-medium">This action cannot be undone</p>
                    <p>Users will be permanently removed from the system.</p>
                  </div>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => executeAction(selectedAction)}
              disabled={loading}
              className={currentAction?.variant === 'destructive' ? 'bg-red-600 hover:bg-red-700' : ''}
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="h-3 w-3 animate-spin rounded-full border border-current border-t-transparent" />
                  <span>Processing...</span>
                </div>
              ) : (
                `Yes, ${currentAction?.label}`
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}