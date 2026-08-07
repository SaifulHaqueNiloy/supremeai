import React, { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import { getApiBaseUrl } from '../../utils/api';
import { AppDefaults } from '../../config/constants';
import { apiClient, setApiConcurrency } from '../../services/apiClient';
import { selfHealingState } from '../../core/stateManagement';

interface GlobalConfigInitializerProps {
  children: React.ReactNode;
}

// বাংলা মন্তব্য: সেলফ-হিলিং রিট্রাই এর বাউন্ডেড লিমিট ও ব্যাকঅফ (ইনফিনিট লুপ প্রতিরোধ)।
const MAX_RETRIES = 3;
const BASE_BACKOFF_MS = 1000;

export const GlobalConfigInitializer: React.FC<GlobalConfigInitializerProps> = ({ children }) => {
  const { isConfigLoaded, setConfig } = useStore();
  const [error, setError] = useState<string | null>(null);
  const [isHealing, setIsHealing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let retryCount = 0;
    let backoffTimer: ReturnType<typeof setTimeout> | null = null;

    const applyConfig = (data: any) => {
      setConfig(data);
      if (data?.maxConcurrency) {
        setApiConcurrency(data.maxConcurrency);
      }
      // বাংলা মন্তব্য: selfHealing ফ্ল্যাগ backend/AppDefaults থেকে এসেছে কিনা তা স্টেট ম্যানেজারে রিপোর্ট করি
      if (data?.features?.selfHealing !== undefined) {
        selfHealingState.setEnabled(Boolean(data.features.selfHealing));
      }
    };

    const fetchConfig = async () => {
      if (cancelled) return;
      setError(null);
      try {
        const data = await apiClient.get<any>('/api/config/public');
        if (cancelled) return;
        applyConfig(data);
      } catch (err) {
        if (cancelled) return;
        console.error("Config fetch error:", err);
        selfHealingState.reportError(String(err), 'CONFIG_FETCH_FAILED');

        // বাংলা মন্তব্য: সেলফ-হিলিং চালু থাকলে bounded retry করবে, নাহলে সরাসরি safe-default।
        const healingEnabled = useStore.getState().systemConfig?.features?.selfHealing
          ?? AppDefaults.features.selfHealing;
        if (healingEnabled && retryCount < MAX_RETRIES) {
          retryCount += 1;
          setIsHealing(true);
          const delay = BASE_BACKOFF_MS * Math.pow(2, retryCount - 1);
          console.warn(`[Self-Healing] Retry ${retryCount}/${MAX_RETRIES} in ${delay}ms`);
          backoffTimer = setTimeout(fetchConfig, delay);
          return;
        }

        // বাংলা মন্তব্য: retry শেষেও fail → safe-default fallback (graceful degradation)
        applyConfig(AppDefaults);
        setIsHealing(false);
        setError("Failed to connect to SupremeAI core. Using safe-default configurations.");
      }
    };

    const onDeviceOnline = () => {
      // বাংলা মন্তব্য: অফলাইন→অনলাইন হলে নিজে থেকেই কনফিগ রি-ফেচ করে স্টেট রিস্টোর
      const healingEnabled = useStore.getState().systemConfig?.features?.selfHealing
        ?? AppDefaults.features.selfHealing;
      if (healingEnabled && !useStore.getState().isConfigLoaded) {
        console.warn('[Self-Healing] Device back online. Restoring config.');
        retryCount = 0;
        fetchConfig();
      }
    };

    if (!isConfigLoaded) {
      const loadConfig = async () => {
        await fetchConfig();
      };
      loadConfig();
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('online', onDeviceOnline);
    }

    return () => {
      cancelled = true;
      if (backoffTimer) clearTimeout(backoffTimer);
      if (typeof window !== 'undefined') {
        window.removeEventListener('online', onDeviceOnline);
      }
    };
  }, [isConfigLoaded, setConfig]);

  if (!isConfigLoaded) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#0a0a0a] text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
          <p className="text-sm font-medium tracking-wide text-gray-400">
            {isHealing ? 'Recovering Core Telemetry...' : 'Initializing Core Telemetry...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      {error && (
        <div className="fixed top-0 z-50 flex w-full items-center justify-between bg-yellow-600/90 px-4 py-2 text-sm font-semibold text-white backdrop-blur-md">
          <span>{error}</span>
          <button
            onClick={() => window.location.reload()}
            className="rounded bg-yellow-700 px-3 py-1 hover:bg-yellow-800 focus:outline-none"
          >
            Retry Connection
          </button>
        </div>
      )}
      {children}
    </>
  );
};

