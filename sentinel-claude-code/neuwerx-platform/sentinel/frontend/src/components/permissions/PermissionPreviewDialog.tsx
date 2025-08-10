'use client';

import { Permission } from '@/types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Eye, Shield, Database, Globe, Layers, FileText, Settings, Zap, BarChart3 } from 'lucide-react';

interface PermissionPreviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  permission: Permission;
}

const RESOURCE_TYPE_INFO = {
  product_family: { label: 'Product Family', emoji: '📦', icon: FileText },
  app: { label: 'Application', emoji: '🎯', icon: Settings },
  capability: { label: 'Capability', emoji: '⚡', icon: Zap },
  service: { label: 'Service', emoji: '🔧', icon: BarChart3 },
  entity: { label: 'Entity', emoji: '📋', icon: Database },
  page: { label: 'Page', emoji: '📄', icon: Layers },
  api: { label: 'API', emoji: '🔌', icon: Globe },
};

const getActionColor = (action: string) => {
  switch (action) {
    case 'read': return 'bg-green-100 text-green-700';
    case 'write':
    case 'update': return 'bg-blue-100 text-blue-700';
    case 'create': return 'bg-purple-100 text-purple-700';
    case 'delete': return 'bg-red-100 text-red-700';
    case 'execute': return 'bg-orange-100 text-orange-700';
    case 'approve': return 'bg-emerald-100 text-emerald-700';
    case 'reject': return 'bg-rose-100 text-rose-700';
    default: return 'bg-gray-100 text-gray-700';
  }
};

export function PermissionPreviewDialog({ open, onOpenChange, permission }: PermissionPreviewDialogProps) {
  const typeInfo = RESOURCE_TYPE_INFO[permission.resource_type as keyof typeof RESOURCE_TYPE_INFO];
  const IconComponent = typeInfo?.icon || Shield;

  const getResourceScope = () => {
    if (permission.resource_id) {
      return {
        type: 'Specific Resource',
        description: 'Applies to one specific resource instance',
        value: `Resource ID: ${permission.resource_id}`,
        color: 'bg-blue-50 text-blue-700 border-blue-200'
      };
    } else if (permission.resource_path) {
      return {
        type: 'Path Pattern',
        description: 'Applies to resources matching the path pattern',
        value: permission.resource_path,
        color: 'bg-purple-50 text-purple-700 border-purple-200'
      };
    } else {
      return {
        type: 'Global',
        description: 'Applies to all resources of this type',
        value: 'All resources',
        color: 'bg-orange-50 text-orange-700 border-orange-200'
      };
    }
  };

  const resourceScope = getResourceScope();
  const hasConditions = permission.conditions && Object.keys(permission.conditions).length > 0;
  const hasFieldPermissions = permission.field_permissions && Object.keys(permission.field_permissions).length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Eye className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <DialogTitle>Permission Preview</DialogTitle>
              <DialogDescription>
                Detailed view of what this permission allows
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Permission Overview */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <span className="text-2xl">{typeInfo?.emoji}</span>
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {permission.name}
                    <Badge 
                      variant={permission.is_active ? "default" : "secondary"}
                      className={permission.is_active ? "bg-green-100 text-green-800" : ""}
                    >
                      {permission.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </CardTitle>
                  <div className="flex items-center gap-2 mt-1">
                    <IconComponent className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">{typeInfo?.label}</span>
                  </div>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Resource Scope */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Resource Scope</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`p-4 rounded-lg border ${resourceScope.color}`}>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-white bg-opacity-50 rounded-lg flex items-center justify-center">
                    <Database className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-medium">{resourceScope.type}</h4>
                    <p className="text-sm mt-1 opacity-90">{resourceScope.description}</p>
                    <div className="mt-2 font-mono text-sm bg-white bg-opacity-50 px-2 py-1 rounded">
                      {resourceScope.value}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Allowed Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {permission.actions.map((action, index) => (
                  <div key={index} className={`p-3 rounded-lg border ${getActionColor(action)}`}>
                    <div className="font-medium capitalize">{action}</div>
                    <div className="text-xs mt-1 opacity-80">
                      {action === 'read' && 'View and retrieve data'}
                      {action === 'write' && 'Modify existing data'}
                      {action === 'create' && 'Create new resources'}
                      {action === 'update' && 'Modify existing resources'}
                      {action === 'delete' && 'Remove resources'}
                      {action === 'execute' && 'Run operations or functions'}
                      {action === 'approve' && 'Approve requests or changes'}
                      {action === 'reject' && 'Reject requests or changes'}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Advanced Configuration */}
          {(hasConditions || hasFieldPermissions) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Advanced Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {hasConditions && (
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-2">Conditions</h4>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                        {JSON.stringify(permission.conditions, null, 2)}
                      </pre>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Additional conditions that must be met for this permission to apply
                    </p>
                  </div>
                )}

                {hasFieldPermissions && (
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-2">Field Permissions</h4>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                        {JSON.stringify(permission.field_permissions, null, 2)}
                      </pre>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Specific permissions for individual fields within resources
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Permission Meta Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Permission Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-500">Permission ID</div>
                  <div className="font-mono text-xs bg-gray-100 px-2 py-1 rounded mt-1">
                    {permission.id}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Tenant ID</div>
                  <div className="font-mono text-xs bg-gray-100 px-2 py-1 rounded mt-1">
                    {permission.tenant_id}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Created</div>
                  <div className="text-gray-700">
                    {permission.created_at ? new Date(permission.created_at).toLocaleString() : 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Last Updated</div>
                  <div className="text-gray-700">
                    {permission.updated_at ? new Date(permission.updated_at).toLocaleString() : 'N/A'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Summary */}
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-900">Permission Summary</h4>
                  <p className="text-sm text-blue-800 mt-1">
                    This permission allows <strong>{permission.actions.join(', ')}</strong> actions 
                    on <strong>{typeInfo?.label.toLowerCase()}</strong> resources 
                    with <strong>{resourceScope.type.toLowerCase()}</strong> scope.
                    {!permission.is_active && (
                      <span className="block mt-1 text-amber-700">
                        ⚠️ This permission is currently inactive and will not be enforced.
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}