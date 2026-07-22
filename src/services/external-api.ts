import { ResilientExecutor } from '../infrastructure/resilient-executor';
import { JITDefense } from '../security/jit-defense';

// বাংলা মন্তব্য: রেজিলিয়েন্ট এক্সিকিউটর এবং JIT OTP ভ্যালিডেশনের বাস্তব প্রোডাকশন ডেমো সার্ভিস।
export class ExternalApiService {
  static async fetchCriticalData(userId: string): Promise<any> {
    return ResilientExecutor.run(
      'ExternalApiService',
      async () => {
        const response = await fetch(`https://free-api.example.com/data/${userId}`);
        if (!response.ok) throw new Error(`API failed with status ${response.status}`);
        return response.json();
      },
      async () => ({ data: null, status: 'degraded' })
    );
  }

  // Example of JIT Defense implementation on a destructive route
  static async deleteUserData(adminId: string, userId: string, otp: string): Promise<boolean> {
    const isValid = await JITDefense.verifyOTP(adminId, 'DELETE_USER', otp);
    if (!isValid) throw new Error('JIT OTP Verification Failed');

    // Proceed with deletion logic...
    return true;
  }
}
