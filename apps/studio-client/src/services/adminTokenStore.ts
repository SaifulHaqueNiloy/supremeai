// apps/studio-client/src/services/adminTokenStore.ts
import { jwtDecode } from 'jwt-decode';

export const adminTokenStore = {
  /**
   * Decodes and validates admin JWT token from localStorage
   * @returns Decoded token payload or null with comprehensive diagnostic logging
   */
  getDecodedToken: (): any | null => {
    const token = localStorage.getItem('supreme_admin_jwt');
    if (!token) {
      console.debug("🔍 [TOKEN_STORE] No admin JWT token found in storage");
      return null;
    }

    try {
      const decoded = jwtDecode(token);

      // Additional validation: ensure token has required structure
      if (!decoded || typeof decoded !== 'object') {
        throw new Error('Decoded token is not a valid object');
      }

      return decoded;
    } catch (error: any) {
      // 🛡️ অডিটর ফিক্স: সাইলেন্ট ফেইলর ব্লাস্ট করে ইন্টারনাল ডায়াগনস্টিক ট্রেস এনফোর্স
      console.warn("⚠️ [TOKEN_STORE_LEAK]: Failed to safely parse or decode admin JWT token.", {
        error_message: error?.message || 'Malformed structure',
        token_length: token.length,
        timestamp: new Date().toISOString(),
        token_preview: token.substring(0, 20) + '...' // Safe preview for debugging
      });

      // সেফ ফলব্যাক কিন্তু ট্রেসযোগ্য
      return null;
    }
  }
};
