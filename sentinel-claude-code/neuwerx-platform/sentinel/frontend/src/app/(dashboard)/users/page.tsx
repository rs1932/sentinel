'use client';

import { useState } from 'react';
import { Plus, Users, Key, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { UserList } from '@/components/users/UserList';
import { CreateUserDialog } from '@/components/users/CreateUserDialog';
import { ServiceAccountList } from '@/components/users/ServiceAccountList';
import { CreateServiceAccountDialog } from '@/components/users/CreateServiceAccountDialog';
import { BulkOperationsProvider } from '@/components/users/BulkOperationsProvider';

export default function UsersPage() {
  const [activeTab, setActiveTab] = useState('users');
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showCreateServiceAccount, setShowCreateServiceAccount] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [userCount, setUserCount] = useState(0);
  const [serviceAccountCount, setServiceAccountCount] = useState(0);

  const handleRefreshUsers = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleUserCountUpdate = (count: number) => {
    setUserCount(count);
  };

  const handleServiceAccountCountUpdate = (count: number) => {
    setServiceAccountCount(count);
  };

  // Tab configurations with metadata
  const tabConfigs = {
    users: {
      id: 'users',
      label: 'Users',
      icon: Users,
      count: userCount,
      description: 'Manage system users, their profiles, and access permissions',
      buttonText: 'Add User',
      buttonAction: () => setShowCreateUser(true)
    },
    'service-accounts': {
      id: 'service-accounts',
      label: 'Service Accounts',
      icon: Key,
      count: serviceAccountCount,
      description: 'Manage API service accounts for automated integrations',
      buttonText: 'New Service Account',
      buttonAction: () => setShowCreateServiceAccount(true)
    }
  };

  const currentTab = tabConfigs[activeTab as keyof typeof tabConfigs];

  return (
    <BulkOperationsProvider onRefresh={handleRefreshUsers}>
      <div className="space-y-8">
        {/* Enhanced Header */}
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <ShieldCheck className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">User Management</h1>
              <p className="text-muted-foreground">
                Comprehensive user and access management for your organization
              </p>
            </div>
          </div>
        </div>

        {/* Enhanced Tabbed Interface */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Tab Header with Action Button */}
          <div className="flex flex-col space-y-4 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
            <div className="space-y-2">
              <TabsList className="grid w-full grid-cols-2 lg:w-fit bg-muted p-1 rounded-lg h-auto">
                {Object.values(tabConfigs).map((config) => {
                  const Icon = config.icon;
                  return (
                    <TabsTrigger 
                      key={config.id}
                      value={config.id}
                      className="flex items-center justify-center space-x-2 px-4 py-3 data-[state=active]:bg-background data-[state=active]:shadow-sm rounded-md transition-all"
                    >
                      <Icon className="h-4 w-4 flex-shrink-0" />
                      <span className="text-sm font-medium">{config.label}</span>
                      {config.count > 0 && (
                        <Badge 
                          variant="secondary" 
                          className="ml-1 text-xs min-w-[1.25rem] h-5 flex items-center justify-center bg-background/80 text-foreground border"
                        >
                          {config.count}
                        </Badge>
                      )}
                    </TabsTrigger>
                  );
                })}
              </TabsList>
              
              {/* Contextual Description */}
              <p className="text-sm text-muted-foreground leading-relaxed lg:max-w-md">
                {currentTab?.description}
              </p>
            </div>

            {/* Contextual Action Button */}
            <Button 
              onClick={currentTab?.buttonAction}
              size="lg"
              className="flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl transition-all duration-200 bg-primary hover:bg-primary/90 w-full lg:w-auto"
            >
              <Plus className="h-4 w-4 flex-shrink-0" />
              <span className="font-medium">{currentTab?.buttonText}</span>
            </Button>
          </div>

          {/* Tab Content with Enhanced Cards */}
          <div className="space-y-6">
            <TabsContent value="users" className="space-y-0">
              <Card className="border-0 shadow-sm bg-card/50">
                <CardContent className="p-6">
                  <UserList 
                    key={refreshTrigger} 
                    onCountUpdate={handleUserCountUpdate}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="service-accounts" className="space-y-0">
              <Card className="border-0 shadow-sm bg-card/50">
                <CardContent className="p-6">
                  <ServiceAccountList 
                    onCreateNew={() => setShowCreateServiceAccount(true)}
                    onCountUpdate={handleServiceAccountCountUpdate}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </div>
        </Tabs>

        {/* Dialogs */}
        <CreateUserDialog 
          open={showCreateUser} 
          onOpenChange={setShowCreateUser}
          onSuccess={() => {
            handleRefreshUsers();
          }}
        />

        <CreateServiceAccountDialog
          open={showCreateServiceAccount}
          onOpenChange={setShowCreateServiceAccount}
          onSuccess={() => {
            // Trigger refresh of service account list
            setRefreshTrigger(prev => prev + 1);
          }}
        />
      </div>
    </BulkOperationsProvider>
  );
}