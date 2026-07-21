// admin/dashboard_light/script.js
// SupremeAI Light Admin Dashboard - Enhanced Version

// ════════════════════════════════════════════════════════════
// 1. CONFIGURATION & STATE MANAGEMENT
// ════════════════════════════════════════════════════════════
const CONFIG = {
  REPO: 'paykaribazaronline/supremeai',
  BRANCH: 'main',
  API_BASE: '', // Configure your backend API here
  WS_BASE: '',  // WebSocket endpoint if available
  POLL_INTERVAL: 30000, // 30 seconds
  AUTH_TOKEN_KEY: 'supremeai_admin_token',
  THEME_KEY: 'supremeai_theme'
};

const RAW_URL = `https://raw.githubusercontent.com/${CONFIG.REPO}/${CONFIG.BRANCH}`;

// Application State
const AppState = {
  auth: {
    isAuthenticated: false,
    token: localStorage.getItem(CONFIG.AUTH_TOKEN_KEY) || null,
    user: null
  },
  theme: localStorage.getItem(CONFIG.THEME_KEY) || 'dark',
  data: {
    metrics: null,
    jobs: [],
    health: [],
    lastUpdated: null
  },
  ui: {
    activeView: 'view-dashboard',
    jobFilter: 'all',
    isLoading: false,
    error: null
  }
};

// ════════════════════════════════════════════════════════════
// 2. UTILITY FUNCTIONS
// ════════════════════════════════════════════════════════════
const Utils = {
  // Debounce function for search/filter
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  // Format numbers with locale
  formatNumber(num) {
    if (num === null || num === undefined) return '--';
    return Number(num).toLocaleString();
  },

  // Format date
  formatDate(date) {
    return new Date(date).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  },

  // Generate unique ID
  generateId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  },

  // Show notification
  notify(message, type = 'info') {
    const colors = {
      info: 'var(--accent)',
      success: 'var(--success)',
      warning: 'var(--warning)',
      error: 'var(--danger)'
    };
    
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 16px 24px;
      background: var(--bg-surface);
      border: 1px solid ${colors[type]};
      border-radius: 8px;
      color: ${colors[type]};
      font-weight: 500;
      z-index: 1000;
      animation: slideIn 0.3s ease;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  },

  // Error handler
  handleError(error, context = 'Operation') {
    console.error(`[${context}]`, error);
    AppState.ui.error = error.message;
    this.notify(`${context} failed: ${error.message}`, 'error');
  }
};

