// Centralized auth-token storage — FE-04 remediation, step 1 (Issue #521).
//
// বাংলা: নিরাপত্তা অডিট FE-04 অনুযায়ী auth token আর localStorage-এ স্থায়ীভাবে জমা
// হবে না। এখন থেকে টোকেন শুধু sessionStorage-এ (ট্যাব বন্ধ হলেই মুছে যায় — XSS
// exposure উইন্ডো অনেক ছোট) + মেমোরিতে থাকে। পুরনো (legacy) localStorage টোকেন
// পড়ার সময় sessionStorage-এ মাইগ্রেট করে localStorage থেকে মুছে ফেলা হয়, তাই
// আগের ডিপ্লয়মেন্টের সেশনও নিরাপদে চলতে থাকবে।
//
// চূড়ান্ত লক্ষ্য (issue #521-এর suggested fix): টোকেন সম্পূর্ণভাবে HttpOnly cookie-তে
// যাওয়া — backend ইতিমধ্যেই login-এ supreme_access_token/supreme_refresh_token
// httpOnly cookie সেট করে এবং /auth/me cookie-session restore সমর্থন করে। এই মডিউল
// সেই ট্রানজিশনের প্রথম (frontend-only) ধাপ।
//
// Residual risk: sessionStorage ও মেমোরি উভয়ই একই পেজের XSS payload পড়তে পারে —
// এই ধাপ exposure-এর সময়সীমা (lifetime) কমায়, XSS-এর বিরুদ্ধে সম্পূর্ণ সুরক্ষা নয়।
// সম্পূর্ণ ফিক্সের জন্য httpOnly cookie + refresh-rotation দরকার (backend প্রস্তুত)।

const USER_TOKEN_KEY = 'supremeai_auth_token';
export const USER_TOKEN_STORAGE_KEY = USER_TOKEN_KEY;
const ADMIN_TOKEN_KEY = 'supreme_admin_jwt';
export const ADMIN_TOKEN_STORAGE_KEY = ADMIN_TOKEN_KEY;

const hasStorage = (s: Storage | undefined): s is Storage => Boolean(s);

const getSession = (): Storage | undefined => {
  try {
    return typeof window === 'undefined' ? undefined : window.sessionStorage;
  } catch {
    return undefined;
  }
};

const getLocal = (): Storage | undefined => {
  try {
    return typeof window === 'undefined' ? undefined : window.localStorage;
  } catch {
    return undefined;
  }
};

/**
 * Read a token: sessionStorage first, then a legacy localStorage entry.
 *
 * বাংলা: legacy localStorage টোকেন পেলে সেটি sessionStorage-এ কপি করে localStorage
 * থেকে মুছে ফেলা হয় (one-time migration sweep) — পুরনো সেশন নতুন নিয়মে চলে।
 */
const readToken = (key: string): string | null => {
  const session = getSession();
  if (hasStorage(session)) {
    try {
      const cached = session.getItem(key);
      if (cached) return cached;
    } catch {
      // sessionStorage unavailable (privacy mode / SSR) — নীরবে এগোনো।
    }
  }

  const local = getLocal();
  if (hasStorage(local)) {
    try {
      const legacy = local.getItem(key);
      if (legacy) {
        if (hasStorage(session)) {
          try {
            session.setItem(key, legacy);
          } catch {
            // Migration best-effort — টোকেন যেখানে আছে সেখানেই ব্যবহারযোগ্য।
          }
        }
        local.removeItem(key);
        return legacy;
      }
    } catch {
      // localStorage unavailable — নীরবে এগোনো।
    }
  }

  return null;
};

/** বাংলা: টোকেন শুধু sessionStorage-এ লেখা হয় — localStorage আর কখনো লেখা হবে না। */
const writeToken = (key: string, token: string): void => {
  const session = getSession();
  if (hasStorage(session)) {
    try {
      session.setItem(key, token);
    } catch {
      // sessionStorage full/unavailable — টোকেন মেমোরিতে (updateTokenCache) থাকবে।
    }
  }
};

/** বাংলা: দুই স্টোর থেকেই মুছে ফেলা হয় (localStorage মানে legacy sweep)। */
const clearToken = (key: string): void => {
  const session = getSession();
  if (hasStorage(session)) {
    try {
      session.removeItem(key);
    } catch {
      // নীরবে এগোনো।
    }
  }
  const local = getLocal();
  if (hasStorage(local)) {
    try {
      local.removeItem(key);
    } catch {
      // নীরবে এগোনো।
    }
  }
};

// ── User session token (supremeai_auth_token) ──────────────────────────────

export const getUserToken = (): string | null => readToken(USER_TOKEN_KEY);

export const setUserToken = (token: string): void => writeToken(USER_TOKEN_KEY, token);

export const clearUserToken = (): void => clearToken(USER_TOKEN_KEY);

// ── Admin step-up JWT (supreme_admin_jwt) ──────────────────────────────────

export const getAdminToken = (): string | null => readToken(ADMIN_TOKEN_KEY);

export const setAdminToken = (token: string): void => writeToken(ADMIN_TOKEN_KEY, token);

export const clearAdminToken = (): void => clearToken(ADMIN_TOKEN_KEY);
