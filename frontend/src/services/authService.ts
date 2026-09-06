// Authentication Service for SupremeAI 2.0
// বাংলা মন্তব্য: এটি অ্যাডমিন লগইন ও ফায়ারবেস অথেন্টিকেশন সার্ভিস প্রোভাইড করে।

import { apiClient } from './apiClient';

export const authService = {
  // বাংলা মন্তব্য: ফায়ারবেস অথেনটিকেশন, রোল ভেরিফিকেশন এবং টিওটিপি ফ্লো
  firebaseLogin: async (idToken: string): Promise<{ status: string; token?: string; uid?: string; email?: string }> => {
    const response = await apiClient.post<{ status: string; token?: string; access_token?: string; jwt?: string; uid?: string; email?: string }>('/api/admin/firebase-login', { id_token: idToken });
    return { ...response, token: response.token ?? response.access_token ?? response.jwt };
  },

  // বাংলা মন্তব্য: ফায়ারবেস টিওটিপি ৭ ডিজিট কনফিগারেশন সেটআপ সার্ভিস এন্ডপয়েন্ট
  firebaseTotpSetup: async (idToken: string): Promise<{ secret: string; provisioning_uri: string; recovery_codes?: string[] }> => {
    return apiClient.post<{ secret: string; provisioning_uri: string; recovery_codes?: string[] }>('/api/admin/firebase-totp-setup', { id_token: idToken });
  },

  firebaseTotpRecover: async (idToken: string, recoveryCode: string): Promise<{ secret: string; provisioning_uri: string }> => {
    return apiClient.post<{ secret: string; provisioning_uri: string }>('/api/admin/firebase-totp-recover', { id_token: idToken, recovery_code: recoveryCode });
  },

  // বাংলা মন্তব্য: ফায়ারবেস ওটিপি কোড ৭ ডিজিট যাচাইকরণ সার্ভিস এন্ডপয়েন্ট
  firebaseTotpVerify: async (idToken: string, otp: string, rememberBrowser = false): Promise<{ status: string; token: string }> => {
    return apiClient.post<{ status: string; token: string }>('/api/admin/firebase-totp-verify', { id_token: idToken, otp, remember_browser: rememberBrowser });
  },
};
