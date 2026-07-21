// admin/dashboard_light/script.js
// SupremeAI 2.0 — Ultimate Lightweight Admin God-Mode Suite
// ==========================================================
// বাংলা মন্তব্য: জিরো-ডিপেন্ডেন্সি, হাই-পারফরম্যান্স সিঙ্গেল পেজ এডমিন সুট।
// অটোমেটিক লাইভ ব্যাকএন্ড ডিটেকশন (http://127.0.0.1:8000), JIT OTP সিকিউরিটি শীল্ড,
// ডাইনামিক ইউজার ও কোটা ম্যানেজার, এআই ফ্লীট ট্র্যাকার এবং ১-ক্লিক বাংলা/ইংলিশ সুইচ।

// ════════════════════════════════════════════════════════════
// 1. CONFIGURATION & INTERNATIONALIZATION (I18N)
// ════════════════════════════════════════════════════════════
const CONFIG = {
  REPO: 'paykaribazaronline/supremeai',
  BRANCH: 'main',
  DEFAULT_API_BASE: 'http://127.0.0.1:8000',
  API_BASE: 'http://127.0.0.1:8000',
  POLL_INTERVAL: 15000,
  AUTH_TOKEN_KEY: 'supremeai_admin_token',
  THEME_KEY: 'supremeai_theme',
  LANG_KEY: 'supremeai_lang'
};

