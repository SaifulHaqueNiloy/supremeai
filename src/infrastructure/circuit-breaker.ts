import Redis from 'ioredis';
import { config } from '../config';

const redis = new Redis(config.REDIS_URL);

export type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

export interface CircuitOptions {
  failureThreshold: number;
  resetTimeout: number;
}

export class CircuitBreaker {
  private readonly key: string;
  private readonly options: CircuitOptions;

  constructor(serviceName: string, options?: Partial<CircuitOptions>) {
    this.key = `circuit:${serviceName}`;
    this.options = {
      failureThreshold: options?.failureThreshold || 5,
      resetTimeout: options?.resetTimeout || 30000,
    };
  }

  /**
   * Get current state of circuit breaker.
   * বাংলা মন্তব্য: ডিস্ট্রিবিউটেড Redis কী ব্যবহার করে CLOSED, OPEN বা HALF_OPEN স্টেট নির্ধারণ করা হয়।
   */
  private async getState(): Promise<{ state: CircuitState; failures: number }> {
    const failures = parseInt(await redis.get(this.key) || '0', 10);
    const lastFailureTime = parseInt(await redis.get(`${this.key}:time`) || '0', 10);

    if (failures >= this.options.failureThreshold) {
      const timeSinceLastFailure = Date.now() - lastFailureTime;
      if (timeSinceLastFailure > this.options.resetTimeout) {
        return { state: 'HALF_OPEN', failures };
      }
      return { state: 'OPEN', failures };
    }
    return { state: 'CLOSED', failures };
  }

  public async recordFailure(): Promise<void> {
    const multi = redis.multi();
    multi.incr(this.key);
    multi.set(`${this.key}:time`, Date.now().toString());
    multi.expire(this.key, 300);
    await multi.exec();
  }

  public async recordSuccess(): Promise<void> {
    await redis.del(this.key);
    await redis.del(`${this.key}:time`);
  }

  public async canExecute(): Promise<boolean> {
    const { state } = await this.getState();
    return state === 'CLOSED' || state === 'HALF_OPEN';
  }
}
