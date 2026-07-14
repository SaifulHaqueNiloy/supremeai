import { create } from 'zustand';
import { apiClient } from '../services/apiClient';

export enum AuthStatus {
  UNINITIALIZED = 'uninitialized',
  LOGGED_OUT = 'loggedOut',
  LOGGED_IN = 'loggedIn',
}

interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
}

interface AuthState {
  status: AuthStatus;
  user: UserProfile | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  status: AuthStatus.UNINITIALIZED,
  user: null,

  login: async (email, password) => {
    try {
      const response = await apiClient.post<any>('/auth/login', {
        username: email,
        password: password
      });

      const token = response.access_token;
      localStorage.setItem('supremeai_auth_token', token);

      set({
        status: AuthStatus.LOGGED_IN,
        user: {
          id: response.user_id,
          email,
          name: email.split('@')[0], // Backend does not return name right now
          avatarUrl: `https://ui-avatars.com/api/?name=${encodeURIComponent(email)}&background=random`,
        },
      });
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    }
  },

  register: async (email, name, password) => {
    try {
      const response = await apiClient.post<any>('/auth/register', {
        username: email,
        password: password,
        name: name
      });

      const token = response.access_token;
      localStorage.setItem('supremeai_auth_token', token);

      set({
        status: AuthStatus.LOGGED_IN,
        user: {
          id: response.user_id,
          email,
          name,
          avatarUrl: `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=random`,
        },
      });
    } catch (error) {
      console.error("Registration failed:", error);
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('supremeai_auth_token');
    set({ status: AuthStatus.LOGGED_OUT, user: null });
  },

  initialize: async () => {
    const token = localStorage.getItem('supremeai_auth_token');
    if (token) {
      try {
        const response = await apiClient.get<any>('/auth/me');
        set({
          status: AuthStatus.LOGGED_IN,
          user: {
            id: response.user_id,
            email: 'dev_user@example.com', // /auth/me doesn't return email right now, this is a placeholder
            name: response.role,
            avatarUrl: `https://ui-avatars.com/api/?name=${encodeURIComponent(response.role)}&background=random`,
          }
        });
      } catch (e) {
        localStorage.removeItem('supremeai_auth_token');
        set({ status: AuthStatus.LOGGED_OUT });
      }
    } else {
      set({ status: AuthStatus.LOGGED_OUT });
    }
  },
}));
