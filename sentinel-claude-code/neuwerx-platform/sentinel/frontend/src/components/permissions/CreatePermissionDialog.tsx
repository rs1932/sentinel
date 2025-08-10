'use client';

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from '@/hooks/use-toast';

interface CreatePermissionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

interface CreatePermissionForm {
  name: string;
  resource_type: string;
  resource_id: string;
  resource_path: string;
  actions: string[];
  conditions: string;
  field_permissions: string;
}

const RESOURCE_TYPES = [
  { value: 'product_family', label: 'Product Family', emoji: '📦' },
  { value: 'app', label: 'Application', emoji: '🎯' },
  { value: 'capability', label: 'Capability', emoji: '⚡' },
  { value: 'service', label: 'Service', emoji: '🔧' },
  { value: 'entity', label: 'Entity', emoji: '📋' },
  { value: 'page', label: 'Page', emoji: '📄' },
  { value: 'api', label: 'API', emoji: '🔌' },
];

const AVAILABLE_ACTIONS = [
  { value: 'create', label: 'Create', color: 'bg-purple-100 text-purple-700' },
  { value: 'read', label: 'Read', color: 'bg-green-100 text-green-700' },
  { value: 'update', label: 'Update', color: 'bg-blue-100 text-blue-700' },
  { value: 'delete', label: 'Delete', color: 'bg-red-100 text-red-700' },
  { value: 'execute', label: 'Execute', color: 'bg-orange-100 text-orange-700' },
  { value: 'approve', label: 'Approve', color: 'bg-emerald-100 text-emerald-700' },
  { value: 'reject', label: 'Reject', color: 'bg-rose-100 text-rose-700' },
];

