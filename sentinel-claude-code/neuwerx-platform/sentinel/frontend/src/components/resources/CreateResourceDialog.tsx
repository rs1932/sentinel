'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Resource } from '@/types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from '@/hooks/use-toast';

interface CreateResourceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  parentId?: string | null;
  onSuccess: () => void;
}

const RESOURCE_TYPES = [
  { value: 'product_family', label: 'Product Family', emoji: '📦', description: 'Top-level product grouping' },
  { value: 'app', label: 'Application', emoji: '🎯', description: 'Application within a product family' },
  { value: 'capability', label: 'Capability', emoji: '⚡', description: 'Major feature or capability' },
  { value: 'service', label: 'Service', emoji: '🔧', description: 'Microservice or component' },
  { value: 'entity', label: 'Entity', emoji: '📋', description: 'Data entity or resource' },
  { value: 'page', label: 'Page', emoji: '📄', description: 'UI page or screen' },
  { value: 'api', label: 'API', emoji: '🔌', description: 'API endpoint or operation' },
];

const HIERARCHY_RULES = {
  product_family: [],
  app: ['product_family'],
  capability: ['product_family', 'app'],
  service: ['product_family', 'app', 'capability'],
  entity: ['product_family', 'app', 'capability', 'service'],
  page: ['product_family', 'app', 'capability', 'service'],
  api: ['product_family', 'app', 'capability', 'service'],
};

export function CreateResourceDialog({ open, onOpenChange, parentId, onSuccess }: CreateResourceDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    type: '' as string,
    description: '',
  });

  const queryClient = useQueryClient();

  // Fetch parent resource if parentId is provided
  const { data: parentResource } = useQuery({
    queryKey: ['resource', parentId],
    queryFn: () => apiClient.resources.get(parentId!),
    enabled: !!parentId,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData & { parent_id?: string }) => {
      return apiClient.resources.create(data);
    },
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Resource created successfully.',
      });
      onSuccess();
      onOpenChange(false);
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create resource.',
        variant: 'destructive',
      });
    },
  });

  const resetForm = () => {
    setFormData({
      name: '',
      code: '',
      type: '',
      description: '',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.code || !formData.type) {
      toast({
        title: 'Error',
        description: 'Please fill in all required fields.',
        variant: 'destructive',
      });
      return;
    }

    const submitData = {
      ...formData,
      ...(parentId && { parent_id: parentId }),
    };

    createMutation.mutate(submitData);
  };

  // Auto-generate code from name
  const handleNameChange = (name: string) => {
    setFormData(prev => ({
      ...prev,
      name,
      code: prev.code || name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
    }));
  };

  // Get allowed types based on parent
  const getAllowedTypes = () => {
    if (!parentId || !parentResource?.data) {
      // Root level - only product_family allowed
      return RESOURCE_TYPES.filter(type => type.value === 'product_family');
    }

    const parentType = parentResource.data.type;
    return RESOURCE_TYPES.filter(type => 
      (HIERARCHY_RULES[type.value as keyof typeof HIERARCHY_RULES] as string[]).includes(parentType)
    );
  };

  const allowedTypes = getAllowedTypes();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create Resource</DialogTitle>
            <DialogDescription>
              {parentId 
                ? `Create a new child resource under "${parentResource?.data?.name}"`
                : 'Create a new root-level resource'
              }
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {parentId && parentResource?.data && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <Label className="text-sm font-medium">Parent Resource</Label>
                <div className="flex items-center gap-2 mt-1">
                  <span>
                    {RESOURCE_TYPES.find(t => t.value === parentResource.data.type)?.emoji}
                  </span>
                  <span className="font-medium">{parentResource.data.name}</span>
                  <span className="text-sm text-gray-500">({parentResource.data.code})</span>
                </div>
              </div>
            )}

            <div className="grid gap-2">
              <Label htmlFor="type">Resource Type *</Label>
              <Select 
                value={formData.type} 
                onValueChange={(value) => setFormData(prev => ({ ...prev, type: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select resource type" />
                </SelectTrigger>
                <SelectContent>
                  {allowedTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex items-center gap-2">
                        <span>{type.emoji}</span>
                        <div>
                          <div className="font-medium">{type.label}</div>
                          <div className="text-xs text-gray-500">{type.description}</div>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleNameChange(e.target.value)}
                placeholder="Enter resource name"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="code">Code *</Label>
              <Input
                id="code"
                value={formData.code}
                onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value }))}
                placeholder="Enter resource code (e.g., user_management)"
              />
              <div className="text-xs text-gray-500">
                Unique identifier for this resource. Use lowercase letters, numbers, and underscores.
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe what this resource represents"
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isPending || !formData.name || !formData.code || !formData.type}
            >
              {createMutation.isPending ? 'Creating...' : 'Create Resource'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}