'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  User as UserIcon,
  Mail, 
  Calendar, 
  MapPin, 
  Building, 
  Shield,
  Activity,
  Edit
} from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { apiClient } from '@/lib/api';

interface User {
  id: string;
  email: string;
  username?: string;
  attributes: {
    department?: string;
    location?: string;
    role?: string;
    [key: string]: any;
  };
  preferences: {
    theme?: string;
    language?: string;
    notifications?: boolean;
  };
  is_active: boolean;
  last_login?: string;
  login_count: number;
  failed_login_count?: number;
  locked_until?: string;
  created_at: string;
  updated_at: string;
}

interface UserDetailDialogProps {
  user: User;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UserDetailDialog({ user, open, onOpenChange }: UserDetailDialogProps) {
  const [userDetails, setUserDetails] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && user) {
      loadUserDetails();
    }
  }, [open, user?.id]);

  const loadUserDetails = async () => {
    try {
      setLoading(true);
      const details = await apiClient.users.get(user.id);
      setUserDetails(details);
    } catch (error) {
      console.error('Failed to load user details:', error);
      setUserDetails(user); // Fallback to basic user data
    } finally {
      setLoading(false);
    }
  };

  const getInitials = (email: string, username?: string) => {
    const name = username || email;
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const currentUser = userDetails || user;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <UserIcon className="h-5 w-5" />
            <span>User Details</span>
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* User Header */}
            <div className="flex items-start space-x-4">
              <Avatar className="h-16 w-16">
                <AvatarImage src={`/api/v1/users/${currentUser.id}/avatar`} />
                <AvatarFallback className="text-lg">
                  {getInitials(currentUser.email, currentUser.username)}
                </AvatarFallback>
              </Avatar>
              
              <div className="flex-1 space-y-2">
                <div>
                  <h3 className="text-xl font-semibold">
                    {currentUser.username || currentUser.email}
                  </h3>
                  {currentUser.username && (
                    <p className="text-sm text-muted-foreground">{currentUser.email}</p>
                  )}
                </div>
                
                <div className="flex items-center space-x-2">
                  <Badge 
                    variant={currentUser.is_active ? 'default' : 'secondary'}
                    className={currentUser.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}
                  >
                    {currentUser.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  
                  {currentUser.locked_until && new Date(currentUser.locked_until) > new Date() && (
                    <Badge variant="destructive">
                      Locked until {formatDate(currentUser.locked_until)}
                    </Badge>
                  )}
                </div>
              </div>

              <Button variant="outline" size="sm">
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
            </div>

            <Separator />

            {/* Basic Information */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium flex items-center space-x-2">
                <Mail className="h-4 w-4" />
                <span>Contact Information</span>
              </h4>
              
              <div className="grid grid-cols-1 gap-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Email</span>
                  <span>{currentUser.email}</span>
                </div>
                {currentUser.username && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Username</span>
                    <span>{currentUser.username}</span>
                  </div>
                )}
              </div>
            </div>

            <Separator />

            {/* Attributes */}
            {Object.keys(currentUser.attributes || {}).length > 0 && (
              <>
                <div className="space-y-4">
                  <h4 className="text-sm font-medium flex items-center space-x-2">
                    <Building className="h-4 w-4" />
                    <span>Attributes</span>
                  </h4>
                  
                  <div className="grid grid-cols-1 gap-3 text-sm">
                    {currentUser.attributes.department && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Department</span>
                        <span>{currentUser.attributes.department}</span>
                      </div>
                    )}
                    {currentUser.attributes.location && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Location</span>
                        <span>{currentUser.attributes.location}</span>
                      </div>
                    )}
                    {currentUser.attributes.role && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Role/Title</span>
                        <span>{currentUser.attributes.role}</span>
                      </div>
                    )}
                    {Object.entries(currentUser.attributes).filter(([key]) => 
                      !['department', 'location', 'role'].includes(key)
                    ).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between">
                        <span className="text-muted-foreground capitalize">
                          {key.replace(/[_-]/g, ' ')}
                        </span>
                        <span>{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Preferences */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium flex items-center space-x-2">
                <Shield className="h-4 w-4" />
                <span>Preferences</span>
              </h4>
              
              <div className="grid grid-cols-1 gap-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Theme</span>
                  <span className="capitalize">{currentUser.preferences?.theme || 'System'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Language</span>
                  <span className="uppercase">{currentUser.preferences?.language || 'EN'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Notifications</span>
                  <Badge variant={currentUser.preferences?.notifications ? 'default' : 'secondary'}>
                    {currentUser.preferences?.notifications ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>
              </div>
            </div>

            <Separator />

            {/* Activity Stats */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium flex items-center space-x-2">
                <Activity className="h-4 w-4" />
                <span>Activity</span>
              </h4>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <p className="text-muted-foreground">Total Logins</p>
                  <p className="text-2xl font-semibold">{currentUser.login_count.toLocaleString()}</p>
                </div>
                {currentUser.failed_login_count !== undefined && (
                  <div className="space-y-1">
                    <p className="text-muted-foreground">Failed Logins</p>
                    <p className="text-2xl font-semibold text-red-600">{currentUser.failed_login_count}</p>
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-1 gap-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Last Login</span>
                  <span>{formatDate(currentUser.last_login)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Created</span>
                  <span>{formatDate(currentUser.created_at)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Last Updated</span>
                  <span>{formatDate(currentUser.updated_at)}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}