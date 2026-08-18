// frontend/src/store/slices/adminAuthHelpers.ts
// বাংলা মন্তব্য: M0.2 — adminStore.ts-এর auth helpers (decodeJwt, isTokenExpired,
// restoreAdminSession, buildProvisioningUri) এখানে এক্সট্র্যাক্ট করা হয়েছে
// যাতে adminSlice.ts আর adminStore.ts (backward-compat shim) দুজনেই ব্যবহার করতে পারে।

export const decodeJwt = (token: string): Record<string, unknown> | null => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64).split('').map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''),
    );
    const decoded = JSON.parse(jsonPayload);

    if (!decoded || typeof decoded !== 'object') {
      throw new Error('Decoded JWT payload is not a valid object');
    }

    return decoded;
  } catch (e: unknown) {
    console.warn('⚠️ [JWT_DECODE_LEAK]: Failed to safely parse admin JWT token.', {
      error_message: e instanceof Error ? e.message : String(e),
      token_length: token.length,
      timestamp: new Date().toISOString(),
      token_preview: token.substring(0, 20) + '...',
    });
    return null;
  }
};

export const isTokenExpired = (decoded: Record<string, unknown> | null): boolean => {
  if (!decoded || typeof decoded !== 'object') return true;
  const exp = decoded.exp;
  if (typeof exp !== 'number') return true;
  const now = Math.floor(Date.now() / 1000);
  return exp < now;
};

export const restoreAdminSession = (): { adminAuthenticated: boolean; adminRole: string | null } => {
  if (typeof window === 'undefined') return { adminAuthenticated: false, adminRole: null };
  const token = localStorage.getItem('supreme_admin_jwt');
  if (!token) return { adminAuthenticated: false, adminRole: null };
  const decoded = decodeJwt(token);
  if (!decoded || isTokenExpired(decoded)) {
    localStorage.removeItem('supreme_admin_jwt');
    localStorage.removeItem('adminToken');
    localStorage.removeItem('supremeai_auth_token');
    return { adminAuthenticated: false, adminRole: null };
  }
  const role = typeof decoded.role === 'string' ? decoded.role : null;
  return { adminAuthenticated: true, adminRole: role };
};

export const buildProvisioningUri = (email: string, secret: string): string =>
  `otpauth://totp/SupremeAI:${encodeURIComponent(email)}?secret=${secret}&issuer=SupremeAI&digits=6&period=30`;
