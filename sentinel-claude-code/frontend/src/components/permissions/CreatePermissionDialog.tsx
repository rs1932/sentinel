'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
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
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';

interface CreatePermissionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface CreatePermissionForm {
  name: string;
  resource_type: string;
  resource_id: string;
  resource_path: string;
  actions: string[];
  conditions: Record<string, any>;
  field_permissions: Record<string, string[]>;
}

const RESOURCE_TYPES = [
  { value: 'product_family', label: 'Product Family' },
  { value: 'app', label: 'Application' },
  { value: 'capability', label: 'Capability' },
  { value: 'service', label: 'Service' },
  { value: 'entity', label: 'Entity' },
  { value: 'page', label: 'Page' },
  { value: 'api', label: 'API' },
];

const AVAILABLE_ACTIONS = [
  { value: 'create', label: 'Create' },
  { value: 'read', label: 'Read' },
  { value: 'update', label: 'Update' },
  { value: 'delete', label: 'Delete' },
  { value: 'execute', label: 'Execute' },
  { value: 'approve', label: 'Approve' },
  { value: 'reject', label: 'Reject' },
];

export function CreatePermissionDialog({ open, onOpenChange }: CreatePermissionDialogProps) {
  const [form, setForm] = useState<CreatePermissionForm>({
    name: '',
    resource_type: '',
    resource_id: '',
    resource_path: '',
    actions: [],
    conditions: {},
    field_permissions: {},
  });
  const [resourceTarget, setResourceTarget] = useState<'id' | 'path'>('path');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const createPermissionMutation = useMutation({
    mutationFn: (permissionData: any) => apiClient.permissions.create(permissionData),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Permission created successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['permissions'] });
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
      conditions: {},
      field_permissions: {},
    });
    setResourceTarget('path');
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
    setIsSubmitting(true);

    try {
      const submitData = {
        name: form.name,
        resource_type: form.resource_type,
        resource_id: resourceTarget === 'id' && form.resource_id ? form.resource_id : undefined,
        resource_path: resourceTarget === 'path' && form.resource_path ? form.resource_path : undefined,
        actions: form.actions,
        conditions: form.conditions,
        field_permissions: form.field_permissions,
        is_active: true,
      };

      await createPermissionMutation.mutateAsync(submitData);
    } catch (error) {
      // Error handled by mutation
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Permission</DialogTitle>
          <DialogDescription>
            Define a new permission for resources and actions.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name *
              </Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="col-span-3"
                placeholder="permission_name"
                required
              />
            </div>
            
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="resource_type" className="text-right">
                Resource Type *
              </Label>
              <Select
                value={form.resource_type}
                onValueChange={(value) => setForm({ ...form, resource_type: value })}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select resource type" />
                </SelectTrigger>
                <SelectContent>
                  {RESOURCE_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right pt-2">Resource Target</Label>
              <div className="col-span-3 space-y-3">
                <div className="flex items-center space-x-4">
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
                      Specific ID
                    </Label>
                  </div>
                </div>
                
                {resourceTarget === 'path' && (
                  <Input
                    value={form.resource_path}
                    onChange={(e) => setForm({ ...form, resource_path: e.target.value })}
                    placeholder="e.g., users/*, fleet/vehicles/*"
                  />
                )}
                
                {resourceTarget === 'id' && (
                  <Input
                    value={form.resource_id}
                    onChange={(e) => setForm({ ...form, resource_id: e.target.value })}
                    placeholder="Specific resource UUID"
                  />
                )}
              </div>
            </div>

            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right pt-2">Actions *</Label>
              <div className="col-span-3">
                <div className="grid grid-cols-2 gap-2">
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
                        {action.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isSubmitting || !form.name || !form.resource_type || form.actions.length === 0}
            >
              {isSubmitting ? 'Creating...' : 'Create Permission'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}