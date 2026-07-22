import { CircuitBreaker } from './circuit-breaker';
import { selfHealingEngine } from './self-healing-engine';

// বাংলা মন্তব্য: সার্কিট ব্রেকার, সেলফ-হিলিং ইভেন্ট রিট্রাই এবং সেফ ফলব্যাক এক্সিকিউশন কম্বাইন করার সেন্ট্রাল রেজিলিয়েন্ট এক্সিকিউটর।
export class ResilientExecutor {
  static async run(
    serviceName: string,
    operation: () => Promise<any>,
    fallback?: () => Promise<any>
  ): Promise<any> {
    const circuit = new CircuitBreaker(serviceName);

    const isAllowed = await circuit.canExecute();
    if (!isAllowed) {
      if (fallback) return fallback();
      return null;
    }

    try {
      const result = await operation();
      await circuit.recordSuccess();
      return result;
    } catch (error) {
      await circuit.recordFailure();

      selfHealingEngine.executeHealableOperation({
        module: serviceName,
        method: 'auto-retry',
        operation
      });

      if (fallback) return fallback();
      return null;
    }
  }
}
