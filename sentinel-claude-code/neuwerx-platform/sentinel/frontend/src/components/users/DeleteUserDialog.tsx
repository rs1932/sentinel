'use client';

import { useState } from 'react';
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
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Loader2, Trash2 } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface User {
  id: string;
  email: string;
  username?: string;
  is_active: boolean;
  login_count: number;
  last_login?: string;
  created_at: string;
}

interface DeleteUserDialogProps {
  user: User;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function DeleteUserDialog({ user, open, onOpenChange, onSuccess }: DeleteUserDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hardDelete, setHardDelete] = useState(false);

  const handleDelete = async () => {
    try {
      setLoading(true);
      setError(null);

      await apiClient.users.delete(user.id, hardDelete);
      
      onSuccess?.();
      onOpenChange(false);
    } catch (err: any) {
      console.error('Delete user error:', err);
      setError(err.message || 'Failed to delete user');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setError(null);
    setHardDelete(false);
    onOpenChange(false);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  const isRecentUser = () => {
    const createdDate = new Date(user.created_at);
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    return createdDate > thirtyDaysAgo;
  };

  const hasActivity = user.login_count > 0;

  return (
    <AlertDialog open={open} onOpenChange={handleClose}>
      <AlertDialogContent className="sm:max-w-[500px]">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center space-x-2">
            <Trash2 className="h-5 w-5 text-red-600" />
            <span>Delete User</span>
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-4">
            <p>
              Are you sure you want to delete <strong>{user.username || user.email}</strong>?
            </p>

            {/* User Info */}
            <div className="bg-muted p-4 rounded-md space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Email:</span>
                <span>{user.email}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Status:</span>
                <Badge variant={user.is_active ? 'default' : 'secondary'}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Total Logins:</span>
                <span>{user.login_count.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Last Login:</span>
                <span>{formatDate(user.last_login)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Created:</span>
                <span>{formatDate(user.created_at)}</span>
              </div>
            </div>

            {/* Warnings */}
            {(hasActivity || isRecentUser()) && (
              <div className="space-y-2">
                {hasActivity && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription className="text-sm">
                      This user has logged in {user.login_count} times. 
                      {user.last_login && ` Last active on ${formatDate(user.last_login)}.`}
                    </AlertDescription>
                  </Alert>
                )}
                
                {isRecentUser() && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription className="text-sm">
                      This is a recently created user. Consider deactivating instead of deleting.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}

            {/* Delete Options */}
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <Checkbox
                  id="hard-delete"
                  checked={hardDelete}
                  onCheckedChange={setHardDelete}
                />
                <div className="space-y-1">
                  <label
                    htmlFor="hard-delete"
                    className="text-sm font-medium cursor-pointer"
                  >
                    Permanent deletion (hard delete)
                  </label>
                  <p className="text-xs text-muted-foreground">
                    {hardDelete 
                      ? 'User will be completely removed from the database. This cannot be undone.'
                      : 'User will be soft deleted and can be restored later if needed.'
                    }
                  </p>
                </div>
              </div>

              {hardDelete && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription className="text-sm">
                    <strong>Warning:</strong> Hard deletion is permanent and irreversible. 
                    The user's data will be completely removed from the system.
                  </AlertDescription>
                </Alert>
              )}
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleClose}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={loading}
            className="bg-red-600 hover:bg-red-700"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Deleting...</span>
              </div>
            ) : (
              <>
                <Trash2 className="h-4 w-4 mr-2" />
                {hardDelete ? 'Delete Permanently' : 'Delete User'}
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}