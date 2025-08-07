'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { useSettingsStore } from '@/store/settings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { 
  Settings, 
  Bell, 
  Shield, 
  Palette, 
  Globe, 
  Database,
  Mail,
  Save,
  RefreshCw
} from 'lucide-react';

export function SettingsManagement() {
  const { userRole } = useAuthStore();
  const { 
    settings, 
    isLoading, 
    lastSaved,
    updateSetting, 
    saveSettings, 
    resetSettings,
    loadSettings 
  } = useSettingsStore();
  
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Load settings on component mount
  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handleSettingChange = <K extends keyof typeof settings>(key: K, value: typeof settings[K]) => {
    updateSetting(key, value);
    // Clear save success message when user makes changes
    if (saveSuccess) {
      setSaveSuccess(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await saveSettings();
      setSaveSuccess(true);
      // Clear success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      // You could add error handling here
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    resetSettings();
    setSaveSuccess(false);
  };

  const isSystemAdmin = userRole === 'super_admin';

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">
            Manage application settings and configuration
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={handleReset} disabled={isLoading}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Reset
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={isSaving || isLoading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isSaving ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Status Messages */}
      {saveSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg">
          <div className="flex items-center space-x-2">
            <Save className="h-4 w-4" />
            <span className="text-sm font-medium">
              Settings saved successfully
              {lastSaved && (
                <span className="font-normal"> at {lastSaved.toLocaleTimeString()}</span>
              )}
            </span>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg">
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span className="text-sm font-medium">Loading settings...</span>
          </div>
        </div>
      )}

      {/* Application Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-blue-600" />
            <CardTitle>Application Settings</CardTitle>
          </div>
          <CardDescription>
            Basic application configuration and branding
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="appName">Application Name</Label>
              <Input
                id="appName"
                value={settings.appName}
                onChange={(e) => handleSettingChange('appName', e.target.value)}
                disabled={!isSystemAdmin}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="appDescription">Description</Label>
              <Input
                id="appDescription"
                value={settings.appDescription}
                onChange={(e) => handleSettingChange('appDescription', e.target.value)}
                disabled={!isSystemAdmin}
              />
            </div>
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <Label htmlFor="maintenance">Maintenance Mode</Label>
              <p className="text-sm text-gray-600">Temporarily disable access for maintenance</p>
            </div>
            <Switch
              id="maintenance"
              checked={settings.maintenanceMode}
              onCheckedChange={(checked) => handleSettingChange('maintenanceMode', checked)}
              disabled={!isSystemAdmin}
            />
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <Label htmlFor="registration">User Registration</Label>
              <p className="text-sm text-gray-600">Allow new users to register accounts</p>
            </div>
            <Switch
              id="registration"
              checked={settings.registrationEnabled}
              onCheckedChange={(checked) => handleSettingChange('registrationEnabled', checked)}
              disabled={!isSystemAdmin}
            />
          </div>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Shield className="h-5 w-5 text-green-600" />
            <CardTitle>Security Settings</CardTitle>
          </div>
          <CardDescription>
            Authentication and security configuration
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div>
              <Label htmlFor="mfa">Multi-Factor Authentication</Label>
              <p className="text-sm text-gray-600">Require MFA for all users</p>
            </div>
            <Switch
              id="mfa"
              checked={settings.mfaRequired}
              onCheckedChange={(checked) => handleSettingChange('mfaRequired', checked)}
              disabled={!isSystemAdmin}
            />
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <Label htmlFor="passwordComplexity">Password Complexity</Label>
              <p className="text-sm text-gray-600">Enforce strong password requirements</p>
            </div>
            <Switch
              id="passwordComplexity"
              checked={settings.passwordComplexity}
              onCheckedChange={(checked) => handleSettingChange('passwordComplexity', checked)}
              disabled={!isSystemAdmin}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="sessionTimeout">Session Timeout (seconds)</Label>
            <Input
              id="sessionTimeout"
              type="number"
              value={settings.sessionTimeout}
              onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
              disabled={!isSystemAdmin}
              className="w-48"
            />
            <p className="text-xs text-gray-500">
              Current: {Math.floor(settings.sessionTimeout / 60)} minutes
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Bell className="h-5 w-5 text-yellow-600" />
            <CardTitle>Notification Settings</CardTitle>
          </div>
          <CardDescription>
            Configure system notifications and alerts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div>
              <Label htmlFor="emailNotifs">Email Notifications</Label>
              <p className="text-sm text-gray-600">Send notifications via email</p>
            </div>
            <Switch
              id="emailNotifs"
              checked={settings.emailNotifications}
              onCheckedChange={(checked) => handleSettingChange('emailNotifications', checked)}
            />
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <Label htmlFor="pushNotifs">Push Notifications</Label>
              <p className="text-sm text-gray-600">Browser push notifications</p>
            </div>
            <Switch
              id="pushNotifs"
              checked={settings.pushNotifications}
              onCheckedChange={(checked) => handleSettingChange('pushNotifications', checked)}
            />
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <Label htmlFor="systemAlerts">System Alerts</Label>
              <p className="text-sm text-gray-600">Critical system notifications</p>
            </div>
            <Switch
              id="systemAlerts"
              checked={settings.systemAlerts}
              onCheckedChange={(checked) => handleSettingChange('systemAlerts', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Theme & Localization */}
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Palette className="h-5 w-5 text-purple-600" />
            <CardTitle>Appearance & Localization</CardTitle>
          </div>
          <CardDescription>
            Theme, language, and regional settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="locale">Default Language</Label>
              <select 
                id="locale"
                className="w-full p-2 border border-gray-300 rounded-md"
                value={settings.defaultLocale}
                onChange={(e) => handleSettingChange('defaultLocale', e.target.value)}
              >
                <option value="en-US">English (US)</option>
                <option value="en-GB">English (UK)</option>
                <option value="es-ES">Spanish</option>
                <option value="fr-FR">French</option>
                <option value="de-DE">German</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="timezone">Default Timezone</Label>
              <select 
                id="timezone"
                className="w-full p-2 border border-gray-300 rounded-md"
                value={settings.timezone}
                onChange={(e) => handleSettingChange('timezone', e.target.value)}
              >
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Chicago">Central Time</option>
                <option value="America/Denver">Mountain Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
                <option value="Europe/London">GMT</option>
                <option value="Europe/Paris">CET</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Information */}
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Database className="h-5 w-5 text-gray-600" />
            <CardTitle>System Information</CardTitle>
          </div>
          <CardDescription>
            Current system status and information
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Version:</span>
                <Badge variant="outline">v1.0.0</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Environment:</span>
                <Badge variant="outline" className="bg-green-50 text-green-700">
                  Development
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Database:</span>
                <Badge variant="outline" className="bg-blue-50 text-blue-700">
                  Connected
                </Badge>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Uptime:</span>
                <span className="text-sm">2d 14h 32m</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Last Backup:</span>
                <span className="text-sm">2 hours ago</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Active Users:</span>
                <span className="text-sm">42</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {!isSystemAdmin && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Shield className="h-4 w-4 text-yellow-600" />
            <span className="text-sm font-medium text-yellow-800">
              Limited Access
            </span>
          </div>
          <p className="text-sm text-yellow-700 mt-1">
            Some settings are restricted to Super Administrators. Contact your system administrator to modify system-wide settings.
          </p>
        </div>
      )}
    </div>
  );
}