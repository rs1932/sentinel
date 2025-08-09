'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import * as z from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  Loader2, 
  Mail, 
  Send, 
  User, 
  Building2, 
  Settings2, 
  Info,
  AlertCircle,
  Eye,
  EyeOff,
  UserPlus,
  Check,
  Key,
  Shield,
  Bell
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Tenant } from '@/types';

const createUserSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  username: z
    .string()
    .optional()
    .refine(val => !val || val.length >= 3, {
      message: 'Username must be at least 3 characters if provided'
    }),
  password: z
    .string()
    .optional(),
  tenant_id: z.string().optional(),
  attributes: z.object({
    department: z.string().optional(),
    location: z.string().optional(),
    role: z.string().optional(),
  }),
  preferences: z.object({
    theme: z.enum(['light', 'dark', 'system']).default('system'),
    language: z.enum(['en', 'es', 'fr']).default('en'),
    notifications: z.boolean().default(true),
  }),
  is_active: z.boolean().default(true),
  send_invitation: z.boolean().default(false),
}).refine(data => data.send_invitation || (data.password && data.password.length >= 8), {
  message: 'Password must be at least 8 characters if not sending invitation',
  path: ['password']
});

type CreateUserFormData = z.infer<typeof createUserSchema>;

interface CreateUserDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function CreateUserDialog({ open, onOpenChange, onSuccess }: CreateUserDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('basic');
  const [showPassword, setShowPassword] = useState(false);
  const [showAdvancedPreferences, setShowAdvancedPreferences] = useState(false);

  // Fetch available tenants for user assignment
  const { data: tenants } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => apiClient.tenants.list({ limit: 100 }),
    enabled: open,
  });

  const form = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      email: '',
      username: '',
      password: '',
      tenant_id: '',
      attributes: {
        department: '',
        location: '',
        role: '',
      },
      preferences: {
        theme: 'system',
        language: 'en',
        notifications: true,
      },
      is_active: true,
      send_invitation: false,
    },
  });

  const sendInvitation = form.watch('send_invitation');

  const onSubmit = async (data: CreateUserFormData) => {
    try {
      setLoading(true);
      setError(null);

      // Prepare the data according to API format
      const userData = {
        email: data.email,
        ...(data.username && { username: data.username }),
        ...(!data.send_invitation && data.password && { password: data.password }),
        ...(data.tenant_id && { tenant_id: data.tenant_id }),
        attributes: Object.fromEntries(
          Object.entries(data.attributes).filter(([_, value]) => value)
        ),
        preferences: data.preferences,
        is_active: data.is_active,
        send_invitation: data.send_invitation,
      };

      const response = await apiClient.users.create(userData);
      console.log('User created:', response);
      
      onSuccess?.();
      form.reset();
      onOpenChange(false);
    } catch (err: any) {
      console.error('Create user error:', err);
      setError(err.message || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    form.reset();
    setError(null);
    setActiveTab('basic');
    setShowPassword(false);
    setShowAdvancedPreferences(false);
    onOpenChange(false);
  };

  const isFormValid = () => {
    const values = form.getValues();
    if (!values.email) return false;
    if (!values.send_invitation && (!values.password || values.password.length < 8)) return false;
    return true;
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-6xl h-[85vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <DialogTitle className="text-xl font-semibold flex items-center gap-2">
            <UserPlus className="h-5 w-5 text-blue-600" />
            Create New User
          </DialogTitle>
          <DialogDescription>
            Add a new user to your organization. They will receive access based on their assigned roles and permissions.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="flex-1 overflow-hidden flex flex-col">
            {error && (
              <div className="px-6 pt-2">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              </div>
            )}

            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
              <TabsList className="grid w-full grid-cols-4 mx-8 mt-4 h-12" style={{ width: 'calc(100% - 4rem)' }}>
                <TabsTrigger value="basic" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  <span className="hidden sm:inline">Basic Info</span>
                  <span className="sm:hidden">Basic</span>
                </TabsTrigger>
                <TabsTrigger value="access" className="flex items-center gap-2">
                  <Key className="h-4 w-4" />
                  <span className="hidden sm:inline">Access & Security</span>
                  <span className="sm:hidden">Access</span>
                </TabsTrigger>
                <TabsTrigger value="organization" className="flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  <span className="hidden sm:inline">Organization</span>
                  <span className="sm:hidden">Org</span>
                </TabsTrigger>
                <TabsTrigger value="preferences" className="flex items-center gap-2">
                  <Settings2 className="h-4 w-4" />
                  Preferences
                </TabsTrigger>
              </TabsList>

              <div className="flex-1 overflow-y-auto px-8 py-6">
                {/* Basic Information Tab */}
                <TabsContent value="basic" className="mt-0 space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>User Details</CardTitle>
                      <CardDescription>
                        Enter the essential information for the new user account
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <FormField
                        control={form.control}
                        name="email"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Email Address *</FormLabel>
                            <FormControl>
                              <Input
                                type="email"
                                placeholder="user@example.com"
                                className="text-base"
                                {...field}
                              />
                            </FormControl>
                            <FormDescription>
                              This will be the user's login email and primary contact
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="username"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Display Name</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="john_doe (optional)"
                                className="text-base"
                                {...field}
                              />
                            </FormControl>
                            <FormDescription>
                              Optional display name that will appear in the interface
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <Separator />

                      <FormField
                        control={form.control}
                        name="is_active"
                        render={({ field }) => (
                          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                            <div className="space-y-0.5">
                              <FormLabel className="text-base">
                                Active User Account
                              </FormLabel>
                              <FormDescription>
                                User can sign in and access the system immediately
                              </FormDescription>
                            </div>
                            <FormControl>
                              <Switch
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Access & Security Tab */}
                <TabsContent value="access" className="mt-0 space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Authentication Method</CardTitle>
                      <CardDescription>
                        Choose how the user will set up their initial access
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <FormField
                        control={form.control}
                        name="send_invitation"
                        render={({ field }) => (
                          <div className="grid gap-4">
                            <Card className={`cursor-pointer transition-all ${
                              field.value ? 'ring-2 ring-blue-500 bg-blue-50/50' : 'hover:bg-gray-50'
                            }`} onClick={() => field.onChange(true)}>
                              <CardHeader className="pb-3">
                                <div className="flex items-start gap-3">
                                  <Checkbox
                                    checked={field.value}
                                    onCheckedChange={(checked) => field.onChange(checked)}
                                    onClick={(e) => e.stopPropagation()}
                                    className="mt-1"
                                  />
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                      <Mail className="h-4 w-4 text-blue-600" />
                                      <span className="font-medium">Send Invitation Email</span>
                                      <Badge variant="secondary" className="text-xs">Recommended</Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                      User receives a secure email invitation to set their own password. More secure and user-friendly.
                                    </p>
                                  </div>
                                </div>
                              </CardHeader>
                            </Card>

                            <Card className={`cursor-pointer transition-all ${
                              !field.value ? 'ring-2 ring-blue-500 bg-blue-50/50' : 'hover:bg-gray-50'
                            }`} onClick={() => field.onChange(false)}>
                              <CardHeader className="pb-3">
                                <div className="flex items-start gap-3">
                                  <Checkbox
                                    checked={!field.value}
                                    onCheckedChange={(checked) => field.onChange(!checked)}
                                    onClick={(e) => e.stopPropagation()}
                                    className="mt-1"
                                  />
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                      <Key className="h-4 w-4 text-purple-600" />
                                      <span className="font-medium">Set Password Now</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                      Create a password for the user immediately. You'll need to share it with them securely.
                                    </p>
                                  </div>
                                </div>
                              </CardHeader>
                            </Card>
                          </div>
                        )}
                      />

                      {!sendInvitation && (
                        <div className="space-y-4 pt-4">
                          <Separator />
                          <FormField
                            control={form.control}
                            name="password"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Password *</FormLabel>
                                <FormControl>
                                  <div className="relative">
                                    <Input
                                      type={showPassword ? "text" : "password"}
                                      placeholder="Minimum 8 characters"
                                      className="text-base pr-10"
                                      {...field}
                                    />
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      size="sm"
                                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                                      onClick={() => setShowPassword(!showPassword)}
                                    >
                                      {showPassword ? (
                                        <EyeOff className="h-4 w-4" />
                                      ) : (
                                        <Eye className="h-4 w-4" />
                                      )}
                                    </Button>
                                  </div>
                                </FormControl>
                                <FormDescription>
                                  Password must be at least 8 characters long and contain a mix of letters, numbers, and symbols
                                </FormDescription>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Organization Tab */}
                <TabsContent value="organization" className="mt-0 space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Organization Assignment</CardTitle>
                      <CardDescription>
                        Assign the user to a specific organization and department
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <FormField
                        control={form.control}
                        name="tenant_id"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Organization</FormLabel>
                            <Select onValueChange={field.onChange} value={field.value}>
                              <FormControl>
                                <SelectTrigger className="text-base">
                                  <SelectValue placeholder="Select an organization" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                {tenants?.items.map((tenant: Tenant) => (
                                  <SelectItem key={tenant.id} value={tenant.id}>
                                    <div className="flex items-center gap-2">
                                      <Building2 className="h-4 w-4" />
                                      <span>{tenant.name}</span>
                                      <Badge variant="outline" className="text-xs">{tenant.code}</Badge>
                                    </div>
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <FormDescription>
                              The organization this user will belong to and have access to
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <Separator />

                      <div className="space-y-4">
                        <h4 className="font-medium">Department & Role Information</h4>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="attributes.department"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Department</FormLabel>
                                <FormControl>
                                  <Input 
                                    placeholder="e.g., Engineering" 
                                    className="text-base"
                                    {...field} 
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name="attributes.location"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Location</FormLabel>
                                <FormControl>
                                  <Input 
                                    placeholder="e.g., San Francisco" 
                                    className="text-base"
                                    {...field} 
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>

                        <FormField
                          control={form.control}
                          name="attributes.role"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Job Title</FormLabel>
                              <FormControl>
                                <Input 
                                  placeholder="e.g., Senior Software Engineer" 
                                  className="text-base"
                                  {...field} 
                                />
                              </FormControl>
                              <FormDescription>
                                The user's role or position within the organization
                              </FormDescription>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Preferences Tab */}
                <TabsContent value="preferences" className="mt-0 space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Default Preferences</CardTitle>
                      <CardDescription>
                        Set the user's initial preferences. They can change these later in their profile.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="grid grid-cols-2 gap-4">
                        <FormField
                          control={form.control}
                          name="preferences.theme"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Theme Preference</FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="text-base">
                                    <SelectValue />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  <SelectItem value="light">Light Mode</SelectItem>
                                  <SelectItem value="dark">Dark Mode</SelectItem>
                                  <SelectItem value="system">System Default</SelectItem>
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="preferences.language"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Language</FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="text-base">
                                    <SelectValue />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  <SelectItem value="en">English</SelectItem>
                                  <SelectItem value="es">Spanish</SelectItem>
                                  <SelectItem value="fr">French</SelectItem>
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>

                      <Separator />

                      <FormField
                        control={form.control}
                        name="preferences.notifications"
                        render={({ field }) => (
                          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                            <div className="space-y-0.5">
                              <FormLabel className="text-base">
                                Email Notifications
                              </FormLabel>
                              <FormDescription>
                                User will receive email notifications for important updates and system events
                              </FormDescription>
                            </div>
                            <FormControl>
                              <Switch
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />

                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertTitle>About User Preferences</AlertTitle>
                        <AlertDescription className="mt-2 space-y-2">
                          <p>• Users can modify these settings anytime from their profile</p>
                          <p>• Language settings affect the interface display language</p>
                          <p>• Theme preferences are applied immediately upon first login</p>
                          <p>• Notification settings control email frequency and types</p>
                        </AlertDescription>
                      </Alert>
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
                    disabled={!isFormValid() || loading}
                    className="min-w-[140px]"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : sendInvitation ? (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        Send Invitation
                      </>
                    ) : (
                      <>
                        <Check className="mr-2 h-4 w-4" />
                        Create User
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}