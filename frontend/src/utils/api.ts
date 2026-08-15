// বাংলা মন্তব্য: Portal-ভিত্তিক একক backend নির্ধারণ — কোনো cross-portal failover নেই।
// Admin build (VITE_PORTAL_TYPE=admin) শুধু Admin backend-এ কথা বলে, User build শুধু User backend-এ।
// Firebase hosting external rewrite proxy সাপোর্ট করে না, তাই Firebase-এ সরাসরি backend URL ব্যবহার হয় (CORS allow)।
// Vercel-এ relative path ('') রাখা হয় কারণ Vercel external rewrite proxy সাপোর্ট করে।

/** Admin portal-এর canonical backend URL (build-time resolved) */
export const ADMIN_BACKEND_URL: string =
  import.meta.env.VITE_ADMIN_BACKEND || 'https://supremeai-admin.onrender.com';

/** User portal-এর canonical backend URL (build-time resolved) */
export const USER_BACKEND_URL: string =
  import.meta.env.VITE_USER_BACKEND ||
  import.meta.env.VITE_API_BASE ||
  import.meta.env.VITE_API_URL ||
  'https://supremeai-backend.onrender.com';

/**
 * বর্তমান portal-এর canonical backend URL — heartbeat ও অন্যান্য সার্ভিস এটিই ব্যবহার করে।
 * বাংলা মন্তব্য: runtime hostname sniffing নয়, build-time VITE_PORTAL_TYPE দিয়ে নির্ধারিত।
 */
export const BACKEND_URL: string =
  import.meta.env.VITE_PORTAL_TYPE === 'admin' ? ADMIN_BACKEND_URL : USER_BACKEND_URL;

/**
 * @deprecated পুরনো failover array — শুধু backward compatibility-র জন্য readonly রাখা হয়েছে।
 * নতুন কোডে কখনোই এটি ব্যবহার করবেন না; সবসময় `BACKEND_URL` ব্যবহার করুন।
 * বাংলা মন্তব্য: index দিয়ে অন্য portal-এর backend বেছে নিলে আইসোলেশন ভেঙে যাবে।
 */
export const RENDER_BACKENDS: readonly string[] = [USER_BACKEND_URL, ADMIN_BACKEND_URL] as const;

// বাংলা মন্তব্য: switchActiveBackend() সরানো হয়েছে — user→admin (বা উল্টো) failover
// আর্কিটেকচারাল আইসোলেশন ভাঙত এবং CORS/RBAC ঝুঁকি তৈরি করত।
// নেটওয়ার্ক ব্যর্থতা বা 502/503/504-এ apiClient একই URL-এ backoff retry করে।

export const getApiBaseUrl = (): string => {
  if (typeof window === 'undefined') {
    // বাংলা মন্তব্য: SSR/Node.js কনটেক্সটে সরাসরি backend URL
    if (!BACKEND_URL && import.meta.env.PROD) throw new Error('API URL missing in production');
    return BACKEND_URL;
  }

  const hostname = window.location.hostname;

  // 🔥 ফিক্স: Firebase Hosting rewrite দিয়ে external URL-এ proxy করা যায় না,
  // তাই Firebase (.web.app/.firebaseapp.com)-এ সরাসরি portal-নির্দিষ্ট backend URL ব্যবহার করি।
  // Backend CORS ইতিমধ্যে supremeai-admin.web.app allow করে রেখেছে।
  // Vercel (vercel.app) external rewrite proxy সাপোর্ট করে, তাই সেখানে relative path রাখি।
  if (hostname.includes('vercel.app')) {
    return '';
  }

  // Firebase ও বাকি হোস্টে (local dev ইত্যাদি) সরাসরি backend URL
  return BACKEND_URL;
};

export const getWebSocketBaseUrl = (): string => {
  // বাংলা মন্তব্য: এক্সপ্লিসিট override সবার আগে
  if (import.meta.env.VITE_WS_BASE_URL) {
    return import.meta.env.VITE_WS_BASE_URL;
  }

  const apiBase = getApiBaseUrl();

  // 🔥 ফিক্স: Firebase hosting-এ apiBase === '' (relative path)।
  // WebSocket Firebase rewrite proxy দিয়ে যায় না — সরাসরি Render-এর wss:// URL ব্যবহার করতে হবে।
  if (apiBase === '') {
    return BACKEND_URL.replace(/^https:\/\//, 'wss://');
  }

  if (apiBase.startsWith('https://')) {
    return apiBase.replace(/^https:\/\//, 'wss://');
  }
  if (apiBase.startsWith('http://')) {
    return apiBase.replace(/^http:\/\//, 'ws://');
  }

  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = typeof window !== 'undefined' ? window.location.host : 'localhost:8000';
  return `${protocol}//${host}`;
};