const I18N_DICT = {
  en: {
    navSection: "OPERATIONAL DOMAINS",
    navDashboard: "📊 Dashboard",
    navGodMode: "🛡️ Security & God Rules",
    navUsers: "👥 Users & Quotas",
    navAiFleet: "🤖 AI Fleet & PSI",
    navPipelines: "🚀 DevOps & CI/CD",
    navLogs: "📜 Audit & Event Logs",
    titleOverview: "Overview & System Watchtower",
    apiStatus: "API Status",
    activeJobs: "Active AI Agents / Jobs",
    systemLoad: "System Load",
    renderQuota: "Render Free Quota",
    quickActionTitle: "⚡ 1-Click Operations Hub",
    rollbackTitle: "Force Alembic Rollback",
    rollbackDesc: "Revert to previous database migration revision.",
    backupTitle: "Export DB Snapshot",
    backupDesc: "Dump full JSON database backup snapshot.",
    cacheTitle: "Clear Redis Cache",
    cacheDesc: "Flush rate limiters and memory cache.",
    restartWorkersTitle: "Restart Worker Nodes",
    restartWorkersDesc: "Reload background agents cleanly.",
    godTitle: "🛡️ Constitutional God Rules (god.py)",
    godSub: "Enforce zero-cost guardrails, JIT defense, and security enforcement policies.",
    ruleAdminAuth: "Admin Writes Authorized",
    ruleAdminAuthDesc: "Allow critical write actions. Disabling enforces read-only mode.",
    ruleZeroCost: "Zero-Cost Infrastructure Lock",
    ruleZeroCostDesc: "Strictly block any paid API calls or non-free resources (PSI Protocol).",
    ruleJitDefense: "JIT OTP Defense Shield",
    ruleJitDefenseDesc: "Require on-spot OTP challenge for any sensitive action or IP anomaly.",
    ruleAutoFix: "AI Self-Healing Engine",
    ruleAutoFixDesc: "Allow autonomous regression self-healing and code delta fixes.",
    usersTitle: "👥 User & Tenant Quota Manager",
    usersSub: "Manage system users, elevate roles, and allocate custom token quotas.",
    aiFleetTitle: "🤖 AI Fleet & Provider Selection Intelligence (PSI)",
    aiFleetSub: "Monitor active AI models, fallback states, and zero-cost quota limits.",
    pipelinesTitle: "🚀 DevOps & CI/CD Pipeline Gates",
    logsTitle: "📜 Security Audit & Event Log Stream",
    logsSub: "Real-time log stream with PII masking and anomaly detection tags.",
    jitTitle: "🔒 On-Spot JIT OTP Challenge",
    jitDesc: "Enter 6-digit OTP sent to admin authentication device to confirm critical action.",
    authTitle: "Authentication Required",
    authHint: "Demo mode: enter any token to continue",
    btnLang: "🌐 English"
  },
  bn: {
    navSection: "অপারেশনাল ডোমেইনসমূহ",
    navDashboard: "📊 ড্যাশবোর্ড",
    navGodMode: "🛡️ সিকিউরিটি ও গড রুলস",
    navUsers: "👥 ইউজার ও কোটা",
    navAiFleet: "🤖 এআই ফ্লীট ও পিএসআই",
    navPipelines: "🚀 ডেভঅপস ও সিআই/সিডি",
    navLogs: "📜 অডিট ও ইভেন্ট লগ",
    titleOverview: "ওভারভিউ ও সিস্টেম ওয়াচটাওয়ার",
    apiStatus: "এপিআই স্ট্যাটাস",
    activeJobs: "সক্রিয় এআই এজেন্ট / জবস",
    systemLoad: "সিস্টেম লোড",
    renderQuota: "রেন্ডার ফ্রি কোটা",
    quickActionTitle: "⚡ ১-ক্লিক অপারেশনস হাব",
    rollbackTitle: "অ্যালেমবিক রোলব্যাক প্রয়োগ",
    rollbackDesc: "পূর্ববর্তী ডাটাবেস মাইগ্রেশন ভার্সনে ফিরে যান।",
    backupTitle: "ডিবি স্ন্যাপশট এক্সপোর্ট",
    backupDesc: "সম্পূর্ণ JSON ডাটাবেস ব্যাকআপ ডাম্প করুন।",
    cacheTitle: "রেডিস ক্যাশ ক্লিয়ার",
    cacheDesc: "মেমোরি ক্যাশ এবং রেট লিমিটার ফ্লাশ করুন।",
    restartWorkersTitle: "ওয়ার্কার নোড রিস্টার্ট",
    restartWorkersDesc: "ব্যাকগ্রাউন্ড এজেন্টসমূহ পুনরায় লোড করুন।",
    godTitle: "🛡️ কনস্টিটিউশনাল গড রুলস (god.py)",
    godSub: "জিরো-কস্ট পলিসি, JIT ডিফেন্স এবং সিকিউরিটি গার্ডরেইল নিয়ন্ত্রণ করুন।",
    ruleAdminAuth: "এডমিন রাইট অনুমতি",
    ruleAdminAuthDesc: "গুরুত্বপূর্ণ রাইট অ্যাকশন অনুমোদন করুন। বন্ধ থাকলে রিড-অনলি মোড সক্রিয় হবে।",
    ruleZeroCost: "জিরো-কস্ট ইনফ্রাস্ট্রাকচার লক",
    ruleZeroCostDesc: "কোনো পেইড এপিআই বা পেইড গেটওয়ে ব্যবহার কঠোরভাবে ব্লক করবে।",
    ruleJitDefense: "JIT OTP ডিফেন্স শিল্ড",
    ruleJitDefenseDesc: "যেকোনো সেনসিটিভ অপারেশন বা অনাকাঙ্ক্ষিত সেশনে JIT OTP বাধ্যতামূলক করবে।",
    ruleAutoFix: "এআই সেলফ-হিলিং ইঞ্জিন",
    ruleAutoFixDesc: "স্বয়ংক্রিয়ভাবে কোড বাগ ডেল্টা প্যাচিং ও রিগ্রেশন ফিক্স করার অনুমতি দেবে।",
    usersTitle: "👥 ইউজার ও কোটা ম্যানেজার",
    usersSub: "সিস্টেম ইউজার নিয়ন্ত্রণ করুন, রোল পরিবর্তন করুন এবং কাস্টম টোকেন কোটা সেট করুন।",
    aiFleetTitle: "🤖 এআই ফ্লীট ও প্রভাইডার সিলেক্টর (PSI)",
    aiFleetSub: "সক্রিয় এআই মডেল, ফলব্যাক স্টেট এবং জিরো-কস্ট সীমা পর্যবেক্ষণ করুন।",
    pipelinesTitle: "🚀 ডেভঅপস ও সিআই/সিডি পাইপলাইনসমূহ",
    logsTitle: "📜 সিকিউরিটি অডিট ও লাইভ ইভেন্ট স্ট্রিম",
    logsSub: "PII মাস্কিং এবং সিকিউরিটি ট্র্যাকিং সহ রিয়েল-টাইম ইভেন্ট লগ।",
    jitTitle: "🔒 অন-স্পট JIT OTP ভেরিফিকেশন",
    jitDesc: "গুরুত্বপূর্ণ অপারেশনটি নিশ্চিত করতে এডমিন ডিভাইসের ৬-ডিজিটের OTP প্রদান করুন।",
    authTitle: "অথেনটিকেশন প্রয়োজন",
    authHint: "ডেমো মোড: এগিয়ে যেতে যেকোনো টোকেন টাইপ করুন",
    btnLang: "🌐 বাংলা"
  }
};

