'use client';

import { useState } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
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
import { useToast } from '@/hooks/use-toast';
import { Role } from '@/types';

interface CreateRoleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface CreateRoleForm {
  name: string;
  display_name: string;
  description: string;
  type: 'system' | 'custom';
  parent_role_id: string;
  priority: number;
  role_metadata: Record<string, any>;
}

export function CreateRoleDialog({ open, onOpenChange }: CreateRoleDialogProps) {
  const [form, setForm] = useState<CreateRoleForm>({
    name: '',
    display_name: '',
    description: '',
    type: 'custom',
    parent_role_id: '',
    priority: 0,
    role_metadata: {},
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch available roles for parent selection
  const { data: rolesResponse } = useQuery({
    queryKey: ['roles'],
    queryFn: () => apiClient.roles.list(),
  });

  const availableRoles: Role[] = rolesResponse?.items || rolesResponse || [];

  const createRoleMutation = useMutation({
    mutationFn: (roleData: any) => apiClient.roles.create(roleData),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Role created successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      handleClose();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create role.',
        variant: 'destructive',
      });
    },
  });

  const handleClose = () => {
    setForm({
      name: '',
      display_name: '',
      description: '',
      type: 'custom',
      parent_role_id: '',
      priority: 0,
      role_metadata: {},
    });
    onOpenChange(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const submitData = {
        name: form.name,
        display_name: form.display_name || undefined,
        description: form.description || undefined,
        type: form.type,
        parent_role_id: (form.parent_role_id && form.parent_role_id !== 'none') ? form.parent_role_id : undefined,
        priority: form.priority,
        role_metadata: form.role_metadata,
        is_assignable: true,
        is_active: true,
      };

      await createRoleMutation.mutateAsync(submitData);
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
          <DialogTitle>Create Role</DialogTitle>
          <DialogDescription>
            Create a new role with specific permissions and hierarchy.
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
                placeholder="role_name"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="display_name" className="text-right">
                Display Name
              </Label>
              <Input
                id="display_name"
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                className="col-span-3"
                placeholder="Human Readable Name"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="type" className="text-right">
                Type
              </Label>
              <Select
                value={form.type}
                onValueChange={(value: 'system' | 'custom') => setForm({ ...form, type: value })}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="custom">Custom</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="parent_role" className="text-right">
                Parent Role
              </Label>
              <Select
                value={form.parent_role_id}
                onValueChange={(value) => setForm({ ...form, parent_role_id: value })}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select parent role (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Parent (Root Role)</SelectItem>
                  {availableRoles.map((role) => (
                    <SelectItem key={role.id} value={role.id}>
                      {role.display_name || role.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="priority" className="text-right">
                Priority
              </Label>
              <Input
                id="priority"
                type="number"
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: parseInt(e.target.value) || 0 })}
                className="col-span-3"
                placeholder="0-100 (higher = more priority)"
                min={0}
                max={100}
              />
            </div>
            <div className="grid grid-cols-4 items-start gap-4">
              <Label htmlFor="description" className="text-right pt-2">
                Description
              </Label>
              <Textarea
                id="description"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="col-span-3"
                placeholder="Brief description of this role's purpose"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !form.name}>
              {isSubmitting ? 'Creating...' : 'Create Role'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}