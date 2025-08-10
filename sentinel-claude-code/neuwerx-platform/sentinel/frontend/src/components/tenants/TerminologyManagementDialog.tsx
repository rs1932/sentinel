'use client';

import { useState, useEffect } from 'react';
import { useTerminology } from '@/hooks/useTerminology';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Save, RotateCcw, AlertCircle, CheckCircle, Wand2 } from 'lucide-react';
import type { Tenant } from '@/types';

interface TerminologyManagementDialogProps {
  isOpen: boolean;
  tenant: Tenant | null;
  onClose: () => void;
}

export function TerminologyManagementDialog({ 
  isOpen, 
  tenant, 
  onClose 
}: TerminologyManagementDialogProps) {
  const { 
    getTerminology, 
    updateTerminology, 
    resetTerminology,
    validateTerminology,
    getIndustryTemplates,
    applyTemplate,
    loading 
  } = useTerminology();
  
  const { toast } = useToast();
  const [terminologyConfig, setTerminologyConfig] = useState<any>(null);
  const [editedTerminology, setEditedTerminology] = useState<Record<string, string>>({});
  const [validation, setValidation] = useState<any>(null);
  const [industryTemplates, setIndustryTemplates] = useState<Record<string, Record<string, string>>>({});
  const [activeTab, setActiveTab] = useState('current');

  // Load terminology configuration when dialog opens
  useEffect(() => {
    if (isOpen && tenant) {
      loadTerminologyConfig();
      loadIndustryTemplates();
    }
  }, [isOpen, tenant]);

  const loadTerminologyConfig = async () => {
    if (!tenant) return;

    try {
      const config = await getTerminology(tenant.id);
      setTerminologyConfig(config);
      setEditedTerminology(config.local_config || {});
    } catch (error) {
      console.error('Failed to load terminology:', error);
      toast({
        title: 'Error',
        description: 'Failed to load terminology configuration',
        variant: 'destructive',
      });
    }
  };

  const loadIndustryTemplates = async () => {
    try {
      const templates = await getIndustryTemplates();
      setIndustryTemplates(templates);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleSave = async () => {
    if (!tenant) return;

    try {
      // Validate terminology first
      const validationResult = await validateTerminology(editedTerminology);
      setValidation(validationResult);

      if (!validationResult.valid) {
        toast({
          title: 'Validation Error',
          description: 'Please fix the validation errors before saving',
          variant: 'destructive',
        });
        return;
      }

      await updateTerminology(tenant.id, {
        terminology: editedTerminology,
        inherit_parent: false,
        apply_to_children: false,
      });

      toast({
        title: 'Success',
        description: 'Terminology updated successfully',
      });

      // Reload configuration
      await loadTerminologyConfig();
    } catch (error) {
      console.error('Failed to save terminology:', error);
      toast({
        title: 'Error',
        description: 'Failed to save terminology configuration',
        variant: 'destructive',
      });
    }
  };

  const handleReset = async () => {
    if (!tenant) return;

    if (!confirm('Are you sure you want to reset terminology to inherit from parent? This will remove all local customizations.')) {
      return;
    }

    try {
      await resetTerminology(tenant.id);
      
      toast({
        title: 'Success',
        description: 'Terminology reset successfully',
      });

      // Reload configuration
      await loadTerminologyConfig();
    } catch (error) {
      console.error('Failed to reset terminology:', error);
      toast({
        title: 'Error',
        description: 'Failed to reset terminology',
        variant: 'destructive',
      });
    }
  };

  const handleApplyTemplate = async (templateName: string) => {
    if (!tenant) return;

    try {
      await applyTemplate(tenant.id, templateName);
      
      toast({
        title: 'Success',
        description: `Applied ${templateName} industry template`,
      });

      // Reload configuration
      await loadTerminologyConfig();
      setActiveTab('current');
    } catch (error) {
      console.error('Failed to apply template:', error);
      toast({
        title: 'Error',
        description: 'Failed to apply industry template',
        variant: 'destructive',
      });
    }
  };

  const handleTerminologyChange = (key: string, value: string) => {
    setEditedTerminology(prev => ({
      ...prev,
      [key]: value
    }));
    // Clear validation when user makes changes
    setValidation(null);
  };

  const commonTerminologyKeys = [
    { key: 'tenant', label: 'Tenant', description: 'Main organization entity' },
    { key: 'tenants', label: 'Tenants', description: 'Plural form of tenant' },
    { key: 'sub_tenant', label: 'Sub-Tenant', description: 'Child organization' },
    { key: 'sub_tenants', label: 'Sub-Tenants', description: 'Plural form of sub-tenant' },
    { key: 'user', label: 'User', description: 'Individual person in system' },
    { key: 'users', label: 'Users', description: 'Plural form of user' },
    { key: 'role', label: 'Role', description: 'Access level or position' },
    { key: 'roles', label: 'Roles', description: 'Plural form of role' },
    { key: 'permission', label: 'Permission', description: 'Access right or capability' },
    { key: 'permissions', label: 'Permissions', description: 'Plural form of permission' },
    { key: 'resource', label: 'Resource', description: 'System resource or service' },
    { key: 'resources', label: 'Resources', description: 'Plural form of resource' },
    { key: 'group', label: 'Group', description: 'Collection of users' },
    { key: 'groups', label: 'Groups', description: 'Plural form of group' },
    { key: 'tenant_management', label: 'Tenant Management', description: 'Tenant administration page' },
    { key: 'user_management', label: 'User Management', description: 'User administration page' },
    { key: 'role_management', label: 'Role Management', description: 'Role administration page' },
    { key: 'create_tenant', label: 'Create Tenant', description: 'Create new tenant action' },
    { key: 'create_user', label: 'Create User', description: 'Create new user action' },
    { key: 'dashboard', label: 'Dashboard', description: 'Main overview page' },
    { key: 'settings', label: 'Settings', description: 'Configuration page' },
  ];

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Terminology Management - {tenant?.name}</DialogTitle>
          <DialogDescription>
            Customize how terms are displayed throughout the system for this tenant
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="current">Current Settings</TabsTrigger>
            <TabsTrigger value="edit">Edit Terminology</TabsTrigger>
            <TabsTrigger value="templates">Industry Templates</TabsTrigger>
          </TabsList>

          <TabsContent value="current" className="space-y-4">
            {terminologyConfig ? (
              <div className="space-y-4">
                {/* Status Overview */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Configuration Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span>Inheritance Status:</span>
                      <Badge variant={terminologyConfig.is_inherited ? 'secondary' : 'default'}>
                        {terminologyConfig.is_inherited ? 'Inherited from Parent' : 'Custom Configuration'}
                      </Badge>
                    </div>
                    {terminologyConfig.inherited_from && (
                      <div className="flex items-center justify-between">
                        <span>Inherited From:</span>
                        <span className="text-sm font-mono">{terminologyConfig.inherited_from}</span>
                      </div>
                    )}
                    {terminologyConfig.last_updated && (
                      <div className="flex items-center justify-between">
                        <span>Last Updated:</span>
                        <span className="text-sm">{new Date(terminologyConfig.last_updated).toLocaleString()}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Current Terminology */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Active Terminology</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(terminologyConfig.terminology).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="font-mono text-sm text-gray-600">{key}:</span>
                          <span className="font-medium">{value as string}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                Loading terminology configuration...
              </div>
            )}
          </TabsContent>

          <TabsContent value="edit" className="space-y-4">
            <div className="space-y-4">
              {/* Validation Results */}
              {validation && (
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-2 mb-2">
                      {validation.valid ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-600" />
                      )}
                      <span className={validation.valid ? 'text-green-600' : 'text-red-600'}>
                        {validation.valid ? 'Validation Passed' : 'Validation Failed'}
                      </span>
                    </div>
                    {validation.errors.length > 0 && (
                      <div className="space-y-1">
                        {validation.errors.map((error: string, idx: number) => (
                          <p key={idx} className="text-sm text-red-600">• {error}</p>
                        ))}
                      </div>
                    )}
                    {validation.warnings.length > 0 && (
                      <div className="space-y-1 mt-2">
                        {validation.warnings.map((warning: string, idx: number) => (
                          <p key={idx} className="text-sm text-yellow-600">⚠ {warning}</p>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Terminology Editor */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Edit Terminology</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {commonTerminologyKeys.map((item) => (
                      <div key={item.key} className="space-y-2">
                        <Label htmlFor={item.key}>
                          {item.label}
                          <span className="text-xs text-gray-500 ml-2">({item.description})</span>
                        </Label>
                        <Input
                          id={item.key}
                          value={editedTerminology[item.key] || terminologyConfig?.terminology[item.key] || ''}
                          onChange={(e) => handleTerminologyChange(item.key, e.target.value)}
                          placeholder={terminologyConfig?.terminology[item.key] || item.label}
                        />
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-between pt-4">
                    <Button variant="outline" onClick={handleReset} disabled={loading}>
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Reset to Default
                    </Button>
                    <Button onClick={handleSave} disabled={loading}>
                      {loading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Save className="h-4 w-4 mr-2" />
                      )}
                      Save Changes
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="templates" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Industry Templates</CardTitle>
                <DialogDescription>
                  Apply pre-configured terminology for specific industries
                </DialogDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(industryTemplates).map(([templateName, terminology]) => (
                  <Card key={templateName} className="border-2">
                    <CardHeader>
                      <CardTitle className="text-base capitalize">{templateName} Industry</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-2 text-sm mb-4">
                        {Object.entries(terminology).slice(0, 6).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="text-gray-600">{key}:</span>
                            <span className="font-medium">{value as string}</span>
                          </div>
                        ))}
                        {Object.entries(terminology).length > 6 && (
                          <div className="col-span-2 text-gray-500 text-xs">
                            ... and {Object.entries(terminology).length - 6} more terms
                          </div>
                        )}
                      </div>
                      <Button 
                        size="sm" 
                        onClick={() => handleApplyTemplate(templateName)}
                        disabled={loading}
                      >
                        <Wand2 className="h-4 w-4 mr-2" />
                        Apply Template
                      </Button>
                    </CardContent>
                  </Card>
                ))}
                
                {Object.keys(industryTemplates).length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No industry templates available
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

export default TerminologyManagementDialog;