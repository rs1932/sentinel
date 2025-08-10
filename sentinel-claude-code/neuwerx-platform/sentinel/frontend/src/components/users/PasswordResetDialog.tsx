'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertTriangle, Key, Shield, CheckCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/store/auth';

interface User {
  id: string;
  email: string;
  username?: string;
  tenant?: {
    code: string;
    name: string;
  };
}

interface PasswordResetDialogProps {
  user: User;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function PasswordResetDialog({ 
  user, 
  open, 
  onOpenChange, 
  onSuccess 
}: PasswordResetDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const { user: currentUser } = useAuthStore();

  const handleResetPassword = async () => {
    if (!newPassword.trim()) {
      setError('Please enter a new password');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Use the admin password reset endpoint
      await apiClient.users.adminResetPassword(user.id, newPassword);

      setSuccess(true);
      setNewPassword(''); // Clear password field on success
    } catch (err: any) {
      setError(err.message || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    onOpenChange(false);
    setError(null);
    setSuccess(false);
    setNewPassword('');
    onSuccess?.();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Reset User Password
          </DialogTitle>
          <DialogDescription>
            Set a new password for this user (minimum 8 characters).
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* User Info */}
          <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/50">
            <div className="flex-1">
              <div className="font-medium">{user.username || user.email}</div>
              {user.username && (
                <div className="text-sm text-muted-foreground">{user.email}</div>
              )}
              {user.tenant && (
                <div className="text-xs text-muted-foreground">
                  Tenant: {user.tenant.name} ({user.tenant.code})
                </div>
              )}
            </div>
          </div>

          {/* Success Message */}
          {success && (
            <Alert className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                <strong>Password reset successfully!</strong> The user's password has been updated and they can now use the new password to log in.
              </AlertDescription>
            </Alert>
          )}

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Password Input */}
          {!success && (
            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password (minimum 8 characters)"
                disabled={loading}
                className="w-full"
                autoComplete="new-password"
              />
              <div className="text-xs text-muted-foreground">
                Password must be at least 8 characters long
              </div>
            </div>
          )}

          {/* Security Warning */}
          {!success && (
            <Alert>
              <Shield className="h-4 w-4" />
              <AlertDescription>
                <strong>Security Note:</strong> This will immediately change the user's password. 
                Make sure to communicate the new password securely to the user.
              </AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter className="flex justify-between">
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleClose}
            >
              {success ? 'Done' : 'Cancel'}
            </Button>
            {!success && (
              <Button
                onClick={handleResetPassword}
                disabled={loading || !newPassword.trim() || newPassword.length < 8}
                className="bg-orange-600 hover:bg-orange-700"
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}