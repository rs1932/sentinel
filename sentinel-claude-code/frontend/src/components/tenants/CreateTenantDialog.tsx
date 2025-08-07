'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { apiClient } from '@/lib/api';
import { CreateTenantData, AVAILABLE_FEATURES } from '@/types';
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Plus } from 'lucide-react';

const createTenantSchema = z.object({
  name: z.string().min(1, 'Tenant name is required').max(255, 'Name must be less than 255 characters'),
  code: z.string()
    .min(1, 'Tenant code is required')
    .max(50, 'Code must be less than 50 characters')
    .regex(/^[A-Z0-9][A-Z0-9-]*$/, 'Code must contain only uppercase letters, numbers, and hyphens'),
  type: z.enum(['root', 'sub_tenant']).default('root'),
  isolation_mode: z.enum(['shared', 'dedicated']).default('shared'),
  features: z.array(z.string()).default([]),
});

type CreateTenantForm = z.infer<typeof createTenantSchema>;

interface CreateTenantDialogProps {
  isOpen: boolean;
  onClose: () => void;
  parentTenant?: string;
}

export function CreateTenantDialog({ isOpen, onClose, parentTenant }: CreateTenantDialogProps) {
  const [settingsJson, setSettingsJson] = useState('{}');
  const [metadataJson, setMetadataJson] = useState('{}');
  const [jsonErrors, setJsonErrors] = useState<{
    settings?: string;
    metadata?: string;
  }>({});

  const { toast } = useToast();
  const queryClient = useQueryClient();

  const form = useForm<CreateTenantForm>({
    resolver: zodResolver(createTenantSchema),
    defaultValues: {
      name: '',
      code: '',
      type: parentTenant ? 'sub_tenant' : 'root',
      isolation_mode: 'shared',
      features: ['api_access'], // Default feature
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateTenantData) => {
      if (parentTenant) {
        return apiClient.tenants.createSubTenant(parentTenant, data);
      } else {
        return apiClient.tenants.create(data);
      }
    },
    onSuccess: () => {
      toast({
        title: 'Success',
        description: `Tenant created successfully`,
      });
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      onClose();
      form.reset();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create tenant',
        variant: 'destructive',
      });
    },
  });

  const onSubmit = (data: CreateTenantForm) => {
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

    const tenantData: CreateTenantData = {
      ...data,
      parent_tenant_id: parentTenant,
      settings,
      metadata,
    };

    createMutation.mutate(tenantData);
  };

  const handleFeatureToggle = (featureValue: string, checked: boolean) => {
    const currentFeatures = form.getValues('features');
    if (checked) {
      form.setValue('features', [...currentFeatures, featureValue]);
    } else {
      form.setValue('features', currentFeatures.filter(f => f !== featureValue));
    }
  };

  const handleCodeChange = (value: string) => {
    // Auto-convert to uppercase and validate format
    const upperValue = value.toUpperCase().replace(/[^A-Z0-9-]/g, '');
    form.setValue('code', upperValue);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Create {parentTenant ? 'Sub-Tenant' : 'Tenant'}
          </DialogTitle>
          <DialogDescription>
            {parentTenant 
              ? 'Create a new sub-tenant under the selected parent tenant.'
              : 'Create a new root tenant organization.'
            }
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Basic Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

              <div className="space-y-2">
                <Label htmlFor="code">Tenant Code *</Label>
                <Input
                  id="code"
                  placeholder="ACME-CORP"
                  value={form.watch('code')}
                  onChange={(e) => handleCodeChange(e.target.value)}
                />
                <p className="text-xs text-gray-500">
                  Uppercase letters, numbers, and hyphens only
                </p>
                {form.formState.errors.code && (
                  <p className="text-sm text-red-600">{form.formState.errors.code.message}</p>
                )}
              </div>
            </div>

            {!parentTenant && (
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select
                  value={form.watch('type')}
                  onValueChange={(value) => form.setValue('type', value as 'root' | 'sub_tenant')}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="root">Root Tenant</SelectItem>
                    <SelectItem value="sub_tenant">Sub-Tenant</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="isolation_mode">Isolation Mode</Label>
              <Select
                value={form.watch('isolation_mode')}
                onValueChange={(value) => form.setValue('isolation_mode', value as 'shared' | 'dedicated')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="shared">
                    <div>
                      <div className="font-medium">Shared</div>
                      <div className="text-sm text-gray-500">Cost-effective, shared infrastructure</div>
                    </div>
                  </SelectItem>
                  <SelectItem value="dedicated">
                    <div>
                      <div className="font-medium">Dedicated</div>
                      <div className="text-sm text-gray-500">Isolated resources, enhanced security</div>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
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
            <h3 className="text-lg font-medium">Advanced Configuration</h3>
            
            <div className="space-y-2">
              <Label htmlFor="settings">Settings (JSON)</Label>
              <Textarea
                id="settings"
                placeholder='{"theme": "corporate", "locale": "en-US"}'
                value={settingsJson}
                onChange={(e) => setSettingsJson(e.target.value)}
                rows={3}
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
                rows={3}
              />
              {jsonErrors.metadata && (
                <p className="text-sm text-red-600">{jsonErrors.metadata}</p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={createMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Tenant
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}