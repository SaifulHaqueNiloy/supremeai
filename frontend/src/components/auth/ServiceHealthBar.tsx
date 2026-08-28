/* eslint-disable @typescript-eslint/no-explicit-any */
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';

// বাংলা মন্তব্য: লগইন পেজের জন্য Public Service Health Bar — কোনো Authentication লাগবে না
// এটি Backend, Database, Redis, Memory এর Real-time Status দেখাবে

interface HealthCheckResult {
  status: string;
  message: string;
  details?: Record<string, unknown>;
  response_time_ms?: number;
}

interface HealthData {
  status: string;
  timestamp: number;
  total_response_time_ms: number;
  checks: {
    application: HealthCheckResult;
    redis: HealthCheckResult;
    database: HealthCheckResult;
    external_services: HealthCheckResult;
    memory: HealthCheckResult;
    disk: HealthCheckResult;
  };
  summary: {
    total_checks: number;
    healthy: number;
    degraded: number;
    unhealthy: number;
    unknown: number;
  };
}

interface ServiceStatusProps {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | 'loading';
  responseTime?: number;
}

const StatusDot: React.FC<{ status: ServiceStatusProps['status'] }> = ({ status }) => {
  const colors = {
    healthy: 'bg-emerald-500 shadow-emerald-500/50',
    degraded: 'bg-amber-500 shadow-amber-500/50',
    unhealthy: 'bg-red-500 shadow-red-500/50',
    unknown: 'bg-gray-500 shadow-gray-500/50',
    loading: 'bg-blue-500 animate-pulse shadow-blue-500/50',
  };

  return (
    <div className={`w-2 h-2 rounded-full ${colors[status]} shadow-sm`} />
  );
};

const ServiceStatusItem: React.FC<ServiceStatusProps> = ({ name, status, responseTime }) => {
  const statusLabels = {
    healthy: 'Online',
    degraded: 'Slow',
    unhealthy: 'Down',
    unknown: 'Unknown',
    loading: 'Checking...',
  };

  const statusColors = {
    healthy: 'text-emerald-400',
    degraded: 'text-amber-400',
    unhealthy: 'text-red-400',
    unknown: 'text-gray-400',
    loading: 'text-blue-400',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-black/20 backdrop-blur-sm"
    >
      <div className="flex items-center gap-2">
        <StatusDot status={status} />
        <span className="text-xs font-medium text-gray-300">{name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`text-xs font-semibold ${statusColors[status]}`}>
          {statusLabels[status]}
        </span>
        {responseTime && status === 'healthy' && (
          <span className="text-[10px] text-gray-500 font-mono">
            {responseTime.toFixed(0)}ms
          </span>
        )}
      </div>
    </motion.div>
  );
};

// বাংলা মন্তব্য: Public Health Check Function — কোনো Auth Header ছাড়াই কল হবে
const fetchPublicHealth = async (): Promise<HealthData> => {
  const apiBaseUrl = import.meta.env.VITE_API_URL || '';
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000); // 8s timeout for health check

  try {
    const res = await fetch(`${apiBaseUrl}/health/aggregated`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // বাংলা: কোনো Authorization header নেই — public endpoint
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      throw new Error(`Health check failed with status ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    clearTimeout(timeoutId);
    
    // বাংলা: Backend unreachable হলে fallback response
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('Backend health check timed out');
    }
    throw error;
  }
};

export const ServiceHealthBar: React.FC = () => {
  const { data, error, isLoading, isError } = useQuery<HealthData>({
    queryKey: ['public-health-status'],
    queryFn: fetchPublicHealth,
    refetchInterval: isError ? false : 15000, // 15 seconds refresh
    retry: 2,
    staleTime: 10_000,
    // বাংলা: Always enabled — login page-এও দেখাবে
    enabled: true,
  });

  // বাংলা: Error state — backend unreachable
  if (isError) {
    return (
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md mb-4 p-3 rounded-xl bg-red-950/60 border border-red-800/50 backdrop-blur-sm"
        >
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-sm font-semibold text-red-300">⚠️ System Unreachable</span>
          </div>
          <p className="text-xs text-red-400/80">
            Backend server is not responding. Please try again in a few moments.
          </p>
          <p className="text-[10px] text-red-500/60 mt-1 font-mono">
            {error?.message || 'Network error or CORS issue'}
          </p>
        </motion.div>
      </AnimatePresence>
    );
  }

  // বাংলা: Loading state
  if (isLoading || !data) {
    return (
      <div className="w-full max-w-md mb-4 p-3 rounded-xl bg-black/30 border border-white/5 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-sm font-medium text-gray-400">Checking system status...</span>
        </div>
      </div>
    );
  }

  // বাংলা: Parse health data for display
  const services: { key: keyof HealthData['checks']; label: string }[] = [
    { key: 'application', label: 'Backend API' },
    { key: 'database', label: 'Database' },
    { key: 'redis', label: 'Redis Cache' },
    { key: 'memory', label: 'Memory' },
    { key: 'disk', label: 'Disk' },
  ];

  const getServiceStatus = (check: HealthCheckResult): ServiceStatusProps['status'] => {
    if (!check || !check.status) return 'unknown';
    return check.status as ServiceStatusProps['status'];
  };

  const overallStatus = data.status;
  const isHealthy = overallStatus === 'healthy';
  const isDegraded = overallStatus === 'degraded';
  const isUnhealthy = overallStatus === 'unhealthy';

  // বাংলা: Overall status banner color
  const bannerColor = isHealthy 
    ? 'border-emerald-800/40 bg-emerald-950/30' 
    : isDegraded 
      ? 'border-amber-800/40 bg-amber-950/30'
      : 'border-red-800/40 bg-red-950/30';

  const textColor = isHealthy ? 'text-emerald-300' : isDegraded ? 'text-amber-300' : 'text-red-300';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`w-full max-w-md mb-4 p-4 rounded-xl border backdrop-blur-sm ${bannerColor}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`w-2.5 h-2.5 rounded-full ${
              isHealthy ? 'bg-emerald-500 shadow-emerald-500/50' :
              isDegraded ? 'bg-amber-500 animate-pulse shadow-amber-500/50' :
              'bg-red-500 animate-pulse shadow-red-500/50'
            }`} />
            <span className={`text-sm font-bold ${textColor}`}>
              {isHealthy ? '✓ All Systems Operational' :
               isDegraded ? '⚠ System Degraded' :
               '✕ System Issues Detected'}
            </span>
          </div>
          <span className="text-[10px] text-gray-500 font-mono">
            {data.summary.healthy}/{data.summary.total_checks} OK
          </span>
        </div>

        {/* Service Status Grid */}
        <div className="space-y-1.5">
          {services.map(({ key, label }) => {
            const check = data.checks[key];
            return (
              <ServiceStatusItem
                key={key}
                name={label}
                status={getServiceStatus(check)}
                responseTime={check?.response_time_ms}
              />
            );
          })}
        </div>

        {/* Footer */}
        {(isDegraded || isUnhealthy) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-3 pt-3 border-t border-white/5"
          >
            <p className="text-[11px] text-gray-400">
              {isDegraded 
                ? 'Some services are experiencing slow response times. Login may take longer than usual.'
                : 'Critical services are down. You may experience issues during login.'}
            </p>
          </motion.div>
        )}

        {/* Response Time */}
        <div className="mt-2 flex justify-end">
          <span className="text-[10px] text-gray-600 font-mono">
            Checked: {new Date(data.timestamp * 1000).toLocaleTimeString()}
          </span>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ServiceHealthBar;
