// frontend/src/store/slices/adminSlice.ts
// বাংলা মন্তব্য: M0.2 — adminStore.ts-এর সম্পূর্ণ auth/login/TOTP লজিক এখানে ম্যাপ করা হয়েছে।
// useSupremeStore-এর মাধ্যমে একীকৃত — আলাগা zustand store নয়।

import type { StateCreator } from 'zustand';
import { getApiBaseUrl } from '../../utils/api';
import { getFirebaseAuth } from '../../firebase';
import { signInWithEmailAndPassword, signOut } from 'firebase/auth';
import type { SupremeStore } from '../useSupremeStore';
import type { User, Role, Permission } from './types';
import { buildProvisioningUri, decodeJwt, restoreAdminSession } from './adminAuthHelpers';

export interface AdminSlice {
  adminAuthenticated: boolean;
  adminRole: string | null;
  adminEmail: string;
  adminError: string;
  actionStatus: string;
  adminSubTab: string;
  otpRequired: boolean;
  adminOtp: string;
  totpSetupRequired: boolean;
  totpSecret: string;
  provisioningUri: string;

  users: User[];
  roles: Role[];
  permissions: Permission[];

  setAdminRole: (val: string | null) => void;
  setAdminError: (val: string) => void;
  setActionStatus: (val: string) => void;
  setAdminSubTab: (tab: string) => void;
  setAdminEmail: (val: string) => void;
  setOtpRequired: (val: boolean) => void;
  setAdminOtp: (val: string) => void;
  setTotpSetupRequired: (val: boolean) => void;
  setTotpSecret: (val: string) => void;
  setProvisioningUri: (val: string) => void;

  addUser: (user: User) => void;
  removeUser: (userId: string) => void;
  updateAdminUser: (user: User) => void;
  fetchUsers: () => Promise<void>;
  fetchRoles: () => Promise<void>;
  fetchPermissions: () => Promise<void>;

  handleAdminLogin: (password?: string) => Promise<void>;
  handleAdminLogout: () => void;
  resetTotpSetup: () => Promise<void>;
}

