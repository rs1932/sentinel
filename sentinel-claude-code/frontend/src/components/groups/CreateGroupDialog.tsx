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
import { Group } from '@/types';

interface CreateGroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface CreateGroupForm {
  name: string;
  display_name: string;
  description: string;
  parent_group_id: string;
  metadata: Record<string, any>;
}

export function CreateGroupDialog({ open, onOpenChange }: CreateGroupDialogProps) {
  const [form, setForm] = useState<CreateGroupForm>({
    name: '',
    display_name: '',
    description: '',
    parent_group_id: '',
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

  const availableGroups: Group[] = groupsResponse?.items || groupsResponse || [];

  const createGroupMutation = useMutation({
    mutationFn: (groupData: any) => apiClient.groups.create(groupData),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Group created successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      handleClose();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create group.',
        variant: 'destructive',
      });
    },
  });

  const handleClose = () => {
    setForm({
      name: '',
      display_name: '',
      description: '',
      parent_group_id: '',
      metadata: {},
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
        parent_group_id: (form.parent_group_id && form.parent_group_id !== 'none') ? form.parent_group_id : undefined,
        metadata: form.metadata,
      };

      await createGroupMutation.mutateAsync(submitData);
    } catch (error) {
      // Error handled by mutation
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create Group</DialogTitle>
          <DialogDescription>
            Create a new group to organize users and assign roles.
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
                placeholder="internal_name"
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
                  {availableGroups.map((group) => (
                    <SelectItem key={group.id} value={group.id}>
                      {group.display_name || group.name}
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
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !form.name}>
              {isSubmitting ? 'Creating...' : 'Create Group'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}