// Add notification animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
`;
document.head.appendChild(style);

// ════════════════════════════════════════════════════════════
// 3. AUTHENTICATION MODULE
// ════════════════════════════════════════════════════════════
const Auth = {
  // Check if user is authenticated
  check() {
    const token = localStorage.getItem(CONFIG.AUTH_TOKEN_KEY);
    if (token) {
      AppState.auth.isAuthenticated = true;
      AppState.auth.token = token;
      this.updateUI();
      return true;
    }
    return false;
  },

  // Show auth modal
  showModal() {
    document.getElementById('authModal').classList.remove('hidden');
  },

  // Hide auth modal
  hideModal() {
    document.getElementById('authModal').classList.add('hidden');
  },

  // Submit authentication
  async submit(token) {
    try {
      // Demo mode - accept any non-empty token
      if (token && token.trim()) {
        localStorage.setItem(CONFIG.AUTH_TOKEN_KEY, token);
        AppState.auth.isAuthenticated = true;
        AppState.auth.token = token;
        AppState.auth.user = { name: 'Admin', role: 'administrator' };
        
        this.hideModal();
        this.updateUI();
        Utils.notify('Authentication successful!', 'success');
        
        // Refresh data after auth
        await DataService.refreshAll();
      }
    } catch (error) {
      Utils.handleError(error, 'Authentication');
    }
  },

  // Logout
  logout() {
    localStorage.removeItem(CONFIG.AUTH_TOKEN_KEY);
    AppState.auth.isAuthenticated = false;
    AppState.auth.token = null;
    AppState.auth.user = null;
    this.updateUI();
    Utils.notify('Logged out successfully', 'info');
  },

  // Update UI based on auth state
  updateUI() {
    const userBadge = document.getElementById('userBadge');
    const userName = document.getElementById('userName');
    
    if (AppState.auth.isAuthenticated && AppState.auth.user) {
      userBadge.style.display = 'flex';
      userName.textContent = AppState.auth.user.name;
    } else {
      userBadge.style.display = 'none';
    }
  }
};

// ════════════════════════════════════════════════════════════
// 4. THEME MANAGER
// ════════════════════════════════════════════════════════════
const Theme = {
  toggle() {
    const newTheme = AppState.theme === 'dark' ? 'light' : 'dark';
    this.apply(newTheme);
  },

  apply(theme) {
    AppState.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(CONFIG.THEME_KEY, theme);
    
    const toggleBtn = document.getElementById('themeToggle');
    toggleBtn.textContent = theme === 'dark' ? '🌓 Light Mode' : '🌓 Dark Mode';
  },

  init() {
    this.apply(AppState.theme);
  }
};

// ════════════════════════════════════════════════════════════
// 5. DATA SERVICE (API CLIENT)
// ════════════════════════════════════════════════════════════
const DataService = {
  // Generic fetch wrapper with error handling
  async fetch(endpoint, options = {}) {
    try {
      const url = `${CONFIG.API_BASE}${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(AppState.auth.token && { 'Authorization': `Bearer ${AppState.auth.token}` }),
          ...options.headers
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      Utils.handleError(error, `API ${endpoint}`);
      throw error;
    }
  },

  // Fetch metrics from backend
  async fetchMetrics() {
    try {
      // Try backend API first
      if (CONFIG.API_BASE) {
        const data = await this.fetch('/api/admin/metrics');
        AppState.data.metrics = data;
        return data;
      }
      
      // Fallback to mock data for demo
      return this.generateMockMetrics();
    } catch (error) {
      // Return mock data on error
      return this.generateMockMetrics();
    }
  },

  // Fetch CI/CD jobs
  async fetchJobs() {
    try {
      // Try GitHub Raw API
      const response = await fetch(`${RAW_URL}/logs/ci/latest.json?t=${Date.now()}`);
      if (response.ok) {
        const data = await response.json();
        AppState.data.jobs = data.jobs || {};
        return data.jobs;
      }
    } catch (error) {
      console.warn('GitHub fetch failed, using mock data');
    }
    
    // Fallback to mock jobs
    return this.generateMockJobs();
  },

  // Fetch health status
  async fetchHealth() {
    try {
      if (CONFIG.API_BASE) {
        const data = await this.fetch('/api/admin/health');
        AppState.data.health = data;
        return data;
      }
    } catch (error) {
      console.warn('Health API failed, using mock data');
    }
    
    return this.generateMockHealth();
  },

  // Refresh all data
  async refreshAll() {
    AppState.ui.isLoading = true;
    this.updateLoadingState();

    try {
      await Promise.all([
        this.fetchMetrics(),
        this.fetchJobs(),
        this.fetchHealth()
      ]);

      AppState.data.lastUpdated = new Date();
      this.renderAll();
      Utils.notify('Data refreshed successfully', 'success');
    } catch (error) {
      Utils.handleError(error, 'Data refresh');
    } finally {
      AppState.ui.isLoading = false;
      this.updateLoadingState();
    }
  },

  // Update loading state in UI
  updateLoadingState() {
    const syncText = document.getElementById('syncText');
    if (AppState.ui.isLoading) {
      syncText.textContent = 'Syncing...';
    } else {
      syncText.textContent = 'Live Sync';
    }
  },

  // Render all data to UI
  renderAll() {
    this.renderMetrics();
    this.renderJobs();
    this.renderHealth();
  },

  // Render metrics
  renderMetrics() {
    const metrics = AppState.data.metrics;
    if (!metrics) return;

    document.getElementById('apiStatus').textContent = 'Healthy';
    document.getElementById('activeJobs').textContent = Utils.formatNumber(metrics.total_requests_24h);
    document.getElementById('systemLoad').textContent = `${metrics.cpu_usage_percent || 0}%`;
  },

  // Render jobs
  renderJobs() {
    const jobs = AppState.data.jobs;
    const grid = document.getElementById('jobsGrid');
    
    if (!jobs || Object.keys(jobs).length === 0) {
      grid.innerHTML = '<div class="text-muted">No jobs found</div>';
      return;
    }

    const jobArray = Object.entries(jobs).map(([id, status]) => ({
      id,
      name: formatJobName(id),
      status
    }));

    // Apply filter
    const filtered = AppState.ui.jobFilter === 'all' 
      ? jobArray 
      : jobArray.filter(job => job.status === AppState.ui.jobFilter);

    grid.innerHTML = filtered.map(job => {
      const icon = job.status === 'success' ? '✅' : job.status === 'failure' ? '❌' : '⏭';
      const color = job.status === 'success' ? 'var(--success)' : job.status === 'failure' ? 'var(--danger)' : 'var(--text-muted)';
      
      return `
        <div class="job-card" onclick="Terminal.open('${job.id}', '${job.status}')">
          <div>
            <h4>${job.name}</h4>
            <p>Status: ${job.status.toUpperCase()}</p>
          </div>
          <span class="job-status-icon" style="color: ${color}">${icon}</span>
        </div>
      `;
    }).join('');
  },

  // Render health status
  renderHealth() {
    const health = AppState.data.health;
    const grid = document.getElementById('healthGrid');
    
    if (!health || health.length === 0) {
      grid.innerHTML = '<div class="text-muted">Health data unavailable</div>';
      return;
    }

    grid.innerHTML = health.map(service => {
      const statusClass = service.status === 'healthy' ? 'healthy' : service.status === 'warning' ? 'warning' : 'critical';
      
      return `
        <div class="health-card">
          <h4>${service.name}</h4>
          <div class="health-status">
            <span class="health-dot ${statusClass}"></span>
            <span>${service.status.toUpperCase()}</span>
          </div>
          <p class="text-muted">${service.message || 'Operational'}</p>
          <p class="text-muted" style="font-size: 11px; margin-top: 4px;">
            Last check: ${Utils.formatDate(service.lastCheck)}
          </p>
        </div>
      `;
    }).join('');
  },

  // Generate mock metrics
  generateMockMetrics() {
    return {
      total_requests_24h: Math.floor(Math.random() * 5000) + 1000,
      cpu_usage_percent: Math.floor(Math.random() * 60) + 20,
      gpu_usage_percent: Math.floor(Math.random() * 70) + 10,
      memory_usage_percent: Math.floor(Math.random() * 50) + 30,
      latency_p50_ms: Math.floor(Math.random() * 50) + 20,
      latency_p95_ms: Math.floor(Math.random() * 100) + 50,
      requests_per_second: Math.floor(Math.random() * 100) + 20,
      cost_per_hour: Math.random() * 0.5
    };
  },

  // Generate mock jobs
  generateMockJobs() {
    const jobNames = [
      'build_backend_image',
      'deploy_user_backend',
      'deploy_admin_backend',
      'deploy_combined_backend',
      'run_tests',
      'security_scan'
    ];

    const statuses = ['success', 'success', 'success', 'failure', 'running'];
    const jobs = {};

    jobNames.forEach(name => {
      jobs[name] = statuses[Math.floor(Math.random() * statuses.length)];
    });

    return jobs;
  },

  // Generate mock health data
  generateMockHealth() {
    const services = [
      { name: 'Backend API', status: 'healthy' },
      { name: 'Database', status: 'healthy' },
      { name: 'Redis Cache', status: 'healthy' },
      { name: 'Cloud Run', status: 'healthy' },
      { name: 'Firestore', status: 'healthy' },
      { name: 'Auth Service', status: 'healthy' }
    ];

    return services.map(service => ({
      ...service,
      message: service.status === 'healthy' ? 'Operational' : 'Degraded',
      lastCheck: new Date()
    }));
  }
};

