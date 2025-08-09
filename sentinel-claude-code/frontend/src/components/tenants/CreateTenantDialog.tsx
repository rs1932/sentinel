'use client';

import { useState, useEffect } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { apiClient } from '@/lib/api';
import { CreateTenantData, AVAILABLE_FEATURES, Tenant } from '@/types';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { 
  Loader2, 
  Building2, 
  Shield, 
  Sparkles, 
  Settings2,
  AlertCircle,
  Info,
  GitBranch,
  Cloud,
  Server,
  Check,
  X,
  ChevronDown,
  Building,
  Lock,
  Zap,
  Users,
  FileText,
  Brain,
  Workflow,
  Key
} from 'lucide-react';

const createTenantSchema = z.object({
  name: z.string().min(1, 'Organization name is required').max(255, 'Name must be less than 255 characters'),
  code: z.string()
    .min(1, 'Organization code is required')
    .max(50, 'Code must be less than 50 characters')
    .regex(/^[A-Z0-9][A-Z0-9-]*$/, 'Code must contain only uppercase letters, numbers, and hyphens'),
  type: z.enum(['root', 'sub_tenant']),
  parent_tenant_id: z.string().optional(),
  isolation_mode: z.enum(['shared', 'dedicated']),
  features: z.array(z.string()),
});

type CreateTenantForm = z.infer<typeof createTenantSchema>;

interface CreateTenantDialogProps {
  isOpen: boolean;
  onClose: () => void;
  parentTenant?: string;
}

// Feature icons mapping
const FEATURE_ICONS: Record<string, any> = {
  multi_factor_auth: Shield,
  advanced_audit: FileText,
  ai_insights: Brain,
  custom_workflows: Workflow,
  api_access: Zap,
  sso: Users,
  field_encryption: Lock,
  compliance_reporting: FileText,
};

// Feature descriptions for better UX
const FEATURE_DESCRIPTIONS: Record<string, string> = {
  multi_factor_auth: 'Add an extra layer of security with 2FA/MFA support',
  advanced_audit: 'Track all actions with detailed audit logs and reporting',
  ai_insights: 'Get intelligent insights and predictions powered by AI',
  custom_workflows: 'Build custom workflows and automation for your processes',
  api_access: 'Full REST API access for integrations and automation',
  sso: 'Enable Single Sign-On with SAML, OAuth, and other providers',
  field_encryption: 'Encrypt sensitive fields at the database level',
  compliance_reporting: 'Generate compliance reports for GDPR, HIPAA, SOC2, etc.',
};

