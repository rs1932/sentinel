'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Loader2, Users, Shield, UserCheck, UserX, 
  Trash2, Lock, Unlock, Info, AlertTriangle
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface User {
  id: string;
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_service_account: boolean;
  roles?: Array<{
    id: string;
    name: string;
    display_name: string;
  }>;
}

interface BulkActionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedUsers: string[];
  users: User[];
  onSuccess?: () => void;
}

export function BulkActionsDialog({ 
  open, 
  onOpenChange, 
  selectedUsers, 
  users,
  onSuccess 
}: BulkActionsDialogProps) {
  const [selectedAction, setSelectedAction] = useState<string>('');
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Get selected user objects
  const selectedUserObjects = users.filter(user => selectedUsers.includes(user.id));

  // Fetch available roles for role assignment
  const { data: rolesResponse, isLoading: rolesLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => apiClient.roles.list({
      is_active: true,
      limit: 100,
      sort_by: 'display_name',
      sort_order: 'asc'
    }),
    enabled: open && selectedAction === 'assign-roles'
  });

  // Bulk operation mutation
  const bulkOperationMutation = useMutation({
    mutationFn: async ({ action, userIds }: { action: string; userIds: string[] }) => {
      switch (action) {
        case 'activate':
        case 'deactivate':
        case 'delete':
          return apiClient.users.bulk(action, userIds);
        case 'assign-roles':
          // For role assignment, we need to call individual role assignment APIs
          const promises = [];
          for (const userId of userIds) {
            for (const roleId of selectedRoles) {
              promises.push(apiClient.roles.assignToUser(roleId, userId));
            }
          }
          return Promise.all(promises);
        case 'remove-roles':
          // For role removal, we need to call individual role removal APIs
          const removePromises = [];
          for (const userId of userIds) {
            for (const roleId of selectedRoles) {
              removePromises.push(apiClient.roles.removeFromUser(roleId, userId));
            }
          }
          return Promise.all(removePromises);
        default:
          throw new Error('Invalid action');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      onSuccess?.();
      setError(null);
      onOpenChange(false);
    },
    onError: (err: any) => {
      setError(err.message || 'Bulk operation failed');
    }
  });

  const roles = rolesResponse?.data || [];

  const getUserDisplayName = (user: User) => {
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return user.username || user.email.split('@')[0];
  };

  const handleRoleToggle = (roleId: string, checked: boolean) => {
    if (checked) {
      setSelectedRoles([...selectedRoles, roleId]);
    } else {
      setSelectedRoles(selectedRoles.filter(id => id !== roleId));
    }
  };

  const handleSubmit = async () => {
    if (!selectedAction) return;

    try {
      setLoading(true);
      setError(null);

      await bulkOperationMutation.mutateAsync({
        action: selectedAction,
        userIds: selectedUsers
      });
    } catch (err) {
      // Error handled by mutation
    } finally {
      setLoading(false);
    }
  };

  const getActionDescription = () => {
    switch (selectedAction) {
      case 'activate':
        return `Activate ${selectedUsers.length} user${selectedUsers.length !== 1 ? 's' : ''}. They will be able to sign in and access the system.`;
      case 'deactivate':
        return `Deactivate ${selectedUsers.length} user${selectedUsers.length !== 1 ? 's' : ''}. They will not be able to sign in but their data will be preserved.`;
      case 'delete':
        return `Permanently delete ${selectedUsers.length} user${selectedUsers.length !== 1 ? 's' : ''}. This action cannot be undone.`;
      case 'assign-roles':
        return `Assign selected roles to ${selectedUsers.length} user${selectedUsers.length !== 1 ? 's' : ''}. Existing roles will be preserved.`;
      case 'remove-roles':
        return `Remove selected roles from ${selectedUsers.length} user${selectedUsers.length !== 1 ? 's' : ''}. Other roles will be preserved.`;
      default:
        return '';
    }
  };

  const isActionDestructive = () => {
    return ['delete', 'deactivate'].includes(selectedAction);
  };

  const canSubmit = () => {
    if (!selectedAction) return false;
    if (['assign-roles', 'remove-roles'].includes(selectedAction)) {
      return selectedRoles.length > 0;
    }
    return true;
  };

  const getActionStats = () => {
    const activeUsers = selectedUserObjects.filter(u => u.is_active).length;
    const inactiveUsers = selectedUserObjects.filter(u => !u.is_active).length;
    const serviceAccounts = selectedUserObjects.filter(u => u.is_service_account).length;

    return { activeUsers, inactiveUsers, serviceAccounts };
  };

  const { activeUsers, inactiveUsers, serviceAccounts } = getActionStats();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>Bulk Actions</span>
          </DialogTitle>
          <DialogDescription>
            Perform actions on {selectedUsers.length} selected user{selectedUsers.length !== 1 ? 's' : ''}.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-6">
          {/* Selection Summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-lg font-bold text-blue-600">{activeUsers}</div>
              <div className="text-sm text-blue-600">Active Users</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-bold text-gray-600">{inactiveUsers}</div>
              <div className="text-sm text-gray-600">Inactive Users</div>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <div className="text-lg font-bold text-orange-600">{serviceAccounts}</div>
              <div className="text-sm text-orange-600">Service Accounts</div>
            </div>
          </div>

          {/* Action Selection */}
          <div>
            <label className="text-sm font-medium mb-2 block">Select Action</label>
            <Select value={selectedAction} onValueChange={(value) => {
              setSelectedAction(value);
              setSelectedRoles([]);
              setError(null);
            }}>
              <SelectTrigger>
                <SelectValue placeholder="Choose an action to perform" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="activate">
                  <div className="flex items-center space-x-2">
                    <UserCheck className="h-4 w-4 text-green-600" />
                    <span>Activate Users</span>
                  </div>
                </SelectItem>
                <SelectItem value="deactivate">
                  <div className="flex items-center space-x-2">
                    <UserX className="h-4 w-4 text-orange-600" />
                    <span>Deactivate Users</span>
                  </div>
                </SelectItem>
                <SelectItem value="assign-roles">
                  <div className="flex items-center space-x-2">
                    <Shield className="h-4 w-4 text-blue-600" />
                    <span>Assign Roles</span>
                  </div>
                </SelectItem>
                <SelectItem value="remove-roles">
                  <div className="flex items-center space-x-2">
                    <Shield className="h-4 w-4 text-purple-600" />
                    <span>Remove Roles</span>
                  </div>
                </SelectItem>
                <SelectItem value="delete">
                  <div className="flex items-center space-x-2">
                    <Trash2 className="h-4 w-4 text-red-600" />
                    <span>Delete Users</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Role Selection for Role Actions */}
          {['assign-roles', 'remove-roles'].includes(selectedAction) && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Select Roles</label>
                {rolesLoading && (
                  <Loader2 className="h-4 w-4 animate-spin" />
                )}
              </div>
              
              {rolesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span className="ml-2">Loading roles...</span>
                </div>
              ) : roles.length > 0 ? (
                <ScrollArea className="h-48 border rounded-md">
                  <div className="p-4 space-y-3">
                    {roles.map((role) => (
                      <div key={role.id} className="flex items-start space-x-3">
                        <Checkbox
                          checked={selectedRoles.includes(role.id)}
                          onCheckedChange={(checked) => 
                            handleRoleToggle(role.id, checked as boolean)
                          }
                          className="mt-1"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium text-sm">{role.display_name}</span>
                            <Badge variant="outline" className="text-xs">
                              {role.type}
                            </Badge>
                          </div>
                          {role.description && (
                            <p className="text-sm text-gray-600 mt-1">
                              {role.description}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <div className="text-center py-8">
                  <Shield className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-sm text-gray-500">No roles available</p>
                </div>
              )}

              {selectedRoles.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-blue-900 mb-2">
                    Selected Roles ({selectedRoles.length})
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {selectedRoles.map((roleId) => {
                      const role = roles.find(r => r.id === roleId);
                      return role ? (
                        <Badge key={roleId} variant="secondary" className="text-xs">
                          {role.display_name}
                        </Badge>
                      ) : null;
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Action Description */}
          {selectedAction && (
            <div className={`p-4 rounded-lg border ${
              isActionDestructive() 
                ? 'bg-red-50 border-red-200' 
                : 'bg-blue-50 border-blue-200'
            }`}>
              <div className="flex items-start space-x-3">
                <Info className={`h-4 w-4 mt-0.5 ${
                  isActionDestructive() ? 'text-red-600' : 'text-blue-600'
                }`} />
                <div className="text-sm">
                  <div className={`font-medium ${
                    isActionDestructive() ? 'text-red-900' : 'text-blue-900'
                  }`}>
                    {isActionDestructive() ? 'Warning' : 'Action Summary'}
                  </div>
                  <div className={`mt-1 ${
                    isActionDestructive() ? 'text-red-700' : 'text-blue-700'
                  }`}>
                    {getActionDescription()}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Selected Users List */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Affected Users ({selectedUsers.length})
            </label>
            <ScrollArea className="h-32 border rounded-md">
              <div className="p-3 space-y-2">
                {selectedUserObjects.map((user) => (
                  <div key={user.id} className="flex items-center justify-between text-sm">
                    <div>
                      <span className="font-medium">{getUserDisplayName(user)}</span>
                      <span className="text-gray-500 ml-2">{user.email}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      {user.is_service_account && (
                        <Badge variant="outline" className="text-xs">Service</Badge>
                      )}
                      <Badge
                        variant={user.is_active ? "default" : "secondary"}
                        className={`text-xs ${
                          user.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </div>

        <DialogFooter>
          <Button 
            type="button" 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit}
            disabled={loading || !canSubmit()}
            variant={isActionDestructive() ? 'destructive' : 'default'}
          >
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isActionDestructive() ? 'Confirm Action' : 'Apply Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}