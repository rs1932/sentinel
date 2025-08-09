'use client';

import { useState } from 'react';
import { useT, useTerminology } from '@/components/terminology';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Building2, Users, Shield, Package, Settings } from 'lucide-react';
import { useAuthStore } from '@/store/auth';

/**
 * TerminologyDemo Component
 * 
 * Demonstrates how terminology mapping transforms the UI based on tenant-specific
 * configuration. This shows the before/after effect of applying Maritime terminology
 * to standard Sentinel interface elements.
 */
export function TerminologyDemo() {
  const { user } = useAuthStore();
  const t = useT();
  const { terminology, loading, updateTerminology, resetTerminology } = useTerminology();
  const [isApplyingTerminology, setIsApplyingTerminology] = useState(false);

  // Maritime terminology example
  const maritimeTerminology = {
    tenant: 'Maritime Authority',
    tenants: 'Maritime Authorities',
    sub_tenant: 'Port Organization',
    sub_tenants: 'Port Organizations',
    user: 'Maritime Stakeholder',
    users: 'Maritime Stakeholders',
    role: 'Stakeholder Type',
    roles: 'Stakeholder Types',
    permission: 'Service Clearance',
    permissions: 'Service Clearances',
    resource: 'Maritime Service',
    resources: 'Maritime Services',
    group: 'Stakeholder Group',
    groups: 'Stakeholder Groups',
    tenant_management: 'Maritime Authority Management',
    user_management: 'Stakeholder Management',
    role_management: 'Stakeholder Type Management',
    create_tenant: 'Create Maritime Authority',
    create_user: 'Add Maritime Stakeholder',
    dashboard: 'Operations Center',
    settings: 'Maritime Configuration',
  };

  const handleApplyMaritimeTerminology = async () => {
    if (!user?.tenant_id) return;

    setIsApplyingTerminology(true);
    try {
      await updateTerminology(user.tenant_id, {
        terminology: maritimeTerminology,
        inherit_parent: false,
        apply_to_children: true,
      });
    } catch (error) {
      console.error('Failed to apply maritime terminology:', error);
    } finally {
      setIsApplyingTerminology(false);
    }
  };

  const handleResetTerminology = async () => {
    if (!user?.tenant_id) return;

    setIsApplyingTerminology(true);
    try {
      await resetTerminology(user.tenant_id);
    } catch (error) {
      console.error('Failed to reset terminology:', error);
    } finally {
      setIsApplyingTerminology(false);
    }
  };

  const menuItems = [
    { id: 'dashboard', icon: Settings, key: 'dashboard' },
    { id: 'tenants', icon: Building2, key: 'tenants' },
    { id: 'users', icon: Users, key: 'users' },
    { id: 'roles', icon: Shield, key: 'roles' },
    { id: 'resources', icon: Package, key: 'resources' },
  ];

  const isMaritimeActive = terminology.tenant === 'Maritime Authority';

  return (
    <div className="space-y-6 max-w-4xl mx-auto p-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Industry Terminology Mapping Demo
        </h1>
        <p className="text-gray-600">
          See how Sentinel adapts its interface terminology for different industries
        </p>
      </div>

      {/* Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Terminology Control Panel</CardTitle>
          <CardDescription>
            Apply Maritime industry terminology or reset to default Sentinel terms
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Current Mode:</p>
              <Badge variant={isMaritimeActive ? 'default' : 'secondary'}>
                {isMaritimeActive ? 'Maritime Industry' : 'Default Sentinel'}
              </Badge>
            </div>
            <div className="space-x-2">
              <Button
                onClick={handleApplyMaritimeTerminology}
                disabled={isApplyingTerminology || isMaritimeActive}
                variant="outline"
              >
                Apply Maritime Terminology
              </Button>
              <Button
                onClick={handleResetTerminology}
                disabled={isApplyingTerminology || !isMaritimeActive}
                variant="outline"
              >
                Reset to Default
              </Button>
            </div>
          </div>
          {loading && (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-sm text-gray-600 mt-2">Updating terminology...</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation Demo */}
      <Card>
        <CardHeader>
          <CardTitle>Navigation Menu Preview</CardTitle>
          <CardDescription>
            See how navigation labels change with terminology mapping
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.id}
                  className="flex flex-col items-center p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Icon className="h-8 w-8 text-blue-600 mb-2" />
                  <span className="text-sm font-medium text-center">
                    {t(item.key)}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Management Actions Demo */}
      <Card>
        <CardHeader>
          <CardTitle>Management Actions Preview</CardTitle>
          <CardDescription>
            Common management actions with terminology-aware labels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <span className="font-medium">{t('tenant_management')}</span>
              <Button size="sm" variant="outline">
                {t('create_tenant')}
              </Button>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <span className="font-medium">{t('user_management')}</span>
              <Button size="sm" variant="outline">
                {t('create_user')}
              </Button>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <span className="font-medium">{t('role_management')}</span>
              <Button size="sm" variant="outline">
                Create {t('role')}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Terminology Mapping Table */}
      <Card>
        <CardHeader>
          <CardTitle>Active Terminology Mappings</CardTitle>
          <CardDescription>
            Current terminology configuration for this tenant
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2 font-medium">Default Term</th>
                  <th className="text-left p-2 font-medium">Current Translation</th>
                  <th className="text-left p-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries({
                  tenant: 'Tenant',
                  tenants: 'Tenants',
                  user: 'User',
                  users: 'Users',
                  role: 'Role',
                  roles: 'Roles',
                  resource: 'Resource',
                  resources: 'Resources',
                }).map(([key, defaultValue]) => (
                  <tr key={key} className="border-b hover:bg-gray-50">
                    <td className="p-2 font-mono text-sm">{defaultValue}</td>
                    <td className="p-2 font-medium">{t(key)}</td>
                    <td className="p-2">
                      <Badge variant={t(key) !== defaultValue ? 'default' : 'secondary'}>
                        {t(key) !== defaultValue ? 'Customized' : 'Default'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Implementation Notes */}
      <Card>
        <CardHeader>
          <CardTitle>Implementation Details</CardTitle>
          <CardDescription>
            How the terminology system works under the hood
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-2">🔄 Dynamic Translation</h4>
              <p className="text-sm text-gray-600">
                Components use the useT() hook to translate terms in real-time.
                No hardcoded strings in the UI.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-2">🎯 Zero Breaking Changes</h4>
              <p className="text-sm text-gray-600">
                All existing APIs remain unchanged. Terminology is display-layer only.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-2">🏗️ Hierarchical Inheritance</h4>
              <p className="text-sm text-gray-600">
                Child tenants inherit terminology from parents. Can be overridden locally.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-2">⚡ Performance Optimized</h4>
              <p className="text-sm text-gray-600">
                In-memory caching with selective invalidation ensures fast responses.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default TerminologyDemo;