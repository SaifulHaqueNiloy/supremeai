import { EventEmitter } from 'events';

export interface ErrorContext {
  module: string;
  method: string;
  error: unknown;
  payload?: any;
  timestamp: number;
}

class ErrorBus extends EventEmitter {
  private static instance: ErrorBus;

  private constructor() {
    super();
    // বাংলা মন্তব্য: হাই-ট্রাফিকের সময় মেমোরি লিক রোধে সর্বোচ্চ লিসেনার লিমিট নির্ধারণ
    this.setMaxListeners(50);
  }

  public static getInstance(): ErrorBus {
    if (!ErrorBus.instance) {
      ErrorBus.instance = new ErrorBus();
    }
    return ErrorBus.instance;
  }

  public emitError(context: ErrorContext): void {
    // বাংলা মন্তব্য: গ্লোবাল ইভেন্ট ইমিশন - সেলফ-হিলিং এজেন্ট এবং মনিটরিং এটি রিসিভ করতে পারবে
    this.emit('system_error', context);
  }
}

export const errorBus = ErrorBus.getInstance();