// ════════════════════════════════════════════════════════════
// 6. TERMINAL MODULE
// ════════════════════════════════════════════════════════════
const Terminal = {
  open(jobId, status) {
    const modal = document.getElementById('terminalModal');
    const title = document.getElementById('terminalTitle');
    const body = document.getElementById('terminalBody');
    
    title.textContent = `logs/${jobId}.log`;
    modal.classList.remove('hidden');
    body.innerHTML = `<div class="t-line t-info">> [SYSTEM] Fetching logs for ${jobId}...</div>`;

    this.fetchLogs(jobId, status);
  },

  async fetchLogs(jobId, status) {
    const body = document.getElementById('terminalBody');
    
    try {
      // Try to fetch real logs
      const response = await fetch(`${RAW_URL}/logs/ci/latest.md?t=${Date.now()}`);
      if (response.ok) {
        const text = await response.text();
        body.innerHTML = '';
        
        const lines = text.split('\n').slice(0, 30);
        lines.forEach(line => {
          if (!line.trim()) return;
          const div = document.createElement('div');
          div.className = `t-line ${line.includes('Failed') || line.includes('Error') ? 't-error' : ''}`;
          div.innerText = `> ${line}`;
          body.appendChild(div);
        });
      } else {
        throw new Error('Logs not found');
      }
    } catch (error) {
      // Show mock logs on error
      body.innerHTML = `
        <div class="t-line t-info">> [SYSTEM] Job: ${jobId}</div>
        <div class="t-line">> [SYSTEM] Status: ${status.toUpperCase()}</div>
        <div class="t-line">> [SYSTEM] Timestamp: ${Utils.formatDate(new Date())}</div>
        <div class="t-line t-info">> [INFO] Starting deployment process...</div>
        <div class="t-line">> [INFO] Pulling Docker image...</div>
        <div class="t-line">> [INFO] Image pulled successfully</div>
        <div class="t-line">> [INFO] Deploying to Cloud Run...</div>
        <div class="t-line t-success">> [SUCCESS] Deployment completed</div>
        <div class="t-line">> [SYSTEM] Total time: 45s</div>
      `;
    }
    
    body.scrollTop = body.scrollHeight;
  },

  close() {
    document.getElementById('terminalModal').classList.add('hidden');
  }
};

