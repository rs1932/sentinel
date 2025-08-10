'use client';

import { useState } from 'react';
import { useAuthStore } from '@/store/auth';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Copy, Check, Bug } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DebugDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DebugDialog({ open, onOpenChange }: DebugDialogProps) {
  const { user, tokens, userRole, isAuthenticated, tokenExpiresAt } = useAuthStore();
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

  const copyToClipboard = async (text: string, itemName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedItem(itemName);
      setTimeout(() => setCopiedItem(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const formatJson = (obj: any) => {
    return JSON.stringify(obj, null, 2);
  };

  const getTokenExpiry = () => {
    if (!tokenExpiresAt) return 'N/A';
    const expiry = new Date(tokenExpiresAt);
    const now = new Date();
    const diff = expiry.getTime() - now.getTime();
    
    if (diff < 0) return 'EXPIRED';
    
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  const parseJwtPayload = (token: string) => {
    try {
      if (!token || token.split('.').length !== 3) {
        return { error: 'Invalid JWT format' };
      }
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(jsonPayload);
    } catch (error) {
      return { error: 'Failed to parse JWT', details: error instanceof Error ? error.message : 'Unknown error' };
    }
  };

  const jwtPayload = tokens?.access_token ? parseJwtPayload(tokens.access_token) : null;
  const scopes = jwtPayload?.scope ? jwtPayload.scope.split(' ') : [];
  
  // Debug log to help troubleshoot
  console.log('Debug Dialog - JWT Payload:', jwtPayload);
  console.log('Debug Dialog - Scopes:', scopes);

  const CopyButton = ({ text, itemName }: { text: string; itemName: string }) => (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => copyToClipboard(text, itemName)}
      className="h-6 w-6 p-0"
    >
      {copiedItem === itemName ? (
        <Check className="h-3 w-3 text-green-500" />
      ) : (
        <Copy className="h-3 w-3" />
      )}
    </Button>
  );

  const JsonBlock = ({ title, data, itemName }: { title: string; data: any; itemName: string }) => (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">{title}</h4>
        <CopyButton text={formatJson(data)} itemName={itemName} />
      </div>
      <div className="h-48 rounded-md border">
        <ScrollArea className="h-full p-3">
          <pre className="text-xs font-mono whitespace-pre-wrap">
            {formatJson(data)}
          </pre>
        </ScrollArea>
      </div>
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl w-[90vw] max-h-[85vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bug className="h-5 w-5" />
            Debug Information
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col h-[75vh]">
          <Tabs defaultValue="auth" className="flex-1 flex flex-col">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="auth">Authentication</TabsTrigger>
              <TabsTrigger value="user">User Data</TabsTrigger>
              <TabsTrigger value="tokens">Tokens</TabsTrigger>
              <TabsTrigger value="system">System</TabsTrigger>
            </TabsList>

            <div className="flex-1 mt-4 overflow-hidden">
            <TabsContent value="auth" className="flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                <div className="space-y-4 p-1">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">Authentication Status</h4>
                      <Badge variant={isAuthenticated ? "default" : "destructive"}>
                        {isAuthenticated ? "Authenticated" : "Not Authenticated"}
                      </Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">User Role</h4>
                      <Badge variant="secondary">{userRole || 'N/A'}</Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">Token Expires In</h4>
                      <Badge variant="outline">{getTokenExpiry()}</Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">Total Scopes</h4>
                      <Badge variant="outline">{scopes.length}</Badge>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Scopes</h4>
                    <div className="flex flex-wrap gap-1 p-3 border rounded-md min-h-[100px]">
                      {scopes.length > 0 ? scopes.map((scope, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {scope}
                        </Badge>
                      )) : (
                        <span className="text-sm text-muted-foreground">No scopes available</span>
                      )}
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="user" className="flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                <div className="space-y-4 p-1">
                  <JsonBlock title="User Object" data={user || {}} itemName="user" />
                  
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Tenant Information</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="font-medium">Tenant ID:</span>
                        <div className="flex items-center gap-2 mt-1">
                          <code className="bg-gray-100 px-2 py-1 rounded text-xs break-all">
                            {user?.tenant_id || 'N/A'}
                          </code>
                          {user?.tenant_id && (
                            <CopyButton text={user.tenant_id} itemName="tenant-id" />
                          )}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">Tenant Code:</span>
                        <div className="mt-1">
                          <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                            {user?.tenant?.code || 'N/A'}
                          </code>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="tokens" className="flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                <div className="space-y-4 p-1">
                  <JsonBlock title="Tokens Object" data={tokens || {}} itemName="tokens" />
                  
                  {jwtPayload && (
                    <JsonBlock title="JWT Payload" data={jwtPayload} itemName="jwt-payload" />
                  )}
                  
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Token Information</h4>
                    <div className="grid grid-cols-1 gap-2 text-sm">
                      <div>
                        <span className="font-medium">Access Token (first 50 chars):</span>
                        <div className="flex items-center gap-2 mt-1">
                          <code className="bg-gray-100 px-2 py-1 rounded text-xs break-all">
                            {tokens?.access_token?.substring(0, 50)}...
                          </code>
                          {tokens?.access_token && (
                            <CopyButton text={tokens.access_token} itemName="access-token" />
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="system" className="flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                <div className="space-y-4 p-1">
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Environment</h4>
                    <div className="grid grid-cols-1 gap-2 text-sm">
                      <div>
                        <span className="font-medium">URL:</span>
                        <div className="mt-1">
                          <code className="bg-gray-100 px-2 py-1 rounded text-xs break-all">
                            {window.location.origin}
                          </code>
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">User Agent:</span>
                        <div className="mt-1">
                          <code className="bg-gray-100 px-2 py-1 rounded text-xs break-all">
                            {navigator.userAgent.substring(0, 100)}...
                          </code>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Local Storage Keys</h4>
                    <div className="p-3 border rounded-md space-y-2">
                      {Object.keys(localStorage).map((key) => (
                        <div key={key} className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">{key}</Badge>
                          <CopyButton text={localStorage.getItem(key) || ''} itemName={`localStorage-${key}`} />
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Timestamp</h4>
                    <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                      {new Date().toISOString()}
                    </code>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>
            </div>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
}