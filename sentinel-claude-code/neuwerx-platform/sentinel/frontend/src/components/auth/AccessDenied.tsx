'use client';

import { AlertTriangle, Shield, LogOut, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/store/auth';
import { REQUIRED_ADMIN_SCOPES, getUserAdminScopes } from '@/lib/auth/adminCheck';

interface AccessDeniedProps {
  userScopes?: string[];
  userEmail?: string;
  tenantCode?: string;
}

export function AccessDenied({ userScopes = [], userEmail, tenantCode }: AccessDeniedProps) {
  const { logout } = useAuthStore();
  
  const userAdminScopes = getUserAdminScopes(userScopes);
  const hasAnyAdminScope = userAdminScopes.length > 0;

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
            <Shield className="h-6 w-6 text-red-600" />
          </div>
          <CardTitle className="text-2xl font-bold text-gray-900">Access Denied</CardTitle>
          <CardDescription>
            You do not have permission to access the Sentinel administrative interface
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* User Info */}
          {(userEmail || tenantCode) && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">Current User</h4>
              <div className="text-sm text-gray-600">
                {userEmail && <div>Email: {userEmail}</div>}
                {tenantCode && <div>Tenant: {tenantCode}</div>}
              </div>
            </div>
          )}

          {/* Required Permissions */}
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Administrative Access Required</strong>
              <br />
              Sentinel is an RBAC/Authentication management system. You need admin permissions to access this interface.
            </AlertDescription>
          </Alert>

          {/* Required Scopes */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Required Admin Permissions</h4>
            <div className="flex flex-wrap gap-2">
              {REQUIRED_ADMIN_SCOPES.map(scope => (
                <Badge 
                  key={scope} 
                  variant={userScopes.includes(scope) ? "default" : "secondary"}
                  className={userScopes.includes(scope) ? "bg-green-100 text-green-800" : ""}
                >
                  {scope}
                  {userScopes.includes(scope) && " ✓"}
                </Badge>
              ))}
            </div>
            <p className="text-xs text-gray-500">
              You need at least one of these permissions to access the system.
            </p>
          </div>

          {/* Current User Scopes */}
          {userScopes.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-gray-700">Your Current Permissions</h4>
              <div className="flex flex-wrap gap-2">
                {userScopes.map(scope => (
                  <Badge 
                    key={scope} 
                    variant="outline"
                    className={REQUIRED_ADMIN_SCOPES.includes(scope as any) ? "border-green-500 text-green-700" : ""}
                  >
                    {scope}
                  </Badge>
                ))}
              </div>
              {!hasAnyAdminScope && (
                <p className="text-xs text-red-600">
                  None of your current permissions provide admin access to Sentinel.
                </p>
              )}
            </div>
          )}

          {/* Contact Info */}
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              If you believe you should have access, please contact your administrator to request the appropriate admin permissions.
            </AlertDescription>
          </Alert>

          {/* Logout Button */}
          <div className="pt-4">
            <Button 
              onClick={handleLogout} 
              variant="outline" 
              className="w-full"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}