// ════════════════════════════════════════════════════════════
// 7. QUICK ACTIONS & GOD MODE
// ════════════════════════════════════════════════════════════
const Actions = {
  async trigger(actionType) {
    if (!AppState.auth.isAuthenticated) {
      Auth.showModal();
      return;
    }

    const confirmMessage = `Execute critical action: ${actionType.toUpperCase()}?`;
    if (!confirm(confirmMessage)) return;

    try {
      // Try backend API
      if (CONFIG.API_BASE) {
        const result = await DataService.fetch(`/api/admin/actions/${actionType}`, {
          method: 'POST'
        });
        Utils.notify(`Action ${actionType} completed successfully`, 'success');
        return result;
      }

      // Demo mode - simulate action
      Utils.notify(`Action ${actionType} triggered (demo mode)`, 'success');
      console.log(`[Actions] ${actionType} triggered at ${new Date().toISOString()}`);
    } catch (error) {
      Utils.handleError(error, `Action ${actionType}`);
    }
  },

  async toggleGodMode(ruleName, isEnabled) {
    if (!AppState.auth.isAuthenticated) {
      Auth.showModal();
      return;
    }

    try {
      const message = isEnabled ? 
        `ENABLE ${ruleName}?` : 
        `DISABLE ${ruleName}?`;
      
      if (!confirm(message)) {
        // Revert toggle
        event.target.checked = !isEnabled;
        return;
      }

      // Try backend API
      if (CONFIG.API_BASE) {
        await DataService.fetch('/api/admin/rules', {
          method: 'POST',
          body: JSON.stringify({
            key: ruleName,
            value: isEnabled ? 'true' : 'false'
          })
        });
      }

      Utils.notify(`${ruleName} updated successfully`, 'success');
      console.log(`[GodMode] ${ruleName} = ${isEnabled}`);
    } catch (error) {
      Utils.handleError(error, 'Rule update');
      event.target.checked = !isEnabled;
    }
  }
};