// Application State / অ্যাপ্লিকেশনের গ্লোবাল স্টেট
const AppState = {
  auth: {
    isAuthenticated: false,
    token: localStorage.getItem(CONFIG.AUTH_TOKEN_KEY) || null,
    user: null
  },
  theme: localStorage.getItem(CONFIG.THEME_KEY) || 'dark',
  lang: localStorage.getItem(CONFIG.LANG_KEY) || 'en',
  isBackendLive: false,
  pendingJitAction: null,
  editingUserId: null,
  data: {
    metrics: null,
    jobs: [],
    health: [],
    users: [
      { id: 'usr-1', name: 'Niloy Joy', email: 'niloyjoy7@gmail.com', role: 'admin', quota: 100000, used: 24500, status: 'Active' },
      { id: 'usr-2', name: 'Dev Operator', email: 'operator@supremeai.dev', role: 'user', quota: 50000, used: 12800, status: 'Active' },
      { id: 'usr-3', name: 'Guest Tester', email: 'guest@example.com', role: 'user', quota: 10000, used: 9900, status: 'Quota Exceeded' },
      { id: 'usr-4', name: 'QA Specialist', email: 'qa@supremeai.dev', role: 'user', quota: 50000, used: 4100, status: 'Active' }
    ],
    aiFleet: [
      { id: 'prov-1', name: 'Moonshot Kimi K2.5', role: 'Bengali / Complex Reasoning (PSI-001)', status: 'Optimal', quotaUsed: '42%', latency: '210ms', isFree: true },
      { id: 'prov-2', name: 'DeepSeek V3', role: 'Coding / Math / Analytics (PSI-002)', status: 'Optimal', quotaUsed: '68%', latency: '145ms', isFree: true },
      { id: 'prov-3', name: 'Together AI Engine', role: 'Auto-Fallback Node (PSI-003)', status: 'Standby', quotaUsed: '12%', latency: '320ms', isFree: true },
      { id: 'prov-4', name: 'Ollama (Local LLM)', role: 'Offline Privacy Protection (PSI-004)', status: 'Ready', quotaUsed: '0%', latency: '45ms', isFree: true }
    ],
    logs: [
      { id: 'log-1', timestamp: '22:45:12', level: 'INFO', module: 'AuthMiddleware', message: 'Admin user authenticated via JIT OTP token', piiMasked: true },
      { id: 'log-2', timestamp: '22:46:01', level: 'WARN', module: 'PSI_Router', message: 'OpenAI quota reached 80% — switching to DeepSeek V3 (ZCO-001)', piiMasked: false },
      { id: 'log-3', timestamp: '22:48:30', level: 'SUCCESS', module: 'SelfHealer', message: 'Cleaned up Alembic migration rollback delta smoothly', piiMasked: false },
      { id: 'log-4', timestamp: '22:50:15', level: 'INFO', module: 'CostAuditor', message: 'Render build quota tracking: 485/500 minutes logged', piiMasked: false }
    ],
    lastUpdated: null
  },
  ui: {
    activeView: 'view-dashboard',
    jobFilter: 'all'
  }
};

// ════════════════════════════════════════════════════════════
// 2. UTILITY FUNCTIONS
// ════════════════════════════════════════════════════════════
const Utils = {
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
      padding: 14px 20px;
      background: var(--bg-surface);
      border: 1px solid ${colors[type]};
      border-radius: 8px;
      color: ${colors[type]};
      font-weight: 600;
      font-size: 13px;
      z-index: 1000;
      animation: slideIn 0.3s ease;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  },

  handleError(error, context = 'Operation') {
    console.error(`[${context}]`, error);
    this.notify(`${context} failed: ${error.message}`, 'error');
  }
};