export function CreateTenantDialog({ isOpen, onClose, parentTenant }: CreateTenantDialogProps) {
  const [activeTab, setActiveTab] = useState('basic');
  const [tenantType, setTenantType] = useState<'root' | 'sub_tenant'>(parentTenant ? 'sub_tenant' : 'root');
  const [selectedParent, setSelectedParent] = useState<string>(parentTenant || '');
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [customSettings, setCustomSettings] = useState<Record<string, any>>({});
  const [customMetadata, setCustomMetadata] = useState<Record<string, any>>({});

  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch available parent tenants for sub-tenant creation
  const { data: parentTenants } = useQuery({
    queryKey: ['parent-tenants'],
    queryFn: () => apiClient.tenants.list({ type: 'root', limit: 100 }),
    enabled: isOpen && !parentTenant,
  });

  const form = useForm<CreateTenantForm>({
    resolver: zodResolver(createTenantSchema),
    defaultValues: {
      name: '',
      code: '',
      type: tenantType,
      parent_tenant_id: selectedParent,
      isolation_mode: 'shared',
      features: ['api_access'], // Default feature
    },
  });

  // Update form when tenant type changes
  useEffect(() => {
    form.setValue('type', tenantType);
    if (tenantType === 'root') {
      form.setValue('parent_tenant_id', undefined);
      setSelectedParent('');
    }
  }, [tenantType, form]);

  // Update form when parent selection changes
  useEffect(() => {
    if (selectedParent) {
      form.setValue('parent_tenant_id', selectedParent);
    }
  }, [selectedParent, form]);

  const createMutation = useMutation({
    mutationFn: (data: CreateTenantData) => {
      return apiClient.tenants.create(data);
    },
    onSuccess: () => {
      toast({
        title: '✓ Tenant Created Successfully',
        description: `${form.getValues('name')} has been created.`,
      });
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      handleClose();
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to Create Tenant',
        description: error.message || 'An error occurred while creating the tenant.',
        variant: 'destructive',
      });
    },
  });

  const handleClose = () => {
    form.reset();
    setActiveTab('basic');
    setTenantType('root');
    setSelectedParent('');
    setShowAdvancedSettings(false);
    setCustomSettings({});
    setCustomMetadata({});
    onClose();
  };

  const onSubmit = (data: CreateTenantForm) => {
    const tenantData: CreateTenantData = {
      ...data,
      settings: customSettings,
      metadata: customMetadata,
    };

    // Remove parent_tenant_id if it's a root tenant
    if (data.type === 'root') {
      delete tenantData.parent_tenant_id;
    }

    createMutation.mutate(tenantData);
  };

  const handleFeatureToggle = (featureValue: string) => {
    const currentFeatures = form.getValues('features');
    const isChecked = currentFeatures.includes(featureValue);
    
    if (isChecked) {
      form.setValue('features', currentFeatures.filter(f => f !== featureValue));
    } else {
      form.setValue('features', [...currentFeatures, featureValue]);
    }
  };

  const handleCodeChange = (value: string) => {
    // Auto-convert to uppercase and validate format
    const upperValue = value.toUpperCase().replace(/[^A-Z0-9-]/g, '');
    form.setValue('code', upperValue);
  };

  const addCustomSetting = (key: string, value: string) => {
    if (key && value) {
      setCustomSettings({ ...customSettings, [key]: value });
    }
  };

  const addCustomMetadata = (key: string, value: string) => {
    if (key && value) {
      setCustomMetadata({ ...customMetadata, [key]: value });
    }
  };

  const isFormValid = () => {
    const values = form.getValues();
    return values.name && 
           values.code && 
           (values.type === 'root' || values.parent_tenant_id) &&
           values.features.length > 0;
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-6xl h-[85vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <DialogTitle className="text-xl font-semibold flex items-center gap-2">
            <Building2 className="h-5 w-5 text-blue-600" />
            Create New Organization
          </DialogTitle>
          <DialogDescription>
            Set up a new {tenantType === 'sub_tenant' ? 'sub-organization under a parent' : 'root organization'} with customized features and settings.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(onSubmit)} className="flex-1 overflow-hidden flex flex-col">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
            <TabsList className="grid w-full grid-cols-4 mx-8 mt-4 h-12" style={{ width: 'calc(100% - 4rem)' }}>
              <TabsTrigger value="basic" className="flex items-center gap-2">
                <Building className="h-4 w-4" />
                <span className="hidden sm:inline">Basic Info</span>
                <span className="sm:hidden">Basic</span>
              </TabsTrigger>
              <TabsTrigger value="hierarchy" className="flex items-center gap-2">
                <GitBranch className="h-4 w-4" />
                <span className="hidden sm:inline">Hierarchy</span>
                <span className="sm:hidden">Type</span>
              </TabsTrigger>
              <TabsTrigger value="features" className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Features
              </TabsTrigger>
              <TabsTrigger value="settings" className="flex items-center gap-2">
                <Settings2 className="h-4 w-4" />
                Settings
              </TabsTrigger>
            </TabsList>

            <div className="flex-1 overflow-y-auto px-8 py-6">
              {/* Basic Information Tab */}
              <TabsContent value="basic" className="mt-0 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Organization Details</CardTitle>
                    <CardDescription>
                      Enter the basic information for your new organization
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="name">Organization Name *</Label>
                      <Input
                        id="name"
                        placeholder="e.g., Acme Corporation"
                        {...form.register('name')}
                        className="text-base"
                      />
                      {form.formState.errors.name && (
                        <p className="text-sm text-red-600 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {form.formState.errors.name.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="code">Organization Code *</Label>
                      <Input
                        id="code"
                        placeholder="e.g., ACME-CORP"
                        value={form.watch('code')}
                        onChange={(e) => handleCodeChange(e.target.value)}
                        className="font-mono text-base"
                      />
                      <p className="text-xs text-muted-foreground">
                        A unique identifier using uppercase letters, numbers, and hyphens. This cannot be changed later.
                      </p>
                      {form.formState.errors.code && (
                        <p className="text-sm text-red-600 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {form.formState.errors.code.message}
                        </p>
                      )}
                    </div>

                    <Separator />

                    <div className="space-y-3">
                      <Label>Infrastructure Mode</Label>
                      <RadioGroup 
                        value={form.watch('isolation_mode')} 
                        onValueChange={(value) => form.setValue('isolation_mode', value as 'shared' | 'dedicated')}
                      >
                        <Card className={`cursor-pointer transition-all ${
                          form.watch('isolation_mode') === 'shared' ? 'ring-2 ring-blue-500' : ''
                        }`}>
                          <label htmlFor="shared" className="cursor-pointer">
                            <CardHeader className="pb-3">
                              <div className="flex items-start gap-3">
                                <RadioGroupItem value="shared" id="shared" className="mt-1" />
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <Cloud className="h-4 w-4 text-blue-600" />
                                    <span className="font-medium">Shared Infrastructure</span>
                                    <Badge variant="secondary" className="text-xs">Recommended</Badge>
                                  </div>
                                  <p className="text-sm text-muted-foreground">
                                    Cost-effective solution with shared resources. Perfect for most organizations with standard security requirements.
                                  </p>
                                </div>
                              </div>
                            </CardHeader>
                          </label>
                        </Card>

                        <Card className={`cursor-pointer transition-all ${
                          form.watch('isolation_mode') === 'dedicated' ? 'ring-2 ring-blue-500' : ''
                        }`}>
                          <label htmlFor="dedicated" className="cursor-pointer">
                            <CardHeader className="pb-3">
                              <div className="flex items-start gap-3">
                                <RadioGroupItem value="dedicated" id="dedicated" className="mt-1" />
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <Server className="h-4 w-4 text-purple-600" />
                                    <span className="font-medium">Dedicated Resources</span>
                                    <Badge variant="outline" className="text-xs">Enterprise</Badge>
                                  </div>
                                  <p className="text-sm text-muted-foreground">
                                    Isolated infrastructure with enhanced security, guaranteed resources, and custom configurations.
                                  </p>
                                </div>
                              </div>
                            </CardHeader>
                          </label>
                        </Card>
                      </RadioGroup>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Hierarchy Tab */}
              <TabsContent value="hierarchy" className="mt-0 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Organization Hierarchy</CardTitle>
                    <CardDescription>
                      Define whether this is a root organization or a sub-organization
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <RadioGroup value={tenantType} onValueChange={(value) => setTenantType(value as 'root' | 'sub_tenant')}>
                      <Card className={`cursor-pointer transition-all ${
                        tenantType === 'root' ? 'ring-2 ring-blue-500' : ''
                      }`}>
                        <label htmlFor="root" className="cursor-pointer">
                          <CardHeader>
                            <div className="flex items-start gap-3">
                              <RadioGroupItem value="root" id="root" className="mt-1" />
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <Building2 className="h-5 w-5 text-blue-600" />
                                  <span className="font-medium text-lg">Root Organization</span>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                  A standalone, top-level organization that can have its own sub-organizations. 
                                  Root organizations have full autonomy and can manage their own hierarchy.
                                </p>
                              </div>
                            </div>
                          </CardHeader>
                        </label>
                      </Card>

                      <Card className={`cursor-pointer transition-all ${
                        tenantType === 'sub_tenant' ? 'ring-2 ring-blue-500' : ''
                      }`}>
                        <label htmlFor="sub_tenant" className="cursor-pointer">
                          <CardHeader>
                            <div className="flex items-start gap-3">
                              <RadioGroupItem value="sub_tenant" id="sub_tenant" className="mt-1" />
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <GitBranch className="h-5 w-5 text-green-600" />
                                  <span className="font-medium text-lg">Sub-Organization</span>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                  A child organization under a parent. Sub-organizations inherit certain settings 
                                  from their parent while maintaining their own users and configurations.
                                </p>
                              </div>
                            </div>
                          </CardHeader>
                        </label>
                      </Card>
                    </RadioGroup>

                    {tenantType === 'sub_tenant' && (
                      <div className="space-y-3 pt-4">
                        <Label htmlFor="parent">Select Parent Organization *</Label>
                        <Select value={selectedParent} onValueChange={setSelectedParent}>
                          <SelectTrigger id="parent" className="w-full">
                            <SelectValue placeholder="Choose a parent organization" />
                          </SelectTrigger>
                          <SelectContent>
                            {parentTenants?.items.map((tenant: Tenant) => (
                              <SelectItem key={tenant.id} value={tenant.id}>
                                <div className="flex items-center gap-2">
                                  <Building2 className="h-4 w-4" />
                                  <span>{tenant.name}</span>
                                  <span className="text-muted-foreground">({tenant.code})</span>
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {tenantType === 'sub_tenant' && !selectedParent && (
                          <p className="text-sm text-amber-600 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            Please select a parent organization
                          </p>
                        )}
                      </div>
                    )}

                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertTitle>About Organization Hierarchy</AlertTitle>
                      <AlertDescription className="mt-2 space-y-2">
                        <p>• Root organizations can have multiple sub-organizations</p>
                        <p>• Sub-organizations can inherit settings and terminology from their parent</p>
                        <p>• Users in a parent organization can be granted access to sub-organizations</p>
                        <p>• Each organization maintains its own user base and permissions</p>
                      </AlertDescription>
                    </Alert>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Features Tab */}
              <TabsContent value="features" className="mt-0 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Features & Capabilities</CardTitle>
                    <CardDescription>
                      Select the features you want to enable for this organization
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4">
                      {AVAILABLE_FEATURES.map((feature) => {
                        const Icon = FEATURE_ICONS[feature.value] || Shield;
                        const isChecked = form.watch('features').includes(feature.value);
                        
                        return (
                          <Card
                            key={feature.value}
                            className={`cursor-pointer transition-all ${
                              isChecked ? 'ring-2 ring-blue-500 bg-blue-50/50' : 'hover:bg-gray-50'
                            }`}
                            onClick={() => handleFeatureToggle(feature.value)}
                          >
                            <CardHeader className="pb-3">
                              <div className="flex items-start gap-3">
                                <Checkbox
                                  checked={isChecked}
                                  onCheckedChange={() => handleFeatureToggle(feature.value)}
                                  onClick={(e) => e.stopPropagation()}
                                  className="mt-1"
                                />
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <Icon className="h-4 w-4 text-blue-600" />
                                    <span className="font-medium">{feature.label}</span>
                                    {feature.value === 'api_access' && (
                                      <Badge variant="outline" className="text-xs">Essential</Badge>
                                    )}
                                  </div>
                                  <p className="text-sm text-muted-foreground">
                                    {FEATURE_DESCRIPTIONS[feature.value]}
                                  </p>
                                </div>
                              </div>
                            </CardHeader>
                          </Card>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Advanced Settings Tab */}
              <TabsContent value="settings" className="mt-0 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Additional Settings</CardTitle>
                    <CardDescription>
                      Configure advanced settings and metadata for this organization
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Settings2 className="h-5 w-5 text-gray-600" />
                        <div>
                          <p className="font-medium">Advanced Configuration</p>
                          <p className="text-sm text-muted-foreground">
                            Add custom settings and metadata
                          </p>
                        </div>
                      </div>
                      <Switch
                        checked={showAdvancedSettings}
                        onCheckedChange={setShowAdvancedSettings}
                      />
                    </div>

                    {showAdvancedSettings && (
                      <>
                        <Separator />
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-medium mb-3">Custom Settings</h4>
                            <div className="space-y-2">
                              {Object.entries(customSettings).map(([key, value]) => (
                                <div key={key} className="flex items-center gap-2 text-sm">
                                  <Badge variant="secondary">{key}</Badge>
                                  <span className="text-muted-foreground">{String(value)}</span>
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      const newSettings = { ...customSettings };
                                      delete newSettings[key];
                                      setCustomSettings(newSettings);
                                    }}
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                </div>
                              ))}
                              <div className="flex gap-2">
                                <Input
                                  id="setting-key"
                                  placeholder="Key"
                                  className="flex-1"
                                />
                                <Input
                                  id="setting-value"
                                  placeholder="Value"
                                  className="flex-1"
                                />
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    const key = (document.getElementById('setting-key') as HTMLInputElement)?.value;
                                    const value = (document.getElementById('setting-value') as HTMLInputElement)?.value;
                                    if (key && value) {
                                      addCustomSetting(key, value);
                                      (document.getElementById('setting-key') as HTMLInputElement).value = '';
                                      (document.getElementById('setting-value') as HTMLInputElement).value = '';
                                    }
                                  }}
                                >
                                  Add
                                </Button>
                              </div>
                            </div>
                          </div>

                          <Separator />

                          <div>
                            <h4 className="font-medium mb-3">Custom Metadata</h4>
                            <div className="space-y-2">
                              {Object.entries(customMetadata).map(([key, value]) => (
                                <div key={key} className="flex items-center gap-2 text-sm">
                                  <Badge variant="outline">{key}</Badge>
                                  <span className="text-muted-foreground">{String(value)}</span>
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      const newMetadata = { ...customMetadata };
                                      delete newMetadata[key];
                                      setCustomMetadata(newMetadata);
                                    }}
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                </div>
                              ))}
                              <div className="flex gap-2">
                                <Input
                                  id="metadata-key"
                                  placeholder="Key"
                                  className="flex-1"
                                />
                                <Input
                                  id="metadata-value"
                                  placeholder="Value"
                                  className="flex-1"
                                />
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    const key = (document.getElementById('metadata-key') as HTMLInputElement)?.value;
                                    const value = (document.getElementById('metadata-value') as HTMLInputElement)?.value;
                                    if (key && value) {
                                      addCustomMetadata(key, value);
                                      (document.getElementById('metadata-key') as HTMLInputElement).value = '';
                                      (document.getElementById('metadata-value') as HTMLInputElement).value = '';
                                    }
                                  }}
                                >
                                  Add
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </div>
          </Tabs>

          <DialogFooter className="px-8 py-4 border-t bg-gray-50">
            <div className="flex items-center justify-between w-full">
              <div className="text-sm text-muted-foreground">
                {!isFormValid() && (
                  <span className="flex items-center gap-1 text-amber-600">
                    <AlertCircle className="h-3 w-3" />
                    Please complete all required fields
                  </span>
                )}
              </div>
              <div className="flex gap-3">
                <Button type="button" variant="outline" onClick={handleClose}>
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  disabled={!isFormValid() || createMutation.isPending}
                  className="min-w-[120px]"
                >
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      Create Organization
                    </>
                  )}
                </Button>
              </div>
            </div>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}