export const createAdminSlice: StateCreator<SupremeStore, [], [], AdminSlice> = (set, get) => ({
  adminAuthenticated: restoreAdminSession().adminAuthenticated,
  adminRole: restoreAdminSession().adminRole,
  adminEmail: '',
  adminError: '',
  actionStatus: '',
  adminSubTab: 'dashboard',
  otpRequired: false,
  adminOtp: '',
  totpSetupRequired: false,
  totpSecret: '',
  provisioningUri: '',
  users: [],
  roles: [],
  permissions: [],

  setAdminRole: (val) => set({ adminRole: val }),
  setAdminError: (val) => set({ adminError: val }),
  setActionStatus: (val) => set({ actionStatus: val }),
  setAdminSubTab: (tab) => set({ adminSubTab: tab }),
  setAdminEmail: (val) => set({ adminEmail: val }),
  setOtpRequired: (val) => set({ otpRequired: val }),
  setAdminOtp: (val) => set({ adminOtp: val }),
  setTotpSetupRequired: (val) => set({ totpSetupRequired: val }),
  setTotpSecret: (val) => set({ totpSecret: val }),
  setProvisioningUri: (val) => set({ provisioningUri: val }),

  addUser: (user) => set((state) => ({ users: [...state.users, user] })),
  removeUser: (userId) => set((state) => ({ users: state.users.filter((user) => user.id !== userId) })),
  updateAdminUser: (user) =>
    set((state) => ({ users: state.users.map((u) => (u.id === user.id ? { ...u, ...user } : u)) })),

  fetchUsers: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${getApiBaseUrl()}/admin-api/users`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('supreme_admin_jwt') || ''}` },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const users = await response.json();
      set({ users });
    } catch (err) {
      console.error('Failed to fetch users:', err);
      set({ error: 'Failed to fetch users' });
    } finally {
      set({ loading: false });
    }
  },
  fetchRoles: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${getApiBaseUrl()}/admin-api/roles`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('supreme_admin_jwt') || ''}` },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const roles = await response.json();
      set({ roles });
    } catch (err) {
      console.error('Failed to fetch roles:', err);
      set({ error: 'Failed to fetch roles' });
    } finally {
      set({ loading: false });
    }
  },
  fetchPermissions: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${getApiBaseUrl()}/admin-api/permissions`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('supreme_admin_jwt') || ''}` },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const permissions = await response.json();
      set({ permissions });
    } catch (err) {
      console.error('Failed to fetch permissions:', err);
      set({ error: 'Failed to fetch permissions' });
    } finally {
      set({ loading: false });
    }
  },

  handleAdminLogin: async (password?: string) => {
    const { adminEmail, otpRequired, adminOtp } = get();
    const cleanEmail = adminEmail.trim();
    const cleanPassword = password?.trim() || '';

    if (!otpRequired && (!cleanEmail || !cleanPassword)) return;
    set({ adminError: '' });

    try {
      const API_BASE = getApiBaseUrl();
      const auth = await getFirebaseAuth();
      let idToken = '';

      if (!otpRequired) {
        try {
          const userCredential = await signInWithEmailAndPassword(auth, cleanEmail, cleanPassword);
          idToken = await userCredential.user.getIdToken(true);
        } catch (authErr) {
          const msg = authErr instanceof Error ? authErr.message : String(authErr);
          set({ adminError: msg });
          return;
        }

        const res = await fetch(`${API_BASE}/api/admin/firebase-login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ id_token: idToken }),
        });
        const data = await res.json();

        if (res.ok) {
          if (data.status === 'otp_required') {
            set({ otpRequired: true });
          } else if (data.status === 'totp_setup_required') {
            const setupRes = await fetch(`${API_BASE}/api/admin/firebase-totp-setup`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              credentials: 'include',
              body: JSON.stringify({ id_token: idToken }),
            });
            const setupData = await setupRes.json();
            if (setupRes.ok) {
              set({
                totpSetupRequired: true,
                otpRequired: true,
                totpSecret: setupData.secret,
                provisioningUri: setupData.provisioning_uri || buildProvisioningUri(cleanEmail, setupData.secret || ''),
              });
            } else {
              set({ adminError: typeof setupData.detail === 'string' ? setupData.detail : 'Failed to setup TOTP.' });
            }
          }
        } else {
          set({ adminError: typeof data.detail === 'string' ? data.detail : 'Not authorized as admin.' });
        }
      } else {
        const user = auth.currentUser;
        if (!user) {
          set({ adminError: 'Session expired. Please login again.', otpRequired: false });
          return;
        }
        idToken = await user.getIdToken();

        const res = await fetch(`${API_BASE}/api/admin/firebase-totp-verify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ id_token: idToken, otp: adminOtp.trim() }),
        });

        if (res.ok) {
          const data = await res.json();
          if (data.token) {
            localStorage.setItem('supreme_admin_jwt', data.token);
            localStorage.setItem('adminToken', data.token);
            const decoded = decodeJwt(data.token);
            if (decoded && typeof decoded.role === 'string') {
              set({ adminRole: decoded.role });
            }
          }
          set({ adminAuthenticated: true, otpRequired: false, totpSetupRequired: false, adminOtp: '' });
        } else {
          const data = await res.json();
          set({ adminError: typeof data.detail === 'string' ? data.detail : 'Invalid verification code.' });
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ adminError: 'Connection failed: ' + msg });
    }
  },

  handleAdminLogout: async () => {
    try {
      const auth = await getFirebaseAuth();
      const TOKEN_KEYS = ['adminToken', 'supreme_admin_jwt', 'supremeai_auth_token'];
      TOKEN_KEYS.forEach((key) => localStorage.removeItem(key));
      await signOut(auth);
    } catch (e) {
      console.error('Logout failed:', e);
    }
    set({
      adminAuthenticated: false,
      adminRole: null,
      otpRequired: false,
      adminOtp: '',
      adminError: '',
      totpSetupRequired: false,
      totpSecret: '',
      provisioningUri: '',
    });
  },

  resetTotpSetup: async () => {
    set({ adminError: '' });
    try {
      const auth = await getFirebaseAuth();
      const user = auth.currentUser;
      if (!user) {
        set({ adminError: 'Session expired. Please login again.' });
        return;
      }
      const idToken = await user.getIdToken(true);
      const API_BASE = getApiBaseUrl();
      const email = (user.email || '').trim() || get().adminEmail.trim();

      const res = await fetch(`${API_BASE}/api/admin/firebase-totp-setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ id_token: idToken }),
      });
      const data = await res.json();
      if (res.ok) {
        set({
          totpSetupRequired: true,
          otpRequired: true,
          totpSecret: data.secret,
          provisioningUri: data.provisioning_uri || buildProvisioningUri(email, data.secret || ''),
        });
      } else {
        set({ adminError: typeof data.detail === 'string' ? data.detail : 'Failed to generate QR code.' });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ adminError: 'Connection failed: ' + msg });
    }
  },
});
