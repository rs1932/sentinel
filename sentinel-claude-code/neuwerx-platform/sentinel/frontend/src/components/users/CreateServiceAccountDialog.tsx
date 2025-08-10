'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
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
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Loader2, 
  Key, 
  CheckCircle, 
  Copy, 
  Eye, 
  EyeOff,
  AlertTriangle 
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

const createServiceAccountSchema = z.object({
  name: z
    .string()
    .min(3, 'Name must be at least 3 characters')
    .max(255, 'Name must be less than 255 characters'),
  description: z
    .string()
    .optional(),
  attributes: z.object({
    purpose: z.string().optional(),
    environment: z.string().optional(),
    owner: z.string().optional(),
  }),
  is_active: z.boolean().default(true),
});

type CreateServiceAccountFormData = z.infer<typeof createServiceAccountSchema>;

interface CreateServiceAccountDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

interface Credentials {
  client_id: string;
  client_secret: string;
}

export function CreateServiceAccountDialog({ 
  open, 
  onOpenChange, 
  onSuccess 
}: CreateServiceAccountDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<Credentials | null>(null);
  const [showSecret, setShowSecret] = useState(false);

  const form = useForm<CreateServiceAccountFormData>({
    resolver: zodResolver(createServiceAccountSchema),
    defaultValues: {
      name: '',
      description: '',
      attributes: {
        purpose: '',
        environment: '',
        owner: '',
      },
      is_active: true,
    },
  });

  const onSubmit = async (data: CreateServiceAccountFormData) => {
    try {
      setLoading(true);
      setError(null);

      // Prepare the data according to API format
      const serviceAccountData = {
        name: data.name,
        description: data.description || undefined,
        attributes: Object.fromEntries(
          Object.entries(data.attributes).filter(([_, value]) => value)
        ),
        is_active: data.is_active,
      };

      const response = await apiClient.request('/service-accounts', {
        method: 'POST',
        body: JSON.stringify(serviceAccountData),
      });
      
      console.log('Service account created:', response);
      
      // Response should contain both service_account and credentials
      if (response.credentials) {
        setCredentials(response.credentials);
      }
      
      onSuccess?.();
    } catch (err: any) {
      console.error('Create service account error:', err);
      setError(err.message || 'Failed to create service account');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!credentials) {
      form.reset();
      setError(null);
      onOpenChange(false);
    }
  };

  const handleCredentialsCopied = () => {
    setCredentials(null);
    form.reset();
    setError(null);
    setShowSecret(false);
    onOpenChange(false);
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: `${label} copied to clipboard`,
    });
  };

  // If credentials are generated, show the credentials dialog
  if (credentials) {
    return (
      <Dialog open={open} onOpenChange={() => {}}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span>Service Account Created</span>
            </DialogTitle>
            <DialogDescription>
              Your service account has been created successfully. Please save these credentials securely.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="bg-muted p-4 rounded-lg space-y-3">
              <div>
                <label className="text-sm font-medium">Client ID</label>
                <div className="flex items-center space-x-2 mt-1">
                  <code className="flex-1 bg-background p-2 rounded text-xs">
                    {credentials.client_id}
                  </code>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(credentials.client_id, 'Client ID')}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium">Client Secret</label>
                <div className="flex items-center space-x-2 mt-1">
                  <code className="flex-1 bg-background p-2 rounded text-xs">
                    {showSecret ? credentials.client_secret : '••••••••••••••••'}
                  </code>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowSecret(!showSecret)}
                  >
                    {showSecret ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(credentials.client_secret, 'Client Secret')}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
            
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>Important:</strong> This is the only time the client secret will be shown. 
                Make sure to save it in a secure location before closing this dialog.
              </AlertDescription>
            </Alert>
          </div>

          <DialogFooter>
            <Button onClick={handleCredentialsCopied} className="w-full">
              I've Saved the Credentials
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Key className="h-5 w-5" />
            <span>Create Service Account</span>
          </DialogTitle>
          <DialogDescription>
            Create a new service account for API access. Service accounts use client credentials 
            for authentication and can be used for automated integrations.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Basic Information */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium">Basic Information</h4>
              
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name *</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="e.g., Production API Client"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      A descriptive name for this service account
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Optional description of what this service account is used for..."
                        className="min-h-[80px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Describe the purpose and usage of this service account
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Attributes */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium">Additional Information</h4>
              
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="attributes.purpose"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Purpose</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., Data sync" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="attributes.environment"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Environment</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., Production" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="attributes.owner"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Owner</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., DevOps Team" {...field} />
                    </FormControl>
                    <FormDescription>
                      Team or person responsible for this service account
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Status */}
            <FormField
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel>
                      Active service account
                    </FormLabel>
                    <FormDescription>
                      Service account can authenticate and access the API
                    </FormDescription>
                  </div>
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <Key className="mr-2 h-4 w-4" />
                Create Service Account
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}