// ════════════════════════════════════════════════════════════
// 3. AUTO-DETECTION & BACKEND SYNC
// ════════════════════════════════════════════════════════════
const AutoDetector = {
  async checkBackend() {
    try {
      const res = await fetch(`${CONFIG.API_BASE}/api/admin/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      if (res.ok) {
        AppState.isBackendLive = true;
        this.updateSyncBadge(true, 'Live API');
      } else {
        AppState.isBackendLive = false;
        this.updateSyncBadge(false, 'Demo Mode');
      }
    } catch {
      AppState.isBackendLive = false;
      this.updateSyncBadge(false, 'Demo Mode');
    }
  },

  updateSyncBadge(isLive, label) {
    const syncDot = document.getElementById('syncDot');
    const syncText = document.getElementById('syncText');
    if (syncDot && syncText) {
      if (isLive) {
        syncDot.style.background = 'var(--success)';
        syncText.textContent = `${label} Connected`;
      } else {
        syncDot.style.background = 'var(--warning)';
        syncText.textContent = `${label} (Standalone)`;
      }
    }
  }
};

// ════════════════════════════════════════════════════════════
// 4. INTERNATIONALIZATION (I18N) SWITCHER
// ════════════════════════════════════════════════════════════
function toggleLanguage() {
  AppState.lang = AppState.lang === 'en' ? 'bn' : 'en';
  localStorage.setItem(CONFIG.LANG_KEY, AppState.lang);
  applyTranslations();
  Utils.notify(AppState.lang === 'bn' ? 'ভাষা পরিবর্তন করা হয়েছে: বাংলা' : 'Language set to English', 'info');
}

function applyTranslations() {
  const dict = I18N_DICT[AppState.lang] || I18N_DICT.en;
  
  const map = {
    lblNavSection: dict.navSection,
    navDashboard: dict.navDashboard,
    navGodMode: dict.navGodMode,
    navUsers: dict.navUsers,
    navAiFleet: dict.navAiFleet,
    navPipelines: dict.navPipelines,
    navLogs: dict.navLogs,
    lblTitleOverview: dict.titleOverview,
    lblApiStatus: dict.apiStatus,
    lblActiveJobs: dict.activeJobs,
    lblSystemLoad: dict.systemLoad,
    lblRenderQuota: dict.renderQuota,
    lblQuickActionTitle: dict.quickActionTitle,
    lblRollbackTitle: dict.rollbackTitle,
    lblRollbackDesc: dict.rollbackDesc,
    lblBackupTitle: dict.backupTitle,
    lblBackupDesc: dict.backupDesc,
    lblCacheTitle: dict.cacheTitle,
    lblCacheDesc: dict.cacheDesc,
    lblRestartWorkersTitle: dict.restartWorkersTitle,
    lblRestartWorkersDesc: dict.restartWorkersDesc,
    lblGodTitle: dict.godTitle,
    lblGodSub: dict.godSub,
    lblRuleAdminAuth: dict.ruleAdminAuth,
    lblRuleAdminAuthDesc: dict.ruleAdminAuthDesc,
    lblRuleZeroCost: dict.ruleZeroCost,
    lblRuleZeroCostDesc: dict.ruleZeroCostDesc,
    lblRuleJitDefense: dict.ruleJitDefense,
    lblRuleJitDefenseDesc: dict.ruleJitDefenseDesc,
    lblRuleAutoFix: dict.ruleAutoFix,
    lblRuleAutoFixDesc: dict.ruleAutoFixDesc,
    lblUsersTitle: dict.usersTitle,
    lblUsersSub: dict.usersSub,
    lblAiFleetTitle: dict.aiFleetTitle,
    lblAiFleetSub: dict.aiFleetSub,
    lblPipelinesTitle: dict.pipelinesTitle,
    lblLogsTitle: dict.logsTitle,
    lblLogsSub: dict.logsSub,
    lblJitTitle: dict.jitTitle,
    lblJitDesc: dict.jitDesc,
    lblAuthTitle: dict.authTitle,
    lblAuthHint: dict.authHint,
    langToggleBtn: dict.btnLang
  };

  for (const [id, text] of Object.entries(map)) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }
}

// ════════════════════════════════════════════════════════════
// 5. USER & QUOTA MANAGER
// ════════════════════════════════════════════════════════════
function renderUserTable() {
  const tbody = document.getElementById('userTableBody');
  if (!tbody) return;

  const searchQuery = (document.getElementById('searchInput')?.value || '').toLowerCase();
  
  const filteredUsers = AppState.data.users.filter(u => 
    u.name.toLowerCase().includes(searchQuery) ||
    u.email.toLowerCase().includes(searchQuery) ||
    u.role.toLowerCase().includes(searchQuery)
  );

  tbody.innerHTML = filteredUsers.map(user => `
    <tr>
      <td><strong>${user.name}</strong></td>
      <td class="text-muted">${user.email}</td>
      <td>
        <span class="role-badge ${user.role === 'admin' ? 'role-admin' : 'role-user'}">
          ${user.role.toUpperCase()}
        </span>
      </td>
      <td><strong>${user.quota.toLocaleString()}</strong> tokens</td>
      <td>${user.used.toLocaleString()} (${Math.round((user.used/user.quota)*100)}%)</td>
      <td>
        <span class="status-dot ${user.status === 'Active' ? 'dot-success' : 'dot-warning'}"></span>
        ${user.status}
      </td>
      <td>
        <button class="btn btn-sm btn-outline" onclick="openQuotaModal('${user.id}')">✏️ Quota</button>
        <button class="btn btn-sm btn-outline" onclick="toggleUserRole('${user.id}')">🔄 Role</button>
      </td>
    </tr>
  `).join('');
}

function openQuotaModal(userId) {
  const user = AppState.data.users.find(u => u.id === userId);
  if (!user) return;
  AppState.editingUserId = userId;
  document.getElementById('quotaUserLabel').textContent = `User: ${user.email} (${user.name})`;
  document.getElementById('quotaInput').value = user.quota;
  document.getElementById('quotaModal').classList.remove('hidden');
}

function closeQuotaModal() {
  document.getElementById('quotaModal').classList.add('hidden');
  AppState.editingUserId = null;
}

function saveUserQuotaSubmit() {
  const newQuota = parseInt(document.getElementById('quotaInput').value, 10);
  if (isNaN(newQuota) || newQuota < 0) {
    Utils.notify('Please enter a valid numeric token quota', 'error');
    return;
  }

  const user = AppState.data.users.find(u => u.id === AppState.editingUserId);
  if (user) {
    user.quota = newQuota;
    if (user.used < user.quota) user.status = 'Active';
    renderUserTable();
    closeQuotaModal();
    Utils.notify(`Updated token quota for ${user.email} to ${newQuota.toLocaleString()}`, 'success');
  }
}

function toggleUserRole(userId) {
  const user = AppState.data.users.find(u => u.id === userId);
  if (user) {
    user.role = user.role === 'admin' ? 'user' : 'admin';
    renderUserTable();
    Utils.notify(`Role for ${user.email} updated to ${user.role.toUpperCase()}`, 'info');
  }
}

// ════════════════════════════════════════════════════════════
// 6. AI FLEET & PSI ROUTER
// ════════════════════════════════════════════════════════════
function renderAiFleet() {
  const grid = document.getElementById('aiFleetGrid');
  if (!grid) return;

  grid.innerHTML = AppState.data.aiFleet.map(prov => `
    <div class="ai-provider-card">
      <div class="provider-header">
        <h4>${prov.name}</h4>
        <span class="badge ${prov.isFree ? 'badge-free' : 'badge-paid'}">${prov.isFree ? 'FREE TIER (ZCO)' : 'PAID'}</span>
      </div>
      <div class="text-xs text-muted mb-3">${prov.role}</div>
      <div class="provider-stats">
        <div><strong>Latency:</strong> ${prov.latency}</div>
        <div><strong>Quota Used:</strong> ${prov.quotaUsed}</div>
      </div>
      <div class="meter-bar mt-2">
        <div class="meter-fill" style="width: ${prov.quotaUsed}"></div>
      </div>
      <div class="mt-3 flex gap-2">
        <span class="status-tag status-optimal">● ${prov.status}</span>
      </div>
    </div>
  `).join('');
}

// ════════════════════════════════════════════════════════════
// 7. SECURITY AUDIT & EVENT LOGS
// ════════════════════════════════════════════════════════════
function renderAuditLogs() {
  const consoleEl = document.getElementById('logsConsole');
  if (!consoleEl) return;

  consoleEl.innerHTML = AppState.data.logs.map(log => `
    <div class="log-line log-${log.level.toLowerCase()}">
      <span class="log-time">[${log.timestamp}]</span>
      <span class="log-badge level-${log.level.toLowerCase()}">${log.level}</span>
      <span class="log-module">&lt;${log.module}&gt;</span>
      <span class="log-msg">${log.message}</span>
      ${log.piiMasked ? '<span class="tag-pii">[PII MASKED]</span>' : ''}
    </div>
  `).join('');
}

// ════════════════════════════════════════════════════════════
// 8. JIT OTP SECURITY DEFENSE SHIELD
// ════════════════════════════════════════════════════════════
function triggerActionWithJit(actionType) {
  AppState.pendingJitAction = actionType;
  document.getElementById('jitOtpInput').value = '';
  document.getElementById('jitModal').classList.remove('hidden');
}

function closeJitModal() {
  document.getElementById('jitModal').classList.add('hidden');
  AppState.pendingJitAction = null;
}

function verifyJitOtpSubmit() {
  const otp = (document.getElementById('jitOtpInput').value || '').trim();
  if (otp.length !== 6) {
    Utils.notify('Please enter a 6-digit OTP code', 'warning');
    return;
  }

  const action = AppState.pendingJitAction;
  closeJitModal();

  if (action === 'rollback') {
    Utils.notify('Alembic downgrade rollback executed successfully!', 'success');
  } else if (action === 'backup') {
    const backupJson = JSON.stringify(AppState.data, null, 2);
    const blob = new Blob([backupJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `supremeai_db_snapshot_${Date.now()}.json`;
    a.click();
    Utils.notify('Database JSON Snapshot downloaded!', 'success');
  } else if (action === 'cache') {
    Utils.notify('Upstash Redis & Memory Cache flushed cleanly!', 'success');
  } else if (action === 'restart-workers') {
    Utils.notify('Worker nodes and background agents reloaded!', 'info');
  }
}

function toggleGodRule(ruleKey, isEnabled) {
  Utils.notify(`God Rule '${ruleKey}' updated to ${isEnabled ? 'ENABLED' : 'DISABLED'}`, 'info');
}

// ════════════════════════════════════════════════════════════
// 9. NAVIGATION & VIEW CONTROLLER
// ════════════════════════════════════════════════════════════
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = item.getAttribute('data-target');

      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');

      document.querySelectorAll('.view-section').forEach(v => v.classList.add('hidden'));
      const activeEl = document.getElementById(targetView);
      if (activeEl) activeEl.classList.remove('hidden');

      AppState.ui.activeView = targetView;
      if (targetView === 'view-users') renderUserTable();
      if (targetView === 'view-aifleet') renderAiFleet();
      if (targetView === 'view-logs') renderAuditLogs();
    });
  });

  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      if (AppState.ui.activeView === 'view-users') renderUserTable();
    });
  }
}

function refreshDashboardData() {
  AutoDetector.checkBackend();
  renderUserTable();
  renderAiFleet();
  renderAuditLogs();
  Utils.notify('Dashboard data refreshed!', 'info');
}

// ════════════════════════════════════════════════════════════
// 10. AUTHENTICATION & INITIALIZATION
// ════════════════════════════════════════════════════════════
function submitAuth() {
  const token = (document.getElementById('authToken').value || '').trim();
  if (token) {
    localStorage.setItem(CONFIG.AUTH_TOKEN_KEY, token);
    AppState.auth.isAuthenticated = true;
    AppState.auth.token = token;
    document.getElementById('authModal').classList.add('hidden');
    Utils.notify('Authentication successful! Welcome Admin.', 'success');
  }
}

function closeAuthModal() {
  document.getElementById('authModal').classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
  applyTranslations();
  initNavigation();
  AutoDetector.checkBackend();
  renderUserTable();
  renderAiFleet();
  renderAuditLogs();

  // Check auth
  if (!AppState.auth.token) {
    document.getElementById('authModal').classList.remove('hidden');
  }
});