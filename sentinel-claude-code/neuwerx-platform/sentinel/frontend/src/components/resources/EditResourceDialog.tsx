'use client';

import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
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
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/hooks/use-toast';

interface EditResourceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resource: Resource;
  onSuccess: () => void;
}

const RESOURCE_TYPE_INFO = {
  product_family: { label: 'Product Family', emoji: '📦' },
  app: { label: 'Application', emoji: '🎯' },
  capability: { label: 'Capability', emoji: '⚡' },
  service: { label: 'Service', emoji: '🔧' },
  entity: { label: 'Entity', emoji: '📋' },
  page: { label: 'Page', emoji: '📄' },
  api: { label: 'API', emoji: '🔌' },
};

export function EditResourceDialog({ open, onOpenChange, resource, onSuccess }: EditResourceDialogProps) {
  const [formData, setFormData] = useState({
    name: resource.name,
    code: resource.code,
    description: resource.description || '',
    is_active: resource.is_active,
    metadata: JSON.stringify(resource.metadata || {}, null, 2),
  });

  // Update form when resource changes
  useEffect(() => {
    setFormData({
      name: resource.name,
      code: resource.code,
      description: resource.description || '',
      is_active: resource.is_active,
      metadata: JSON.stringify(resource.metadata || {}, null, 2),
    });
  }, [resource]);

  const updateMutation = useMutation({
    mutationFn: (data: {
      name: string;
      code: string;
      description: string;
      is_active: boolean;
      metadata: Record<string, any>;
    }) => {
      return apiClient.resources.update(resource.id, data);
    },
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Resource updated successfully.',
      });
      onSuccess();
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update resource.',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.code) {
      toast({
        title: 'Error',
        description: 'Please fill in all required fields.',
        variant: 'destructive',
      });
      return;
    }

    // Parse metadata JSON
    let parsedMetadata = {};
    try {
      parsedMetadata = JSON.parse(formData.metadata);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Invalid JSON in metadata field.',
        variant: 'destructive',
      });
      return;
    }

    const updateData = {
      name: formData.name,
      code: formData.code,
      description: formData.description,
      is_active: formData.is_active,
      metadata: parsedMetadata,
    };

    updateMutation.mutate(updateData);
  };

  const typeInfo = RESOURCE_TYPE_INFO[resource.type as keyof typeof RESOURCE_TYPE_INFO];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Resource</DialogTitle>
            <DialogDescription>
              Update the details for this resource.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Resource Type Display */}
            <div className="p-3 bg-gray-50 rounded-lg">
              <Label className="text-sm font-medium">Resource Type</Label>
              <div className="flex items-center gap-2 mt-1">
                <span>{typeInfo?.emoji}</span>
                <Badge variant="outline">{typeInfo?.label}</Badge>
                <span className="text-sm text-gray-500">Level {resource.level}</span>
              </div>
            </div>

            {/* Resource Path */}
            <div className="p-3 bg-blue-50 rounded-lg">
              <Label className="text-sm font-medium">Resource Path</Label>
              <div className="font-mono text-sm text-blue-700 mt-1">
                {resource.path}
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter resource name"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="code">Code *</Label>
              <Input
                id="code"
                value={formData.code}
                onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value }))}
                placeholder="Enter resource code"
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

            <div className="flex items-center space-x-2">
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_active: checked }))}
              />
              <Label htmlFor="is_active">Active</Label>
              <div className="text-xs text-gray-500 ml-2">
                {formData.is_active 
                  ? 'Resource is active and can be used' 
                  : 'Resource is inactive and hidden from most operations'
                }
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="metadata">Metadata (JSON)</Label>
              <Textarea
                id="metadata"
                value={formData.metadata}
                onChange={(e) => setFormData(prev => ({ ...prev, metadata: e.target.value }))}
                placeholder="Enter JSON metadata"
                rows={6}
                className="font-mono text-sm"
              />
              <div className="text-xs text-gray-500">
                Additional metadata for this resource in JSON format.
              </div>
            </div>

            {/* Resource Info */}
            <div className="p-3 bg-gray-50 rounded-lg">
              <Label className="text-sm font-medium">Resource Information</Label>
              <div className="text-sm text-gray-600 mt-1 space-y-1">
                <div><strong>ID:</strong> {resource.id}</div>
                <div><strong>Created:</strong> {new Date(resource.created_at).toLocaleString()}</div>
                <div><strong>Updated:</strong> {new Date(resource.updated_at).toLocaleString()}</div>
              </div>
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
              disabled={updateMutation.isPending || !formData.name || !formData.code}
            >
              {updateMutation.isPending ? 'Updating...' : 'Update Resource'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}