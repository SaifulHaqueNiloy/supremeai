import * as crypto from 'crypto';
import Redis from 'ioredis';
import { config } from '../config';

// বাংলা মন্তব্য: Redis ক্লায়েন্ট ইনিশিয়ালাইজেশন - JIT OTP স্টেট ট্র্যাকিংয়ের জন্য
const redis = new Redis(config.REDIS_URL);

export class JITDefense {
  /**
   * Generates a Just-In-Time OTP for sensitive actions.
   * বাংলা মন্তব্য: সংবেদনশীল অ্যাকশনের জন্য ৫ মিনিট মেয়াদের ৬-ডিজিটের এককালীন OTP জেনারেট করে।
   */
  static async generateOTP(userId: string, action: string): Promise<string> {
    const otp = crypto.randomInt(100000, 999999).toString();
    const key = `jit:${userId}:${action}:${otp}`;
    await redis.set(key, 'valid', 'EX', 300); // 5 minutes
    return otp;
  }

  /**
   * Verifies the JIT OTP. One-time use only (prevents replay attacks).
   * বাংলা মন্তব্য: OTP ভেরিফাই করে এবং রিপ্লে অ্যাটাক রোধে সাথে সাথে কী ডিলিট করে।
   */
  static async verifyOTP(userId: string, action: string, otp: string): Promise<boolean> {
    const key = `jit:${userId}:${action}:${otp}`;
    const result = await redis.get(key);

    if (result === 'valid') {
      await redis.del(key); // One-time use
      return true;
    }
    return false;
  }
}