export function CreatePermissionDialog({ open, onOpenChange, onSuccess }: CreatePermissionDialogProps) {
  const [form, setForm] = useState<CreatePermissionForm>({
    name: '',
    resource_type: '',
    resource_id: '',
    resource_path: '',
    actions: [],
    conditions: '{}',
    field_permissions: '{}',
  });
  const [resourceTarget, setResourceTarget] = useState<'id' | 'path' | 'global'>('global');

  // Fetch resources for dropdown
  const { data: resourcesResponse } = useQuery({
    queryKey: ['resources', 'list'],
    queryFn: () => apiClient.resources.list({ 
      type: form.resource_type || undefined,
      limit: 1000 
    }),
    enabled: resourceTarget === 'id' && !!form.resource_type,
  });

  const createPermissionMutation = useMutation({
    mutationFn: (permissionData: any) => apiClient.permissions.create(permissionData),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Permission created successfully.',
      });
      if (onSuccess) onSuccess();
      handleClose();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create permission.',
        variant: 'destructive',
      });
    },
  });

  const handleClose = () => {
    setForm({
      name: '',
      resource_type: '',
      resource_id: '',
      resource_path: '',
      actions: [],
      conditions: '{}',
      field_permissions: '{}',
    });
    setResourceTarget('global');
    onOpenChange(false);
  };

  const handleActionChange = (action: string, checked: boolean) => {
    if (checked) {
      setForm({ ...form, actions: [...form.actions, action] });
    } else {
      setForm({ ...form, actions: form.actions.filter(a => a !== action) });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Parse JSON fields
      let parsedConditions = {};
      let parsedFieldPermissions = {};

      try {
        parsedConditions = JSON.parse(form.conditions);
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Invalid JSON in conditions field.',
          variant: 'destructive',
        });
        return;
      }

      try {
        parsedFieldPermissions = JSON.parse(form.field_permissions);
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Invalid JSON in field permissions.',
          variant: 'destructive',
        });
        return;
      }

      const submitData = {
        name: form.name,
        resource_type: form.resource_type,
        resource_id: resourceTarget === 'id' && form.resource_id ? form.resource_id : null,
        resource_path: resourceTarget === 'path' && form.resource_path ? form.resource_path : null,
        actions: form.actions,
        conditions: parsedConditions,
        field_permissions: parsedFieldPermissions,
        is_active: true,
      };

      await createPermissionMutation.mutateAsync(submitData);
    } catch (error) {
      // Error handled by mutation
    }
  };

  const resources = resourcesResponse?.data?.resources || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Permission</DialogTitle>
          <DialogDescription>
            Define a new permission for resources and actions.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Details */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Permission Name *</Label>
                <Input
                  id="name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="permission_name"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="resource_type">Resource Type *</Label>
                <Select
                  value={form.resource_type}
                  onValueChange={(value) => setForm({ ...form, resource_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select resource type" />
                  </SelectTrigger>
                  <SelectContent>
                    {RESOURCE_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <div className="flex items-center gap-2">
                          <span>{type.emoji}</span>
                          <span>{type.label}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Separator />

          {/* Resource Target */}
          <div className="space-y-4">
            <div>
              <Label className="text-base font-medium">Resource Target</Label>
              <p className="text-sm text-gray-600 mb-3">
                Specify which resources this permission applies to.
              </p>
            </div>

            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="target-global"
                  checked={resourceTarget === 'global'}
                  onCheckedChange={() => setResourceTarget('global')}
                />
                <Label htmlFor="target-global" className="text-sm">
                  Global (All resources)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="target-path"
                  checked={resourceTarget === 'path'}
                  onCheckedChange={() => setResourceTarget('path')}
                />
                <Label htmlFor="target-path" className="text-sm">
                  Path Pattern
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="target-id"
                  checked={resourceTarget === 'id'}
                  onCheckedChange={() => setResourceTarget('id')}
                />
                <Label htmlFor="target-id" className="text-sm">
                  Specific Resource
                </Label>
              </div>
            </div>
            
            {resourceTarget === 'path' && (
              <div className="space-y-2">
                <Label htmlFor="resource_path">Resource Path Pattern</Label>
                <Input
                  id="resource_path"
                  value={form.resource_path}
                  onChange={(e) => setForm({ ...form, resource_path: e.target.value })}
                  placeholder="e.g., users/*, fleet/vehicles/*"
                />
                <p className="text-xs text-gray-500">
                  Use wildcards (*) to match multiple resources. Examples: users/*, api/v1/*
                </p>
              </div>
            )}
            
            {resourceTarget === 'id' && (
              <div className="space-y-2">
                <Label htmlFor="resource_id">Specific Resource</Label>
                <Select
                  value={form.resource_id}
                  onValueChange={(value) => setForm({ ...form, resource_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a specific resource" />
                  </SelectTrigger>
                  <SelectContent>
                    {resources.map((resource: any) => (
                      <SelectItem key={resource.id} value={resource.id}>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{resource.name}</span>
                          <span className="text-xs text-gray-500">({resource.code})</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          <Separator />

          {/* Actions */}
          <div className="space-y-4">
            <div>
              <Label className="text-base font-medium">Actions *</Label>
              <p className="text-sm text-gray-600 mb-3">
                Select which actions this permission allows.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {AVAILABLE_ACTIONS.map((action) => (
                <div key={action.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`action-${action.value}`}
                    checked={form.actions.includes(action.value)}
                    onCheckedChange={(checked) => 
                      handleActionChange(action.value, checked as boolean)
                    }
                  />
                  <Label htmlFor={`action-${action.value}`} className="text-sm">
                    <Badge variant="outline" className={action.color}>
                      {action.label}
                    </Badge>
                  </Label>
                </div>
              ))}
            </div>

            {form.actions.length === 0 && (
              <p className="text-sm text-red-600">At least one action must be selected.</p>
            )}
          </div>

          <Separator />

          {/* Advanced Configuration */}
          <div className="space-y-4">
            <div>
              <Label className="text-base font-medium">Advanced Configuration</Label>
              <p className="text-sm text-gray-600 mb-3">
                Optional JSON configuration for conditions and field-level permissions.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div className="space-y-2">
                <Label htmlFor="conditions">Conditions (JSON)</Label>
                <Textarea
                  id="conditions"
                  value={form.conditions}
                  onChange={(e) => setForm({ ...form, conditions: e.target.value })}
                  placeholder='{"user_id": "$current_user", "status": "active"}'
                  rows={4}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-gray-500">
                  JSON conditions that must be met for this permission to apply.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="field_permissions">Field Permissions (JSON)</Label>
                <Textarea
                  id="field_permissions"
                  value={form.field_permissions}
                  onChange={(e) => setForm({ ...form, field_permissions: e.target.value })}
                  placeholder='{"email": ["read"], "password": ["hidden"], "name": ["read", "write"]}'
                  rows={4}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-gray-500">
                  Define field-level permissions. Values: read, write, hidden.
                </p>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createPermissionMutation.isPending || !form.name || !form.resource_type || form.actions.length === 0}
            >
              {createPermissionMutation.isPending ? 'Creating...' : 'Create Permission'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}