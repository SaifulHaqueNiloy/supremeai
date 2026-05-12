import { AuthUser } from '../types';

const AUTH_TOKEN_KEY = 'supremeai_token';
const FIREBASE_USER_KEY = 'supremeai_user';
const LEGACY_TOKEN_KEY = 'authToken';

// Demo mode mock data for guest users
const DEMO_MOCK_DATA: Record<string, any> = {
  // Admin dashboard contract
  '/api/admin/dashboard/contract': {
    success: true,
    data: {
      contractVersion: '1.0.0-demo',
      title: 'SupremeAI Command Center',
      description: 'Demo Mode - Full system capabilities overview',
      stats: {
        totalUsers: 1247,
        activeUsers: 342,
        activeAIAgents: 8,
        systemHealthScore: 98,
        runningTasks: 42,
        runningProjects: 15,
        completedTasks: 12847,
        successRate: 99.2,
        systemHealthStatus: 'healthy' as const,
        systemHealthReason: 'All systems operational',
        knowledgeBaseSize: 45230,
        activeConnections: 89,
        totalProviders: 12,
        activeProviders: 10,
        backendConnected: true,
        databaseConnected: true,
        lastStartTime: Date.now() - 86400000 * 5,
        serverUptime: '5d 14h 23m',
        latency: 45,
      },
      navigation: [],
      components: [],
      apiEndpoints: {}
    }
  },
  
  // Provider list (demo)
  '/api/admin/providers/configured': {
    success: true,
    data: {
      providers: [
        {
          id: 'demo-gpt4',
          name: 'GPT-4o (Demo)',
          type: 'llm',
          apiKey: 'sk-demo-redacted',
          status: 'active',
          lastTested: new Date().toISOString(),
          models: ['gpt-4o', 'gpt-4-turbo'],
          creatorEmail: 'demo@supreme.ai',
          accountEmail: 'demo@openai.com',
          apiCount: 2,
          usageLimit: 100000,
          currentUsage: 45320,
          canCommunicate: true,
          canExecuteTasks: true,
          canParticipateInVoting: true,
          deploymentSource: 'api' as const
        },
        {
          id: 'demo-claude',
          name: 'Claude 3.5 Sonnet (Demo)',
          type: 'llm',
          apiKey: 'sk-demo-redacted',
          status: 'active',
          lastTested: new Date().toISOString(),
          models: ['claude-3-5-sonnet'],
          creatorEmail: 'demo@supreme.ai',
          accountEmail: 'demo@anthropic.com',
          apiCount: 1,
          usageLimit: 100000,
          currentUsage: 32100,
          canCommunicate: true,
          canExecuteTasks: false,
          canParticipateInVoting: true,
          deploymentSource: 'api' as const
        }
      ]
    }
  },

  // Projects list (demo)
  '/api/projects': [
    {
      id: 'demo-1',
      name: 'E-Commerce Platform',
      description: 'Full-stack online shopping application with AI recommendations',
      ownerId: 'demo-user',
      status: 'ACTIVE',
      createdAt: new Date(Date.now() - 86400000 * 10).toISOString(),
      updatedAt: new Date(Date.now() - 86400000 * 2).toISOString()
    },
    {
      id: 'demo-2',
      name: 'Smart Attendance System',
      description: 'Face recognition based attendance tracking',
      ownerId: 'demo-user',
      status: 'COMPLETED',
      createdAt: new Date(Date.now() - 86400000 * 30).toISOString(),
      updatedAt: new Date(Date.now() - 86400000 * 5).toISOString()
    },
    {
      id: 'demo-3',
      name: 'AI Code Review Bot',
      description: 'Automated code analysis and PR reviewer',
      ownerId: 'demo-user',
      status: 'RUNNING',
      createdAt: new Date(Date.now() - 86400000 * 3).toISOString(),
      updatedAt: new Date().toISOString()
    }
  ],

  // Chat history (demo)
  '/api/chat/history': {
    success: true,
    chat_history: [
      {
        id: 'demo-chat-1',
        is_admin: true,
        message: 'Welcome to SupremeAI Demo Mode! You can chat with AI assistants here.',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        intent: 'INFO_COLLECTION'
      },
      {
        id: 'demo-chat-2',
        is_admin: false,
        message: 'Hello! What can you help me with?',
        timestamp: new Date(Date.now() - 3500000).toISOString(),
        intent: 'NORMAL'
      },
      {
        id: 'demo-chat-3',
        is_admin: true,
        message: 'I can help you with coding, project generation, or answer questions. Try asking me to create a new app!',
        timestamp: new Date(Date.now() - 3400000).toISOString(),
        intent: 'PROJECT_PLAN'
      }
    ]
  },

  // Send chat (demo response)
  '/api/chat/send': {
    success: true,
    message: 'এটি একটি ডেমো রেসপন্স। বাস্তব পরিবেশে, আমি উন্নত AI মডেল ব্যবহার করে আপনার অনুরোধ প্রক্রিয়া করতাম। চেষ্টা করে দেখুন "একটি টোডো অ্যাপ তৈরি করুন" বা "পাইথন কী?"',
    agent_name: 'ডেমো সহকারী',
    confidence: 0.95,
    intent: 'NORMAL'
  },

  // Agents list (demo - this endpoint actually doesn't exist, so we mock it)
  '/api/ai/agents': [
    { id: 'gpt-4o', name: 'GPT-4o', status: 'online', type: 'llm' },
    { id: 'claude-3', name: 'Claude 3.5', status: 'online', type: 'llm' },
    { id: 'phi-3', name: 'Phi-3 Mini', status: 'offline', type: 'llm' }
  ],
  
  // Knowledge rules (demo)
  '/api/admin/rules': [
    { id: 1, name: 'Code Quality', condition: 'cyclomatic_complexity < 10', action: 'flag_for_review' },
    { id: 2, name: 'Security Scan', condition: 'vulnerability_detected', action: 'block_deployment' }
  ],

  // Plans (demo)
  '/api/admin/plans': [
    { id: 1, title: 'Q2 Roadmap', description: 'Improve model orchestration', status: 'active' },
    { id: 2, title: 'Security Audit', description: 'Third-party penetration testing', status: 'pending' }
  ],
};

