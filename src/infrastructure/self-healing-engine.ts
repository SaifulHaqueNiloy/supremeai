import { errorBus } from './error-bus';
import Redis from 'ioredis';
import { config } from '../config';

const redis = new Redis(config.REDIS_URL);

export interface HealableOperation {
  module: string;
  method: string;
  operation: () => Promise<any>;
}

class SelfHealingEngine {
  private maxRetries: number = 3;

  constructor() {
    this.listenForErrors();
  }

  /**
   * Listen for errorBus events and trigger exponential backoff retry.
   * বাংলা মন্তব্য: এরর ইভেন্ট শুনে Redis ফেলিউর কাউন্টের ওপর ভিত্তি করে এক্সপোনেনশিয়াল ব্যাকঅফ দিয়ে অটো-রিট্রাই করে।
   */
  private listenForErrors(): void {
    errorBus.on('system_error', async (context) => {
      const failureKey = `failure:${context.module}:${context.method}`;
      const failureCount = await this.incrementFailureHistory(failureKey);

      if (failureCount < this.maxRetries) {
        const delay = Math.pow(2, failureCount - 1) * 1000; // Exponential backoff (1s, 2s, 4s...)
        setTimeout(() => this.executeHealableOperation({
          module: context.module,
          method: context.method,
          operation: context.payload?.retryLogic,
        }), delay);
      } else {
        await redis.del(failureKey);
        // Escalate to human-in-the-loop (e.g., trigger admin JIT notification)
        console.error(`[Self-Healing] Max retries reached for ${context.method}. Escalating.`);
      }
    });
  }

  private async incrementFailureHistory(key: string): Promise<number> {
    const count = await redis.incr(key);
    if (count === 1) await redis.expire(key, 600); // 10-minute expiry
    return count;
  }

  public async executeHealableOperation(op: HealableOperation): Promise<any> {
    try {
      const result = await op.operation();
      await redis.del(`failure:${op.module}:${op.method}`);
      return result;
    } catch (error) {
      errorBus.emitError({
        module: op.module,
        method: op.method,
        error,
        payload: { retryLogic: op.operation },
        timestamp: Date.now()
      });
      return null;
    }
  }
}

export const selfHealingEngine = new SelfHealingEngine();
