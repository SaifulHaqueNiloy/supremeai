import * as dotenv from 'dotenv';
dotenv.config();

// বাংলা মন্তব্য: অ্যাপ্লিকেশনের কোর কনফিগারেশন ইন্টারফেস
export interface AppConfig {
  PORT: number;
  DB_URI: string;
  REDIS_URL: string;
  JIT_OTP_SECRET: string;
}

// Anti-Silent Failure: প্রয়োজনীয় এনভায়রনমেন্ট ভ্যারিয়েবল না থাকলে ইনস্ট্যান্স দ্রুত বন্ধ হবে
const loadConfig = (): AppConfig => {
  const requiredVars = ['DB_URI', 'REDIS_URL', 'JIT_OTP_SECRET'];
  const missing = requiredVars.filter((v) => !process.env[v]);

  if (missing.length > 0) {
    throw new Error(`[FATAL] Missing critical environment variables: ${missing.join(', ')}`);
  }

  return {
    PORT: parseInt(process.env.PORT || '3000', 10),
    DB_URI: process.env.DB_URI!,
    REDIS_URL: process.env.REDIS_URL!,
    JIT_OTP_SECRET: process.env.JIT_OTP_SECRET!,
  };
};

export const config = loadConfig();
