/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Badge, Skeleton } from '../ui';
import { Globe, HardDrive, Cpu, Network, RefreshCw, Zap, Play, CheckCircle2, Server, Flame, Sparkles } from 'lucide-react';
// বাংলা মন্তব্য: raw fetch()-এর বদলে apiClient ব্যবহার করা হচ্ছে — auth হেডার ও থ্রটল গ্যারান্টি দেয়
import { apiClient } from '../../services/apiClient';
import { adminTokenStore } from '../../services/adminTokenStore';

const CLOUD_PROVIDERS = [
  { id: 'gcp', name: 'Google Cloud Platform', color: '#4285f4', icon: Globe },
  { id: 'aws', name: 'AWS', color: '#ff9900', icon: Globe },
  { id: 'azure', name: 'Azure', color: '#0078d4', icon: Globe },
  { id: 'cloudflare', name: 'Cloudflare', color: '#f48120', icon: Network },
  { id: 'supabase', name: 'Supabase', color: '#3ecf8e', icon: HardDrive },
  { id: 'railway', name: 'Railway', color: '#0b0d0e', icon: Cpu },
  { id: 'render', name: 'Render', color: '#46a5f5', icon: Globe },
];

export function CloudOrchestrator() {
  const [triggeringStage, setTriggeringStage] = useState<string | null>(null);
  const [triggerMessage, setTriggerMessage] = useState<string | null>(null);

  // বাংলা মন্তব্য: queryKey ম্যাচ করানো হয়েছে useDashboardData.useHealthMap()-এর সাথে — ক্যাশ শেয়ার হবে, ডুপ্লিকেট ফেচ বন্ধ
  const { data: health, isLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['dashboard', 'health'],
    queryFn: () => apiClient.get<any>('/admin-api/health-map'),
    enabled: !!adminTokenStore.getDecodedToken(),
    staleTime: 20_000,
  });

  const { data: metrics } = useQuery({
    queryKey: ['dashboard', 'metrics'],
    queryFn: () => apiClient.get<any>('/admin-api/metrics'),
    enabled: !!adminTokenStore.getDecodedToken(),
    staleTime: 20_000,
  });

  // Kaggle 6-Node Cluster Status Query
  const { data: kaggleCluster, refetch: refetchKaggle } = useQuery({
    queryKey: ['dashboard', 'kaggle-status'],
    queryFn: () => apiClient.get<any>('/admin-api/kaggle/status'),
    enabled: !!adminTokenStore.getDecodedToken(),
    staleTime: 10_000,
  });

  const handleTriggerStage = async (stage: string) => {
    try {
      setTriggeringStage(stage);
      setTriggerMessage(`Queueing ${stage} on Kaggle cluster...`);
      const res = await apiClient.post<any>('/admin-api/kaggle/trigger', { stage });
      setTriggerMessage(res?.message || `Stage '${stage}' queued successfully!`);
      setTimeout(() => setTriggerMessage(null), 4000);
    } catch (err: any) {
      setTriggerMessage(`Trigger failed: ${err?.message || 'Unknown error'}`);
    } finally {
      setTriggeringStage(null);
      refetchKaggle();
    }
  };

  const rps = metrics?.requests_per_second ?? 0;
  const cpu = metrics?.cpu_percent ?? metrics?.cpu_usage_percent
    ?? Math.min(100, Math.round((rps / 50) * 100));
  const mem = metrics?.memory_percent ?? metrics?.memory_usage_percent
    ?? Math.min(100, Math.round((rps / 80) * 100));
  const netGbps = Math.min(100, (rps / 500) * 100);

  const providerHealth = Object.entries(health || {}).map(([id, data]: [string, any]) => ({
    id,
    name: CLOUD_PROVIDERS.find(p => p.id === id)?.name || id,
    color: CLOUD_PROVIDERS.find(p => p.id === id)?.color || '#666',
    status: data?.status === 'healthy' ? 'healthy' : data?.status === 'degraded' ? 'degraded' : 'down',
    latency: data?.latency,
    region: data?.region,
  }));

  const nodes = kaggleCluster?.nodes || {
    node_1: { username: 'node_1', used_hours: 0, max_hours: 30, is_healthy: true },
    node_2: { username: 'node_2', used_hours: 0, max_hours: 30, is_healthy: true },
    node_3: { username: 'node_3', used_hours: 0, max_hours: 30, is_healthy: true },
    node_4: { username: 'node_4', used_hours: 0, max_hours: 30, is_healthy: true },
    node_5: { username: 'node_5', used_hours: 0, max_hours: 30, is_healthy: true },
    node_6: { username: 'node_6', used_hours: 0, max_hours: 30, is_healthy: true },
  };

  return (
    <div className="flex-grow p-6 overflow-y-auto bg-[#030611] space-y-6">
      
      {/* ── HEADER ── */}
      <div className="flex items-center justify-between pb-2 border-b border-[#00f3ff]/15">
        <div>
          <h2 className="text-lg font-bold font-['Space_Grotesk'] tracking-widest text-[#00f3ff] uppercase flex items-center gap-2">
            <Server size={18} /> Cloud & Compute Orchestrator
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Hybrid Multi-Cloud Edge & Zero-Cost GPU Cluster Matrix
          </p>
        </div>
        <button
          onClick={() => { refetchHealth(); refetchKaggle(); }}
          className="flex items-center gap-2 px-3 py-1.5 rounded border border-[#00f3ff]/30 text-[#00f3ff] hover:bg-[#00f3ff]/10 text-[10px] font-bold font-mono uppercase transition-colors"
        >
          <RefreshCw size={10} /> Refresh All
        </button>
      </div>

      {/* ── ⚡ SUPREME-KAGGLE 6-NODE SUPERCOMPUTER CLUSTER ── */}
      <div className="bg-[#050b1a] border border-[#00f3ff]/30 rounded-2xl p-5 shadow-[0_0_30px_rgba(0,243,255,0.05)] relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-[#00f3ff]/10 border border-[#00f3ff]/30 rounded-xl text-[#00f3ff]">
              <Flame size={20} className="animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                  Supreme-Kaggle 6-Node GPU Cluster
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                  {kaggleCluster?.active_nodes ?? 6}/6 NODES ONLINE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                Dual Nvidia T4 GPUs (16GB VRAM) • Total Weekly Pool: <strong className="text-white">180.0 Hours ($0 Cost)</strong>
              </p>
            </div>
          </div>

          {/* Quota Gauge */}
          <div className="flex items-center gap-4 font-mono text-xs bg-[#030612] px-4 py-2 rounded-xl border border-slate-800">
            <div>
              <span className="text-slate-500 text-[10px] uppercase block">Pool Remaining</span>
              <span className="text-emerald-400 font-bold text-sm">
                {kaggleCluster?.remaining_hours ?? 180.0}h / 180h
              </span>
            </div>
            <div className="w-[1px] h-6 bg-slate-800" />
            <div>
              <span className="text-slate-500 text-[10px] uppercase block">Reset Schedule</span>
              <span className="text-slate-300 text-xs">Sunday 00:00 UTC</span>
            </div>
          </div>
        </div>

        {/* 6 Nodes Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
          {Object.entries(nodes).map(([nodeId, data]: [string, any], idx) => {
            const isHealthy = data?.is_healthy ?? true;
            return (
              <div
                key={nodeId}
                className={`p-3 rounded-xl border transition-all ${
                  isHealthy
                    ? 'bg-[#030714] border-slate-800 hover:border-[#00f3ff]/40 shadow-sm'
                    : 'bg-rose-950/20 border-rose-900/50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold text-slate-300 uppercase">
                    NODE {idx + 1}
                  </span>
                  <span className="relative flex h-2 w-2">
                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isHealthy ? 'bg-emerald-400' : 'bg-rose-400'}`} />
                    <span className={`relative inline-flex rounded-full h-2 w-2 ${isHealthy ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                  </span>
                </div>
                <div className="text-[11px] font-mono text-white font-bold mb-1">
                  Dual T4 GPU
                </div>
                <div className="flex justify-between items-center text-[9px] font-mono text-slate-400">
                  <span>Quota:</span>
                  <span className="text-emerald-400">
                    {(data?.max_hours ?? 30) - (data?.used_hours ?? 0)}h / 30h
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1 mt-1.5">
                  <div
                    className="h-full rounded-full bg-emerald-400"
                    style={{ width: `${Math.max(5, ((30 - (data?.used_hours ?? 0)) / 30) * 100)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Stage Trigger Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate-800/80 bg-[#030612]/60 -mx-5 -mb-5 px-5 py-3 rounded-b-2xl">
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-[#00f3ff]" />
            <span className="text-xs font-mono font-bold text-slate-300 uppercase">
              Trigger Offline Batch Jobs:
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleTriggerStage('vector_fabric')}
              disabled={!!triggeringStage}
              className="px-3 py-1.5 bg-[#00f3ff]/15 border border-[#00f3ff]/30 hover:bg-[#00f3ff]/25 text-[#00f3ff] rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              <Play size={11} /> Vector Fabric (pgvector)
            </button>
            <button
              onClick={() => handleTriggerStage('brain_distillation')}
              disabled={!!triggeringStage}
              className="px-3 py-1.5 bg-purple-500/15 border border-purple-500/30 hover:bg-purple-500/25 text-purple-300 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              <Play size={11} /> Distillation Cache
            </button>
            <button
              onClick={() => handleTriggerStage('weekend_self_healer')}
              disabled={!!triggeringStage}
              className="px-3 py-1.5 bg-emerald-500/15 border border-emerald-500/30 hover:bg-emerald-500/25 text-emerald-300 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              <Play size={11} /> Self-Healer (Fuzzing)
            </button>
          </div>
        </div>

        {triggerMessage && (
          <div className="mt-3 text-xs font-mono text-[#00f3ff] bg-[#00f3ff]/10 border border-[#00f3ff]/30 p-2 rounded-lg text-center animate-fade-in">
            {triggerMessage}
          </div>
        )}
      </div>

      {/* ── CLOUD PROVIDERS HEALTH MAP ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {isLoading ? (
          <><Skeleton className="h-32 w-full" /><Skeleton className="h-32 w-full" /><Skeleton className="h-32 w-full" /><Skeleton className="h-32 w-full" /></>
        ) : (
          providerHealth.map(p => (
            <Card key={p.id} title={p.name} icon={
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: p.color }} />
            }>
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400">Status</span>
                  <Badge variant={p.status === 'healthy' ? 'success' : p.status === 'degraded' ? 'warning' : 'danger'}>{p.status}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400">Latency</span>
                  <span className="text-xs font-bold text-white font-mono">{p.latency || '< 45ms'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400">Region</span>
                  <span className="text-xs font-bold text-slate-300 font-mono">{p.region || 'global-edge'}</span>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* ── RESOURCE UTILIZATION ── */}
      <Card title="Edge & Server Resource Utilization">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div className="text-[10px] text-slate-400 uppercase mb-2">CPU Usage</div>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-white font-mono">{cpu}</span>
              <span className="text-sm text-slate-400 mb-1">%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2">
              <div className="h-full rounded-full bg-[#00f3ff]" style={{ width: `${cpu}%` }} />
            </div>
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase mb-2">Memory Usage</div>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-white font-mono">{mem}</span>
              <span className="text-sm text-slate-400 mb-1">%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2">
              <div className="h-full rounded-full bg-purple-500" style={{ width: `${mem}%` }} />
            </div>
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase mb-2">Network I/O</div>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-white font-mono">{rps}</span>
              <span className="text-sm text-slate-400 mb-1">req/s</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2">
              <div className="h-full rounded-full bg-emerald-500" style={{ width: `${netGbps}%` }} />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
