'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/lib/api';
import { APP_NAME, ROUTES } from '@/constants';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Eye, EyeOff, Loader2, Lock, Mail, AlertCircle, CheckCircle, Wifi, WifiOff } from 'lucide-react';

const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();
  const { login, setLoading } = useAuthStore();

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setLoginError(null);
    setIsSubmitting(true);
    setLoading(true);

    try {
      // Call the actual backend API
      const response = await apiClient.auth.login({
        email: data.email,
        password: data.password,
      });

      console.log('Login response:', response); // Debug log

      // Extract tokens from response - backend format per actual API response
      const { 
        access_token, 
        refresh_token, 
        token_type, 
        expires_in,
        user_id,
        tenant_id,
        scope
      } = response;

      // Store tokens
      const tokens = {
        access_token,
        refresh_token,
        token_type,
        expires_in,
      };

      // Update API client with new token immediately
      apiClient.setToken(access_token);

      // Validate token to get user data
      const userResponse = await apiClient.auth.validate();

      console.log('User validation response:', userResponse); // Debug log

      // Create user object from validation response
      // Map scopes to roles - scopes are like ["user:read", "user:write", "tenant:admin"]
      const roles = (userResponse.scopes || []).map((scope: string, index: number) => ({
        id: `scope-${index}`,
        name: scope,
        display_name: scope.replace(':', ' ').replace('_', ' '),
        type: scope.includes('admin') ? 'system' as const : 'custom' as const,
        priority: scope.includes('admin') ? 100 : 50,
        tenant_id: userResponse.tenant_id,
        is_assignable: true,
      }));

      const user = {
        id: userResponse.user_id,
        email: userResponse.email || '',
        first_name: '',
        last_name: '',
        tenant_id: userResponse.tenant_id,
        user_type: userResponse.is_service_account ? 'service_account' as const : 'standard' as const,
        is_active: true,
        roles,
        tenant: {
          id: userResponse.tenant_id,
          name: userResponse.tenant_name || 'Unknown',
          display_name: userResponse.tenant_name || 'Unknown',
          type: 'root' as const,
          isolation_mode: 'shared' as const,
          features: [],
          settings: {},
          is_active: true,
        }
      };

      // Login user in store
      login(user, tokens);

      // Navigate to dashboard
      router.push(ROUTES.DASHBOARD);
    } catch (error: any) {
      console.error('Login error details:', error);
      console.error('Error type:', error?.errorType);
      console.error('Error message:', error?.message);
      console.error('Error status:', error?.status);
      
      // Handle different error types based on backend error format
      let errorMessage = 'An unexpected error occurred. Please try again.';
      
      // Handle specific error types from documented API format
      if (error?.errorType === 'authentication_failed' || error?.errorType === 'invalid_credentials') {
        errorMessage = 'Invalid email or password. Please check your credentials.';
      } else if (error?.errorType === 'account_locked') {
        const retryAfter = error?.retryAfter ? Math.ceil(error.retryAfter / 60) : 5;
        errorMessage = `Account locked due to too many failed attempts. Try again in ${retryAfter} minutes.`;
      } else if (error?.errorType === 'tenant_not_found') {
        errorMessage = 'Organization not found. Please check your organization code.';
      } else if (error?.errorType === 'rate_limit_exceeded') {
        const retryAfter = error?.retryAfter ? Math.ceil(error.retryAfter / 60) : 1;
        errorMessage = `Too many login attempts. Please wait ${retryAfter} minute(s) and try again.`;
      } else if (error?.message && error.message !== 'Unauthorized') {
        // Use backend message if it's not the generic "Unauthorized"
        errorMessage = error.message;
      } else if (error?.status === 401) {
        // Fallback for 401 errors without specific error type
        errorMessage = 'Invalid email or password. Please check your credentials.';
      } else if (error?.status === 403) {
        errorMessage = 'Your account has been suspended. Contact your administrator.';
      } else if (error?.status === 422) {
        errorMessage = 'Invalid request format. Please check your input.';
      } else if (error?.status === 429) {
        errorMessage = 'Too many login attempts. Please wait a moment and try again.';
      } else if (error?.status === 0 || error?.message?.includes('Network')) {
        errorMessage = 'Unable to connect to the server. Please check your internet connection.';
      }
      
      setLoginError(errorMessage);
    } finally {
      setIsSubmitting(false);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and branding */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg mb-4">
            <span className="text-white font-bold text-2xl">S</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{APP_NAME}</h1>
          <p className="text-gray-600">Multi-tenant User Management Platform</p>
        </div>

        <Card className="shadow-xl border-0 bg-white/80 backdrop-blur">
          <CardHeader className="space-y-1 pb-6">
            <CardTitle className="text-2xl font-semibold text-center text-gray-900">
              Sign in to your account
            </CardTitle>
            <CardDescription className="text-center text-gray-600">
              Enter your email and password to access your dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                {/* Email field */}
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-gray-700 font-medium">
                        Email Address
                      </FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                          <Input
                            type="email"
                            placeholder="Enter your email"
                            className="pl-10 h-12 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                            {...field}
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Password field */}
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-gray-700 font-medium">
                        Password
                      </FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                          <Input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Enter your password"
                            className="pl-10 pr-10 h-12 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
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
                              <EyeOff className="h-4 w-4 text-gray-400" />
                            ) : (
                              <Eye className="h-4 w-4 text-gray-400" />
                            )}
                          </Button>
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Error message */}
                {loginError && (
                  <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-red-800 mb-1">
                          Authentication Failed
                        </h4>
                        <p className="text-sm text-red-700">
                          {loginError}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Forgot password link */}
                <div className="flex justify-end">
                  <Button variant="link" className="px-0 text-blue-600 hover:text-blue-800">
                    Forgot your password?
                  </Button>
                </div>

                {/* Submit button */}
                <Button
                  type="submit"
                  className="w-full h-12 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={isSubmitting || form.formState.isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Authenticating...
                    </>
                  ) : (
                    <>
                      <Lock className="mr-2 h-4 w-4" />
                      Sign in
                    </>
                  )}
                </Button>
              </form>
            </Form>

            {/* Footer */}
            <div className="mt-6 text-center text-sm text-gray-600">
              <p>Need an account? Contact your administrator</p>
            </div>
          </CardContent>
        </Card>

        {/* Connection info */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <p className="text-sm text-gray-700">
              Connected to Sentinel Backend
            </p>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Use your assigned credentials to sign in
          </p>
        </div>
      </div>
    </div>
  );
}