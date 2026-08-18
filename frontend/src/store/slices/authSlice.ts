import type { StateCreator } from 'zustand';
import type { SupremeStore } from '../useSupremeStore';
import type { User } from './types';
import { apiClient, updateTokenCache } from '../../services/apiClient';

export const AuthStatus = {
  UNINITIALIZED: 'uninitialized',
  LOGGED_OUT: 'loggedOut',
  LOGGED_IN: 'loggedIn',
} as const;

export type AuthStatus = (typeof AuthStatus)[keyof typeof AuthStatus];

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
}

export interface AuthSlice {
  isAuthenticated: boolean;
  status: AuthStatus;
  user: (User & UserProfile) | null;
  loginUser: (userData: User) => void;
  updateUser: (userData: Partial<User>) => void;
  login: (emailOrUser: string | User, password?: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
  initializeAuth: () => Promise<void>;
}

const TOKEN_KEY = 'supremeai_auth_token';
const USER_KEY = 'supremeai_auth_user';

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const part = token.split('.')[1];
    if (!part) return null;
    const base64 = part.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join(''),
    );
    return JSON.parse(jsonPayload) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function persistUser(user: UserProfile | null) {
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
}

function restoreUser(): UserProfile | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as UserProfile;
    if (!parsed || typeof parsed !== 'object' || typeof parsed.email !== 'string') return null;
    return parsed;
  } catch {
    return null;
  }
}

const avatarUrl = (label: string) =>
  `https://ui-avatars.com/api/?name=${encodeURIComponent(label)}&background=random`;

export const createAuthSlice: StateCreator<SupremeStore, [], [], AuthSlice> = (set, get) => ({
  isAuthenticated: false,
  status: AuthStatus.UNINITIALIZED,
  user: null,

  loginUser: (userData) =>
    set({
      isAuthenticated: true,
      status: AuthStatus.LOGGED_IN,
      user: userData as unknown as (User & UserProfile),
    }),

  updateUser: (userData) =>
    set({ user: get().user ? ({ ...get().user, ...userData } as unknown as (User & UserProfile)) : null }),

  login: async (emailOrUser: string | User, password?: string) => {
    if (typeof emailOrUser === 'object') {
      set({
        isAuthenticated: true,
        status: AuthStatus.LOGGED_IN,
        user: emailOrUser as unknown as (User & UserProfile),
      });
      return;
    }

    const email = emailOrUser;
    try {
      interface AuthLoginResponse {
        access_token: string;
        user_id: string;
      }
      const response = await apiClient.post<AuthLoginResponse>('/api/v1/auth/login', {
        username: email,
        password: password,
      });

      const token = response.access_token;
      localStorage.setItem(TOKEN_KEY, token);
      updateTokenCache(token);

      const userProfile: UserProfile = {
        id: response.user_id,
        email,
        name: email.split('@')[0],
        avatarUrl: avatarUrl(email),
      };
      persistUser(userProfile);

      set({
        isAuthenticated: true,
        status: AuthStatus.LOGGED_IN,
        user: userProfile as unknown as (User & UserProfile),
      });
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  },

  register: async (email, name, password) => {
    try {
      interface AuthRegisterResponse {
        access_token: string;
        user_id: string;
      }
      const response = await apiClient.post<AuthRegisterResponse>('/api/v1/auth/register', {
        username: email,
        password: password,
        name: name,
      });

      const token = response.access_token;
      localStorage.setItem(TOKEN_KEY, token);
      updateTokenCache(token);

      const userProfile: UserProfile = {
        id: response.user_id,
        email,
        name,
        avatarUrl: avatarUrl(name),
      };
      persistUser(userProfile);

      set({
        isAuthenticated: true,
        status: AuthStatus.LOGGED_IN,
        user: userProfile as unknown as (User & UserProfile),
      });
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    updateTokenCache(null);
    persistUser(null);
    set({ isAuthenticated: false, status: AuthStatus.LOGGED_OUT, user: null });
  },

  initializeAuth: async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      updateTokenCache(null);
      persistUser(null);
      set({ isAuthenticated: false, status: AuthStatus.LOGGED_OUT, user: null });
      return;
    }

    updateTokenCache(token);

    const cachedUser = restoreUser();
    const payload = decodeJwtPayload(token);
    const payloadEmail =
      typeof payload?.email === 'string' && payload.email ? payload.email : '';
    const payloadName =
      typeof payload?.name === 'string' && payload.name
        ? payload.name
        : payloadEmail
          ? payloadEmail.split('@')[0]
          : 'User';

    const optimisticUser: UserProfile = cachedUser ?? {
      id: typeof payload?.sub === 'string' ? payload.sub : '',
      email: payloadEmail || 'user@supremeai.dev',
      name: payloadName,
      avatarUrl: avatarUrl(payloadEmail || payloadName),
    };

    set({ isAuthenticated: true, status: AuthStatus.LOGGED_IN, user: optimisticUser as unknown as (User & UserProfile) });

    try {
      interface AuthMeResponse {
        user_id?: string;
        email?: string;
        username?: string;
        name?: string;
        role?: string;
      }
      const response = await apiClient.get<AuthMeResponse>('/api/v1/auth/me');
      const verifiedEmail = response.email || response.username || optimisticUser.email;
      const freshUser: UserProfile = {
        id: response.user_id || optimisticUser.id,
        email: verifiedEmail,
        name: response.name || response.role || optimisticUser.name,
        avatarUrl: avatarUrl(verifiedEmail || response.role || optimisticUser.name),
      };
      persistUser(freshUser);
      set({
        isAuthenticated: true,
        status: AuthStatus.LOGGED_IN,
        user: freshUser as unknown as (User & UserProfile),
      });
    } catch (error: unknown) {
      const status = (error as { status?: number })?.status;
      if (status === 401 || status === 403) {
        localStorage.removeItem(TOKEN_KEY);
        updateTokenCache(null);
        persistUser(null);
        set({ isAuthenticated: false, status: AuthStatus.LOGGED_OUT, user: null });
      } else {
        if (import.meta.env.DEV) {
          console.warn('Session validation deferred (transient error):', (error as Error)?.message);
        }
      }
    }
  },
});
