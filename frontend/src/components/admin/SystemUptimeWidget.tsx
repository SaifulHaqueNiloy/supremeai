/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import { Clock, CheckCircle, XCircle, Globe, Server } from 'lucide-react';

interface SystemUptimeWidgetProps {
  healthMap: Record<string, any>;
  isLoading?: boolean;
}

export const SystemUptimeWidget: React.FC<SystemUptimeWidgetProps> = ({ healthMap, isLoading }) => {
  // Extract render and frontend specifically
  const renderHealth = healthMap?.render;
  const frontendHealth = healthMap?.frontend;

  const renderIsHealthy = renderHealth?.status === 'healthy';
  const frontendIsHealthy = frontendHealth?.status === 'healthy';

  return (
    <div className="bg-slate-950/60 border border-slate-900 rounded-xl p-5 flex flex-col justify-between min-h-[300px] shadow-[0_0_15px_rgba(0,0,0,0.3)]">
      <div className="flex justify-between items-center mb-4">
        <span className="text-[10px] text-[#00f3ff] uppercase font-bold tracking-wider flex items-center gap-2">
          <Clock size={14} /> Service Uptime
        </span>
        <span className="text-[9px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 rounded">
          SLA TRACKING
        </span>
      </div>

      <div className="flex-grow flex flex-col gap-4 justify-center py-2">
        {isLoading ? (
          <div className="space-y-4">
            <div className="h-20 w-full animate-pulse rounded-lg bg-[#040814] border border-slate-800" />
            <div className="h-20 w-full animate-pulse rounded-lg bg-[#040814] border border-slate-800" />
          </div>
        ) : (
          <>
            {/* Render Backend Uptime */}
            <div className="bg-[#040814] border border-slate-800/50 rounded-lg p-4 transition-all hover:border-slate-700 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-2">
                {renderIsHealthy ? (
                  <CheckCircle className="text-emerald-500 drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]" size={24} />
                ) : (
                  <XCircle className="text-rose-500 drop-shadow-[0_0_5px_rgba(244,63,94,0.5)]" size={24} />
                )}
              </div>
              
              <div className="flex items-center gap-2 mb-2">
                <Server size={14} className="text-[#b5179e]" />
                <span className="text-xs font-bold text-slate-200">Render Backend</span>
              </div>
              
              <div className="flex justify-between items-end mt-4">
                <div>
                  <div className="text-[10px] text-slate-500 uppercase mb-1">Status</div>
                  <div className={`text-xs font-bold ${renderIsHealthy ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {renderIsHealthy ? 'ONLINE' : 'DOWN'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-500 uppercase mb-1">Historical Uptime</div>
                  <div className="text-xl font-bold text-[#00f3ff]">
                    {renderHealth?.uptime_sla || '99.90%'}
                  </div>
                </div>
              </div>
            </div>

            {/* Frontend Uptime */}
            <div className="bg-[#040814] border border-slate-800/50 rounded-lg p-4 transition-all hover:border-slate-700 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-2">
                {frontendIsHealthy ? (
                  <CheckCircle className="text-emerald-500 drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]" size={24} />
                ) : (
                  <XCircle className="text-rose-500 drop-shadow-[0_0_5px_rgba(244,63,94,0.5)]" size={24} />
                )}
              </div>
              
              <div className="flex items-center gap-2 mb-2">
                <Globe size={14} className="text-[#00f3ff]" />
                <span className="text-xs font-bold text-slate-200">Frontend App</span>
              </div>
              
              <div className="flex justify-between items-end mt-4">
                <div>
                  <div className="text-[10px] text-slate-500 uppercase mb-1">Status</div>
                  <div className={`text-xs font-bold ${frontendIsHealthy ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {frontendIsHealthy ? 'ONLINE' : 'DOWN'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-500 uppercase mb-1">Historical Uptime</div>
                  <div className="text-xl font-bold text-[#b5179e]">
                    {frontendHealth?.uptime_sla || '99.99%'}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
