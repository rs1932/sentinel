'use client';

import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { apiClient } from '@/lib/api';
import { Tenant, UpdateTenantData, AVAILABLE_FEATURES } from '@/types';
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
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Save, Building2 } from 'lucide-react';

const updateTenantSchema = z.object({
  name: z.string().min(1, 'Tenant name is required').max(255, 'Name must be less than 255 characters'),
  features: z.array(z.string()).default([]),
  is_active: z.boolean().default(true),
});

type UpdateTenantForm = z.infer<typeof updateTenantSchema>;

interface EditTenantDialogProps {
  isOpen: boolean;
  tenant: Tenant;
  onClose: () => void;
}

export function EditTenantDialog({ isOpen, tenant, onClose }: EditTenantDialogProps) {
  const [settingsJson, setSettingsJson] = useState('');
  const [metadataJson, setMetadataJson] = useState('');
  const [jsonErrors, setJsonErrors] = useState<{
    settings?: string;
    metadata?: string;
  }>({});

  const { toast } = useToast();
  const queryClient = useQueryClient();

  const form = useForm<UpdateTenantForm>({
    resolver: zodResolver(updateTenantSchema),
    defaultValues: {
      name: tenant.name,
      features: tenant.features || [],
      is_active: tenant.is_active,
    },
  });

  // Initialize JSON fields when tenant changes
  useEffect(() => {
    setSettingsJson(JSON.stringify(tenant.settings || {}, null, 2));
    setMetadataJson(JSON.stringify(tenant.metadata || {}, null, 2));
    form.reset({
      name: tenant.name,
      features: tenant.features || [],
      is_active: tenant.is_active,
    });
  }, [tenant, form]);

  const updateMutation = useMutation({
    mutationFn: (data: UpdateTenantData) => apiClient.tenants.update(tenant.id, data),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Tenant updated successfully',
      });
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      onClose();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update tenant',
        variant: 'destructive',
      });
    },
  });

  const onSubmit = (data: UpdateTenantForm) => {
    // Validate JSON fields
    let settings = {};
    let metadata = {};
    const errors: typeof jsonErrors = {};

    try {
      settings = JSON.parse(settingsJson);
    } catch (e) {
      errors.settings = 'Invalid JSON format';
    }

    try {
      metadata = JSON.parse(metadataJson);
    } catch (e) {
      errors.metadata = 'Invalid JSON format';
    }

    setJsonErrors(errors);

    if (Object.keys(errors).length > 0) {
      return;
    }

    const tenantData: UpdateTenantData = {
      ...data,
      settings,
      metadata,
    };

    updateMutation.mutate(tenantData);
  };

  const handleFeatureToggle = (featureValue: string, checked: boolean) => {
    const currentFeatures = form.getValues('features');
    if (checked) {
      form.setValue('features', [...currentFeatures, featureValue]);
    } else {
      form.setValue('features', currentFeatures.filter(f => f !== featureValue));
    }
  };

  const formatJsonField = (setter: (value: string) => void, currentValue: string) => {
    try {
      const parsed = JSON.parse(currentValue);
      setter(JSON.stringify(parsed, null, 2));
      setJsonErrors(prev => ({ ...prev, [setter === setSettingsJson ? 'settings' : 'metadata']: undefined }));
    } catch (e) {
      // If it's not valid JSON, leave as-is
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Edit Tenant: {tenant.name}
          </DialogTitle>
          <DialogDescription>
            Update tenant information and configuration. Note that some fields like code and type cannot be changed.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Read-only Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Tenant Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Code (Read-only)</Label>
                <Input value={tenant.code} disabled className="bg-gray-50" />
              </div>
              
              <div className="space-y-2">
                <Label>Type (Read-only)</Label>
                <div className="flex items-center h-10">
                  <Badge variant="outline" className="capitalize">
                    {tenant.type.replace('_', ' ')}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Isolation Mode (Read-only)</Label>
              <div className="flex items-center h-10">
                <Badge variant="outline" className="capitalize">
                  {tenant.isolation_mode}
                </Badge>
              </div>
            </div>
          </div>

          <Separator />

          {/* Editable Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Editable Settings</h3>
            
            <div className="space-y-2">
              <Label htmlFor="name">Tenant Name *</Label>
              <Input
                id="name"
                placeholder="Acme Corporation"
                {...form.register('name')}
              />
              {form.formState.errors.name && (
                <p className="text-sm text-red-600">{form.formState.errors.name.message}</p>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="is_active"
                checked={form.watch('is_active')}
                onCheckedChange={(checked) => form.setValue('is_active', checked)}
              />
              <Label htmlFor="is_active" className="text-sm">
                Tenant is active
              </Label>
            </div>
          </div>

          <Separator />

          {/* Features */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {AVAILABLE_FEATURES.map((feature) => (
                <div key={feature.value} className="flex items-start space-x-2">
                  <Checkbox
                    id={feature.value}
                    checked={form.watch('features').includes(feature.value)}
                    onCheckedChange={(checked) => handleFeatureToggle(feature.value, !!checked)}
                  />
                  <div className="grid gap-1.5 leading-none">
                    <Label
                      htmlFor={feature.value}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      {feature.label}
                    </Label>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* Advanced Configuration */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Advanced Configuration</h3>
              <div className="text-xs text-gray-500">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => formatJsonField(setSettingsJson, settingsJson)}
                >
                  Format Settings
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => formatJsonField(setMetadataJson, metadataJson)}
                >
                  Format Metadata
                </Button>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="settings">Settings (JSON)</Label>
              <Textarea
                id="settings"
                placeholder='{"theme": "corporate", "locale": "en-US"}'
                value={settingsJson}
                onChange={(e) => setSettingsJson(e.target.value)}
                rows={4}
                className="font-mono text-sm"
              />
              {jsonErrors.settings && (
                <p className="text-sm text-red-600">{jsonErrors.settings}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="metadata">Metadata (JSON)</Label>
              <Textarea
                id="metadata"
                placeholder='{"industry": "Technology", "company_size": "Enterprise"}'
                value={metadataJson}
                onChange={(e) => setMetadataJson(e.target.value)}
                rows={4}
                className="font-mono text-sm"
              />
              {jsonErrors.metadata && (
                <p className="text-sm text-red-600">{jsonErrors.metadata}</p>
              )}
            </div>
          </div>

          <Separator />

          {/* Timestamps */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-600">Timestamps</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-500">
              <div>
                <span className="font-medium">Created:</span> {new Date(tenant.created_at).toLocaleString()}
              </div>
              <div>
                <span className="font-medium">Updated:</span> {new Date(tenant.updated_at).toLocaleString()}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={updateMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}