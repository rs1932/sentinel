'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, Shield, Users, Plus, X, Info } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface User {
  id: string;
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  roles?: Array<{
    id: string;
    name: string;
    display_name: string;
  }>;
}

interface Role {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  type: 'system' | 'custom';
  is_active: boolean;
  permissions_count?: number;
}

interface AssignRoleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user: User | null;
  onSuccess?: () => void;
}

export function AssignRoleDialog({ open, onOpenChange, user, onSuccess }: AssignRoleDialogProps) {
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch available roles
  const { data: rolesResponse, isLoading: rolesLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => apiClient.roles.list({
      is_active: true,
      limit: 100,
      sort_by: 'display_name',
      sort_order: 'asc'
    }),
    enabled: open
  });

  // Assign roles mutation
  const assignRolesMutation = useMutation({
    mutationFn: async (roleIds: string[]) => {
      if (!user) return;
      
      // Get current user roles
      const currentRoleIds = user.roles?.map(r => r.id) || [];
      
      // Determine roles to add and remove
      const rolesToAdd = roleIds.filter(id => !currentRoleIds.includes(id));
      const rolesToRemove = currentRoleIds.filter(id => !roleIds.includes(id));
      
      // Execute role assignments and removals
      const promises = [];
      
      // Add new roles
      for (const roleId of rolesToAdd) {
        promises.push(apiClient.roles.assignToUser(roleId, user.id));
      }
      
      // Remove roles
      for (const roleId of rolesToRemove) {
        promises.push(apiClient.roles.removeFromUser(roleId, user.id));
      }
      
      await Promise.all(promises);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      onSuccess?.();
      setError(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to assign roles');
    }
  });

  const roles = rolesResponse?.data || [];
  const currentUserRoleIds = user?.roles?.map(r => r.id) || [];

  // Initialize selected roles when user or dialog opens
  useEffect(() => {
    if (user && open) {
      setSelectedRoleIds(currentUserRoleIds);
      setError(null);
    }
  }, [user, open]);

  const getUserDisplayName = (user: User) => {
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return user.username || user.email.split('@')[0];
  };

  const getUserInitials = (user: User) => {
    if (user.first_name && user.last_name) {
      return `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase();
    }
    return user.email.charAt(0).toUpperCase();
  };

  const handleRoleToggle = (roleId: string, checked: boolean) => {
    if (checked) {
      setSelectedRoleIds([...selectedRoleIds, roleId]);
    } else {
      setSelectedRoleIds(selectedRoleIds.filter(id => id !== roleId));
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);
      await assignRolesMutation.mutateAsync(selectedRoleIds);
      onOpenChange(false);
    } catch (err) {
      // Error is handled by mutation
    } finally {
      setLoading(false);
    }
  };

  const hasChanges = () => {
    const current = new Set(currentUserRoleIds);
    const selected = new Set(selectedRoleIds);
    
    if (current.size !== selected.size) return true;
    
    for (const id of current) {
      if (!selected.has(id)) return true;
    }
    
    return false;
  };

  const getRolesByType = () => {
    const systemRoles = roles.filter(r => r.type === 'system');
    const customRoles = roles.filter(r => r.type === 'custom');
    return { systemRoles, customRoles };
  };

  const { systemRoles, customRoles } = getRolesByType();

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Assign Roles</span>
          </DialogTitle>
          <DialogDescription>
            Manage role assignments for user. Roles determine what actions and resources the user can access.
          </DialogDescription>
        </DialogHeader>

        {/* User Info */}
        <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
          <Avatar className="h-10 w-10">
            <AvatarFallback>{getUserInitials(user)}</AvatarFallback>
          </Avatar>
          <div>
            <div className="font-medium">{getUserDisplayName(user)}</div>
            <div className="text-sm text-gray-500">{user.email}</div>
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <ScrollArea className="max-h-[400px]">
          <div className="space-y-6">
            {/* Current Roles */}
            {user.roles && user.roles.length > 0 && (
              <div>
                <div className="flex items-center space-x-2 mb-3">
                  <Badge variant="outline" className="text-xs">
                    Current
                  </Badge>
                  <span className="text-sm font-medium">Currently Assigned Roles</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {user.roles.map((role) => (
                    <Badge key={role.id} variant="default" className="text-xs">
                      {role.display_name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {rolesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="ml-2">Loading roles...</span>
              </div>
            ) : (
              <div className="space-y-6">
                {/* System Roles */}
                {systemRoles.length > 0 && (
                  <div>
                    <div className="flex items-center space-x-2 mb-4">
                      <Shield className="h-4 w-4 text-blue-600" />
                      <h4 className="text-sm font-medium">System Roles</h4>
                    </div>
                    <div className="space-y-3">
                      {systemRoles.map((role) => (
                        <div key={role.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                          <Checkbox
                            checked={selectedRoleIds.includes(role.id)}
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
                              {role.permissions_count && (
                                <span className="text-xs text-gray-500">
                                  {role.permissions_count} permissions
                                </span>
                              )}
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
                  </div>
                )}

                {/* Custom Roles */}
                {customRoles.length > 0 && (
                  <div>
                    <div className="flex items-center space-x-2 mb-4">
                      <Users className="h-4 w-4 text-purple-600" />
                      <h4 className="text-sm font-medium">Custom Roles</h4>
                    </div>
                    <div className="space-y-3">
                      {customRoles.map((role) => (
                        <div key={role.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                          <Checkbox
                            checked={selectedRoleIds.includes(role.id)}
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
                              {role.permissions_count && (
                                <span className="text-xs text-gray-500">
                                  {role.permissions_count} permissions
                                </span>
                              )}
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
                  </div>
                )}

                {roles.length === 0 && (
                  <div className="text-center py-8">
                    <Shield className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                    <h4 className="text-sm font-medium text-gray-900 mb-2">No roles available</h4>
                    <p className="text-sm text-gray-500">
                      No roles are currently available for assignment.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Summary */}
        {hasChanges() && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <Info className="h-4 w-4 text-blue-600 mt-0.5" />
              <div className="text-sm">
                <div className="font-medium text-blue-900">Changes Summary</div>
                <div className="text-blue-700 mt-1">
                  {selectedRoleIds.length} role{selectedRoleIds.length !== 1 ? 's' : ''} will be assigned to this user
                </div>
              </div>
            </div>
          </div>
        )}

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
            disabled={loading || !hasChanges()}
          >
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {hasChanges() ? 'Save Changes' : 'No Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}