export const authUtils = {
  getToken(): string | null {
    const token = localStorage.getItem(AUTH_TOKEN_KEY) || sessionStorage.getItem(AUTH_TOKEN_KEY);
    if (token) return token;
    const legacyToken = localStorage.getItem(LEGACY_TOKEN_KEY) || sessionStorage.getItem(LEGACY_TOKEN_KEY);
    if (legacyToken) {
      localStorage.setItem(AUTH_TOKEN_KEY, legacyToken);
      localStorage.removeItem(LEGACY_TOKEN_KEY);
      sessionStorage.removeItem(LEGACY_TOKEN_KEY);
      return legacyToken;
    }
    return 'GUEST_MODE';
  },

  isAdmin(): boolean {
    const user = this.getCurrentUser();
    return user?.role === 'admin' || user?.tier === 'admin' ||
           user?.email === 'admin@supreme.ai' ||
           user?.email === 'paykaribazaronline@gmail.com';
  },

  isAuthenticated(): boolean {
    const token = this.getToken();
    return !!token && token !== 'GUEST_MODE';
  },

  clearAuth() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(FIREBASE_USER_KEY);
    sessionStorage.removeItem(FIREBASE_USER_KEY);
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    sessionStorage.removeItem(LEGACY_TOKEN_KEY);
  },

  getCurrentUser(): any {
    const userStr = sessionStorage.getItem(FIREBASE_USER_KEY) || localStorage.getItem(FIREBASE_USER_KEY);
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch (e) {
      return null;
    }
  },

  setToken(token: string) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    sessionStorage.setItem(AUTH_TOKEN_KEY, token);
  },

  setCurrentUser(user: any) {
    const userStr = JSON.stringify(user);
    localStorage.setItem(FIREBASE_USER_KEY, userStr);
    sessionStorage.setItem(FIREBASE_USER_KEY, userStr);
  },

  getAuthHeaders(): HeadersInit {
    const token = this.getToken();
    if (token && token !== 'GUEST_MODE') {
      return { Authorization: `Bearer ${token}` };
    }
    return {};
  },

  async fetchWithAuth(url: string, options: any = {}) {
    const token = this.getToken();
    const isGuest = token === 'GUEST_MODE' || !token;
    const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || '';
    const fullUrl = url.startsWith('/') && API_BASE ? `${API_BASE}${url}` : url;
    
    // Normalize URL for mock lookup (strip base and query)
    let normalizedPath = url.split('?')[0];
    if (API_BASE && normalizedPath.startsWith(API_BASE)) {
      normalizedPath = normalizedPath.substring(API_BASE.length);
    }
    if (!normalizedPath.startsWith('/')) normalizedPath = '/' + normalizedPath;

    if (isGuest && DEMO_MOCK_DATA[normalizedPath]) {
      console.log(`[Demo Mode] Returning mock data for: ${normalizedPath}`);
      const mockData = DEMO_MOCK_DATA[normalizedPath];
      await new Promise(resolve => setTimeout(resolve, 200 + Math.random() * 300));
      return {
        ok: true,
        json: async () => mockData,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'Content-Type': 'application/json' }),
        text: async () => JSON.stringify(mockData)
      } as Response;
    }

    const headers = new Headers(options.headers || {});
    if (token && token !== 'GUEST_MODE') {
      headers.set('Authorization', `Bearer ${token}`);
    }

    let response = await fetch(fullUrl, { ...options, headers });

    if (response.status === 401) {
      if (isGuest) {
        console.warn("[Demo Mode] 401 encountered in Guest mode. Returning mock if available.");
        if (DEMO_MOCK_DATA[normalizedPath]) {
          return {
            ok: true,
            json: async () => DEMO_MOCK_DATA[normalizedPath],
            status: 200,
            statusText: 'OK',
            headers: new Headers({ 'Content-Type': 'application/json' }),
            text: async () => JSON.stringify(DEMO_MOCK_DATA[normalizedPath])
          } as Response;
        }
      } else {
        try {
          const { refreshAccessToken } = await import('./firebase');
          const newToken = await refreshAccessToken();
          headers.set('Authorization', `Bearer ${newToken}`);
          response = await fetch(fullUrl, { ...options, headers });
        } catch (err) {
          this.clearAuth();
          window.location.href = '/';
        }
      }
    } else if ((response.status === 403 || response.status === 404) && isGuest && DEMO_MOCK_DATA[normalizedPath]) {
      console.log(`[Demo Mode] ${response.status} intercepted, showing mock: ${normalizedPath}`);
      return {
        ok: true,
        json: async () => DEMO_MOCK_DATA[normalizedPath],
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'Content-Type': 'application/json' }),
        text: async () => JSON.stringify(DEMO_MOCK_DATA[normalizedPath])
      } as Response;
    }
    
    return response;
  }
};

export const fetchWithAuth = authUtils.fetchWithAuth.bind(authUtils);
export const getAuthHeaders = authUtils.getAuthHeaders.bind(authUtils);
export default authUtils;
