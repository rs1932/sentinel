'use client';

import { useState, useEffect } from 'react';
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
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import { Group } from '@/types';

interface EditGroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  group: Group | null;
}

interface UpdateGroupForm {
  name: string;
  display_name: string;
  description: string;
  parent_group_id: string;
  is_active: boolean;
  metadata: Record<string, any>;
}

export function EditGroupDialog({ open, onOpenChange, group }: EditGroupDialogProps) {
  const [form, setForm] = useState<UpdateGroupForm>({
    name: '',
    display_name: '',
    description: '',
    parent_group_id: '',
    is_active: true,
    metadata: {},
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch available groups for parent selection
  const { data: groupsResponse } = useQuery({
    queryKey: ['groups'],
    queryFn: () => apiClient.groups.list(),
  });

  const availableGroups: Group[] = (groupsResponse?.items || groupsResponse || [])
    .filter((g: Group) => g.id !== group?.id); // Exclude self to prevent circular reference

  // Update form when group changes
  useEffect(() => {
    if (group) {
      setForm({
        name: group.name,
        display_name: group.display_name || '',
        description: group.description || '',
        parent_group_id: group.parent_group_id || 'none',
        is_active: group.is_active,
        metadata: group.metadata || {},
      });
    }
  }, [group]);

  const updateGroupMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      apiClient.groups.update(id, data),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Group updated successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      handleClose();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update group.',
        variant: 'destructive',
      });
    },
  });

  const handleClose = () => {
    onOpenChange(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!group) return;

    setIsSubmitting(true);

    try {
      const submitData = {
        display_name: form.display_name || undefined,
        description: form.description || undefined,
        parent_group_id: (form.parent_group_id && form.parent_group_id !== 'none') ? form.parent_group_id : undefined,
        is_active: form.is_active,
        metadata: form.metadata,
      };

      await updateGroupMutation.mutateAsync({ id: group.id, data: submitData });
    } catch (error) {
      // Error handled by mutation
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!group) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Group</DialogTitle>
          <DialogDescription>
            Update the group information and settings.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name
              </Label>
              <Input
                id="name"
                value={form.name}
                className="col-span-3"
                disabled
                title="Group name cannot be changed"
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
              <Label htmlFor="parent_group" className="text-right">
                Parent Group
              </Label>
              <Select
                value={form.parent_group_id}
                onValueChange={(value) => setForm({ ...form, parent_group_id: value })}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select parent group (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Parent (Root Group)</SelectItem>
                  {availableGroups.map((availableGroup) => (
                    <SelectItem key={availableGroup.id} value={availableGroup.id}>
                      {availableGroup.display_name || availableGroup.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
                placeholder="Brief description of this group's purpose"
                rows={3}
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="is_active" className="text-right">
                Active
              </Label>
              <Switch
                id="is_active"
                checked={form.is_active}
                onCheckedChange={(checked) => setForm({ ...form, is_active: checked })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Updating...' : 'Update Group'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}