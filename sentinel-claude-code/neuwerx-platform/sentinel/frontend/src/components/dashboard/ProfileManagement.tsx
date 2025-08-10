'use client';

import { useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Camera, Save, Edit, Mail, Building2 } from 'lucide-react';

export function ProfileManagement() {
  const { user, userRole } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
  });

  const getUserInitials = (firstName?: string, lastName?: string) => {
    if (!firstName || !lastName) return 'U';
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  const getRoleDisplayName = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'Super Administrator';
      case 'tenant_admin':
        return 'Tenant Administrator';
      default:
        return 'User';
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'bg-red-100 text-red-800 hover:bg-red-100';
      case 'tenant_admin':
        return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
    }
  };

  const handleSave = () => {
    // TODO: Implement API call to update profile
    console.log('Saving profile:', formData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setFormData({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
    });
    setIsEditing(false);
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
          <p className="text-gray-600">
            Manage your account settings and personal information
          </p>
        </div>
      </div>

      {/* Profile card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Personal Information</CardTitle>
              <CardDescription>
                Update your personal details and account settings
              </CardDescription>
            </div>
            {!isEditing ? (
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit Profile
              </Button>
            ) : (
              <div className="flex space-x-2">
                <Button variant="outline" onClick={handleCancel}>
                  Cancel
                </Button>
                <Button onClick={handleSave}>
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Avatar section */}
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Avatar className="h-20 w-20">
                <AvatarImage 
                  src={user.avatar_url || `https://avatar.vercel.sh/${user.email}`} 
                  alt={`${user.first_name} ${user.last_name}`}
                />
                <AvatarFallback className="text-lg">
                  {getUserInitials(user.first_name, user.last_name)}
                </AvatarFallback>
              </Avatar>
              <Button
                size="sm"
                className="absolute -bottom-1 -right-1 rounded-full p-1 h-8 w-8"
                variant="secondary"
              >
                <Camera className="h-4 w-4" />
              </Button>
            </div>
            <div>
              <h3 className="text-lg font-medium">
                {user.first_name} {user.last_name}
              </h3>
              <p className="text-sm text-gray-500">{user.email}</p>
              <Badge 
                variant="secondary" 
                className={`mt-2 ${getRoleBadgeColor(userRole || 'user')}`}
              >
                {getRoleDisplayName(userRole || 'user')}
              </Badge>
            </div>
          </div>

          <Separator />

          {/* Form fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="first_name">First Name</Label>
              <Input
                id="first_name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                disabled={!isEditing}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="last_name">Last Name</Label>
              <Input
                id="last_name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                disabled={!isEditing}
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="email">Email Address</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={!isEditing}
                  className="pl-10"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Account details */}
      <Card>
        <CardHeader>
          <CardTitle>Account Details</CardTitle>
          <CardDescription>
            Information about your account and organization
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>Organization</Label>
              <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-md">
                <Building2 className="h-4 w-4 text-gray-500" />
                <span className="text-sm">{user.tenant?.display_name}</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Account Type</Label>
              <div className="p-3 bg-gray-50 rounded-md">
                <span className="text-sm capitalize">
                  {user.user_type?.replace('_', ' ') || 'Standard'}
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>User ID</Label>
              <div className="p-3 bg-gray-50 rounded-md">
                <span className="text-sm font-mono">{user.id}</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Status</Label>
              <div className="p-3 bg-gray-50 rounded-md">
                <Badge
                  variant={user.is_active ? "default" : "secondary"}
                  className={
                    user.is_active
                      ? "bg-green-100 text-green-800 hover:bg-green-100"
                      : "bg-red-100 text-red-800 hover:bg-red-100"
                  }
                >
                  {user.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Roles section */}
      <Card>
        <CardHeader>
          <CardTitle>Assigned Roles</CardTitle>
          <CardDescription>
            Your current roles and permissions within the organization
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {user.roles?.map((role) => (
              <div key={role.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h4 className="font-medium">{role.display_name}</h4>
                  <p className="text-sm text-gray-500">{role.description || 'No description available'}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">
                    {role.type === 'system' ? 'System Role' : 'Custom Role'}
                  </Badge>
                  <Badge variant="secondary">
                    Priority: {role.priority}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}