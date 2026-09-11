// apps/studio-client/src/services/adminTokenStore.ts
// 🚨 CRITICAL CHECK: No external imports allowed here to bypass Vite Rollup blocks

const readAdminToken = (): string | null => {
  // Keep the viewer simple: accept the existing session token first, then
  // support the legacy local token used by older sessions and integrations.
  return sessionStorage.getItem('supreme_admin_jwt') ?? localStorage.getItem('supreme_admin_jwt');
};

export const adminTokenStore = {
  getRawToken: (): string | null => {
    return readAdminToken();
  },
  getDecodedToken: (): Record<string, unknown> | null => {
    const token = readAdminToken();
    if (!token) return null;

    try {
      // 🛡️ Zero-Dependency Pure Native JWT Decoder
      const tokenParts = token.split('.');
      if (tokenParts.length !== 3) {
        throw new Error("Malformed JWT string structure.");
      }

      const base64Url = tokenParts[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');

      // UTF-8 Compliant Native Base64 Parsing
      const jsonPayload = decodeURIComponent(
        window.atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );

      return JSON.parse(jsonPayload);
    } catch (error: unknown) {
      const errObj = error as { message?: string };
      console.warn("⚠️ [TOKEN_STORE_LEAK]: Failed to safely parse or decode admin JWT token natively.", {
        error_message: errObj?.message || 'Invalid base64 payload matrix',
        token_length: token.length,
        timestamp: new Date().toISOString()
      });

      return null;
    }
  }
};