// Helper function for job name formatting
function formatJobName(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// ════════════════════════════════════════════════════════════
// 8. NAVIGATION & UI CONTROLLERS
// ════════════════════════════════════════════════════════════
const Navigation = {
  init() {
    // Nav item clicks
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchView(e.currentTarget.getAttribute('data-target'));
      });
    });

    // Tab filters
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const filter = e.target.getAttribute('data-filter');
        this.setFilter(filter);
      });
    });
  },

  switchView(viewId) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update view sections
    document.querySelectorAll('.view-section').forEach(section => {
      section.classList.add('hidden');
    });
    document.getElementById(viewId).classList.remove('hidden');

    AppState.ui.activeView = viewId;
  },

  setFilter(filter) {
    AppState.ui.jobFilter = filter;

    // Update active tab
    document.querySelectorAll('.tab').forEach(tab => {
      tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Re-render jobs with filter
    DataService.renderJobs();
  }
};

// ════════════════════════════════════════════════════════════
// 9. INITIALIZATION
// ════════════════════════════════════════════════════════════
const App = {
  init() {
    console.log('🚀 SupremeAI Light Admin Dashboard initializing...');

    // Initialize theme
    Theme.init();

    // Check authentication
    if (!Auth.check()) {
      // Show auth modal after a short delay
      setTimeout(() => Auth.showModal(), 1000);
    }

    // Initialize navigation
    Navigation.init();

    // Bind event listeners
    this.bindEvents();

    // Load initial data
    DataService.refreshAll();

    // Start auto-refresh
    this.startAutoRefresh();

    console.log('✅ Dashboard initialized successfully');
  },

  bindEvents() {
    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', () => {
      Theme.toggle();
    });

    // Refresh button
    document.getElementById('btnRefresh').addEventListener('click', () => {
      DataService.refreshAll();
      
      // Animate sync dot
      const syncDot = document.querySelector('.sync-dot');
      syncDot.style.animation = 'none';
      setTimeout(() => {
        syncDot.style.animation = 'pulse 2s infinite';
      }, 100);
    });

    // Auth modal
    document.getElementById('authToken').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        Auth.submit(e.target.value);
      }
    });

    // Close modals on overlay click
    document.getElementById('terminalModal').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) {
        Terminal.close();
      }
    });

    document.getElementById('authModal').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) {
        Auth.hideModal();
      }
    });

    // God mode toggles
    document.getElementById('toggleAdminAuth').addEventListener('change', (e) => {
      Actions.toggleGodMode('admin_authorized', e.target.checked);
    });

    document.getElementById('toggleAutoFix').addEventListener('change', (e) => {
      Actions.toggleGodMode('autofix_authorized', e.target.checked);
    });

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', Utils.debounce((e) => {
      this.handleSearch(e.target.value);
    }, 300));
  },

  handleSearch(query) {
    console.log('Search:', query);
    // Implement search functionality
    // This can filter jobs, metrics, etc.
  },

  startAutoRefresh() {
    setInterval(() => {
      if (AppState.auth.isAuthenticated && !AppState.ui.isLoading) {
        DataService.refreshAll();
      }
    }, CONFIG.POLL_INTERVAL);
  }
};

// Start the application when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => App.init());
} else {
  App.init();
}

// Expose for debugging
window.App = App;
window.AppState = AppState;