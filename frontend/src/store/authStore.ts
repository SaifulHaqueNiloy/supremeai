import { create } from 'zustand';
import { apiClient, updateTokenCache } from '../services/apiClient';

// বাংলা মন্তব্য: erasableSyntaxOnly সক্রিয় থাকায় enum-এর বদলে const object + union type ব্যবহার করা হচ্ছে
export const AuthStatus = {
  UNINITIALIZED: 'uninitialized',
  LOGGED_OUT: 'loggedOut',
  LOGGED_IN: 'loggedIn',
} as const;

export type AuthStatus = (typeof AuthStatus)[keyof typeof AuthStatus];

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

const TOKEN_KEY = 'supremeai_auth_token';
const USER_KEY = 'supremeai_auth_user';

// বাংলা মন্তব্য: JWT payload নিরাপদে ডিকোড করা হয় (reload-এ token থেকেই ইউজার প্রোফাইল রিস্টোর করার জন্য)।
function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const part = token.split('.')[1];
    if (!part) return null;
    const base64 = part.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
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

// 🔻 @deprecated Consolidate auth state into the unified `useSupremeStore` (see slices/authSlice).
// Kept for backward compatibility — do not add new usages; migrate consumers to useSupremeStore.
export const useAuthStore = create<AuthState>((set) => ({
  status: AuthStatus.UNINITIALIZED,
  user: null,

  login: async (email, password) => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const response = await apiClient.post<any>('/api/v1/auth/login', {
        username: email,
        password: password
      });

      const token = response.access_token;
      localStorage.setItem(TOKEN_KEY, token);
      updateTokenCache(token);

      const user: UserProfile = {
        id: response.user_id,
        email,
        name: email.split('@')[0], // Backend does not return name right now
        avatarUrl: avatarUrl(email),
      };
      persistUser(user);

      set({
        status: AuthStatus.LOGGED_IN,
        user,
      });
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    }
  },

  register: async (email, name, password) => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const response = await apiClient.post<any>('/api/v1/auth/register', {
        username: email,
        password: password,
        name: name
      });

      const token = response.access_token;
      localStorage.setItem(TOKEN_KEY, token);
      updateTokenCache(token);

      const user: UserProfile = {
        id: response.user_id,
        email,
        name,
        avatarUrl: avatarUrl(name),
      };
      persistUser(user);

      set({
        status: AuthStatus.LOGGED_IN,
        user,
      });
    } catch (error) {
      console.error("Registration failed:", error);
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    updateTokenCache(null);
    persistUser(null);
    set({ status: AuthStatus.LOGGED_OUT, user: null });
  },

  initialize: async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      updateTokenCache(null);
      persistUser(null);
      set({ status: AuthStatus.LOGGED_OUT, user: null });
      return;
    }

    updateTokenCache(token);

    // বাংলা মন্তব্য: Optimistic restore — reload-এ নেটওয়ার্ক রেসপন্সের জন্য অপেক্ষা না করেই
    // token + cached profile দিয়ে সেশন পুনরুদ্ধার করা হয় (logout-on-reload ফিক্স)।
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

    set({ status: AuthStatus.LOGGED_IN, user: optimisticUser });

    // বাংলা মন্তব্য: ব্যাকগ্রাউন্ডে token ভ্যালিডেট করা হয় — শুধুমাত্র নিশ্চিত 401/403-এ
    // logout হবে; নেটওয়ার্ক/কোল্ড-স্টার্ট/5xx এরর হলে সেশন অক্ষত থাকে।
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const response = await apiClient.get<any>('/api/v1/auth/me');
      const verifiedEmail = response.email || response.username || optimisticUser.email;
      const freshUser: UserProfile = {
        id: response.user_id || optimisticUser.id,
        email: verifiedEmail,
        name: response.name || response.role || optimisticUser.name,
        avatarUrl: avatarUrl(verifiedEmail || response.role || optimisticUser.name),
      };
      persistUser(freshUser);
      set({
        status: AuthStatus.LOGGED_IN,
        user: freshUser,
      });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      const status = error?.status as number | undefined;
      if (status === 401 || status === 403) {
        // বাংলা মন্তব্য: Token সত্যিই invalid/revoked — শুধুমাত্র এই ক্ষেত্রেই সেশন মুছে দেওয়া হয়।
        localStorage.removeItem(TOKEN_KEY);
        updateTokenCache(null);
        persistUser(null);
        set({ status: AuthStatus.LOGGED_OUT, user: null });
      } else {
        // বাংলা মন্তব্য: ক্ষণস্থায়ী ব্যর্থতা (নেটওয়ার্ক ডাউন / Render cold start / 5xx) — logout নয়।
        if (import.meta.env.DEV) {
          console.warn('Session validation deferred (transient error):', error?.message);
        }
      }
    }
  },
}));
