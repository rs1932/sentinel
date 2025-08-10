import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface AppSettings {
  // Application Settings
  appName: string;
  appDescription: string;
  maintenanceMode: boolean;
  registrationEnabled: boolean;
  
  // Notification Settings
  emailNotifications: boolean;
  pushNotifications: boolean;
  systemAlerts: boolean;
  
  // Security Settings
  mfaRequired: boolean;
  sessionTimeout: number;
  passwordComplexity: boolean;
  
  // Theme Settings
  theme: 'light' | 'dark' | 'system';
  primaryColor: string;
  
  // Localization
  defaultLocale: string;
  timezone: string;
}

interface SettingsState {
  settings: AppSettings;
  isLoading: boolean;
  lastSaved: Date | null;
}

interface SettingsActions {
  updateSetting: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => void;
  updateMultipleSettings: (updates: Partial<AppSettings>) => void;
  resetSettings: () => void;
  saveSettings: () => Promise<void>;
  loadSettings: () => Promise<void>;
  setLoading: (loading: boolean) => void;
}

// Default settings
const defaultSettings: AppSettings = {
  // Application Settings
  appName: 'Sentinel',
  appDescription: 'Multi-tenant User Management Platform',
  maintenanceMode: false,
  registrationEnabled: true,
  
  // Notification Settings
  emailNotifications: true,
  pushNotifications: false,
  systemAlerts: true,
  
  // Security Settings
  mfaRequired: false,
  sessionTimeout: 3600,
  passwordComplexity: true,
  
  // Theme Settings
  theme: 'light',
  primaryColor: 'blue',
  
  // Localization
  defaultLocale: 'en-US',
  timezone: 'America/New_York',
};

export const useSettingsStore = create<SettingsState & SettingsActions>()(
  persist(
    (set, get) => ({
      // State
      settings: defaultSettings,
      isLoading: false,
      lastSaved: null,

      // Actions
      updateSetting: (key, value) => {
        set((state) => ({
          settings: {
            ...state.settings,
            [key]: value,
          },
        }));
      },

      updateMultipleSettings: (updates) => {
        set((state) => ({
          settings: {
            ...state.settings,
            ...updates,
          },
        }));
      },

      resetSettings: () => {
        set({
          settings: defaultSettings,
          lastSaved: null,
        });
      },

      saveSettings: async () => {
        const { settings } = get();
        set({ isLoading: true });

        try {
          // TODO: Replace with actual API call
          // await apiClient.settings.update(settings);
          
          // Mock API delay
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          set({ 
            isLoading: false,
            lastSaved: new Date(),
          });
          
          console.log('Settings saved:', settings);
        } catch (error) {
          set({ isLoading: false });
          console.error('Failed to save settings:', error);
          throw error;
        }
      },

      loadSettings: async () => {
        set({ isLoading: true });

        try {
          // TODO: Replace with actual API call
          // const response = await apiClient.settings.get();
          
          // Mock API delay and response
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // For now, use stored settings or defaults
          const { settings } = get();
          
          set({ 
            isLoading: false,
            settings,
          });
          
          console.log('Settings loaded:', settings);
        } catch (error) {
          set({ 
            isLoading: false,
            settings: defaultSettings,
          });
          console.error('Failed to load settings:', error);
        }
      },

      setLoading: (loading) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'settings-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        settings: state.settings,
        lastSaved: state.lastSaved,
      }),
    }
  )
);