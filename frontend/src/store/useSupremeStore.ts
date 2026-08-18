import { create } from 'zustand';
import { persist, subscribeWithSelector } from 'zustand/middleware';

import { createAuthSlice, type AuthSlice } from './slices/authSlice';
import { createThemeSlice, type ThemeSlice } from './slices/themeSlice';
import { createDashboardSlice, type DashboardSlice } from './slices/dashboardSlice';
import { createAdminSlice, type AdminSlice } from './slices/adminSlice';
import { createWorkspaceSlice, type WorkspaceSlice } from './slices/workspaceSlice';
import { createWorkspaceSettingsSlice, type WorkspaceSettingsSlice } from './slices/workspaceSettingsSlice';
import { createSessionCockpitSlice, type SessionCockpitSlice } from './slices/sessionCockpitSlice';
import { createIdeSlice, type IdeSlice } from './slices/ideSlice';
import { createCustomerSlice, type CustomerSlice } from './slices/customerSlice';
import { createCoreSlice, type CoreSlice } from './slices/coreSlice';

// বাংলা মন্তব্য: সব স্টোর স্লাইস প্যাটার্নে ভাগ করা হয়েছে। পাবলিক API (useSupremeStore)
// অপরিবর্তিত রাখা হয়েছে যাতে ১১টি আলাদা legacy স্টোর মাইগ্রেট না করেও কনজুমার ভাঙবে না।
// মাইগ্রেশন প্ল্যান: adminStore/authStore/dashboardStore/customerStore/useStore/
// useWorkspaceStore/useIdeStore/sessionCockpitStore → useSupremeStore স্লাইসে রিডাইরেক্ট।

export type SupremeStore = AuthSlice
  & ThemeSlice
  & DashboardSlice
  & AdminSlice
  & WorkspaceSlice
  & WorkspaceSettingsSlice
  & SessionCockpitSlice
  & IdeSlice
  & CustomerSlice
  & CoreSlice;

// বাংলা মন্তব্য: সুপ্রিম স্টেট টাইপ অ্যালাইয়াস — ব্যাকওয়ার্ড কম্প্যাটিবিলিটির জন্য
export type SupremeState = SupremeStore;

// Re-export domain types previously declared in the monolith (backward compatibility).
export type { User, Workspace, Role, Permission, Session } from './slices/types';

export const useSupremeStore = create<SupremeStore>()(
  persist(
    subscribeWithSelector((...a) => ({
      ...createAuthSlice(...a),
      ...createThemeSlice(...a),
      ...createDashboardSlice(...a),
      ...createAdminSlice(...a),
      ...createWorkspaceSlice(...a),
      ...createWorkspaceSettingsSlice(...a),
      ...createSessionCockpitSlice(...a),
      ...createIdeSlice(...a),
      ...createCustomerSlice(...a),
      ...createCoreSlice(...a),
    })),
    {
      name: 'supreme-storage',
      partialize: (state) => ({
        theme: state.theme,
        activeWorkspace: state.activeWorkspace,
        settings: state.settings,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    },
  ),
);

export default useSupremeStore;
