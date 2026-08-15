import { useEffect, useState } from 'react';
import { Bell, CheckCircle2, AlertTriangle, AlertOctagon, Info, RefreshCw } from 'lucide-react';
import type { SystemAlert } from '../../types';

export function AdminAlertsTab() {
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('adminToken');
      if (!token) {
        setError('Admin authentication required. Please log in again.');
        setLoading(false);
        return;
      }
      const response = await fetch('/api/admin/alerts', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch alerts');
      }
      
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleResolve = async (id: string) => {
    try {
      const token = localStorage.getItem('adminToken');
      if (!token) {
        window.dispatchEvent(new CustomEvent('supremeai-toast', {
          detail: { message: 'Admin authentication required.', type: 'error' }
        }));
        return;
      }
      const response = await fetch(`/api/admin/alerts/${id}/resolve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to resolve alert');
      }
      
      // Update local state instantly
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, resolved: true } : a));
    } catch (err) {
      console.error(err);
      window.dispatchEvent(new CustomEvent('supremeai-toast', {
        detail: { message: 'Failed to resolve alert. Please try again.', type: 'error' }
      }));
    }
  };

  const getIcon = (level: string) => {
    switch (level) {
      case 'error':
      case 'critical':
        return <AlertOctagon className="text-rose-500" size={20} />;
      case 'warning':
        return <AlertTriangle className="text-amber-500" size={20} />;
      case 'info':
      default:
        return <Info className="text-blue-400" size={20} />;
    }
  };

  const getLevelStyles = (level: string, resolved: boolean) => {
    if (resolved) return 'border-slate-800 bg-slate-900/30 opacity-70';
    
    switch (level) {
      case 'error':
      case 'critical':
        return 'border-rose-500/30 bg-rose-500/5 shadow-[0_0_15px_rgba(244,63,94,0.1)]';
      case 'warning':
        return 'border-amber-500/30 bg-amber-500/5 shadow-[0_0_15px_rgba(245,158,11,0.1)]';
      case 'info':
      default:
        return 'border-blue-400/30 bg-blue-400/5 shadow-[0_0_15px_rgba(96,165,250,0.1)]';
    }
  };

  return (
    <div className="flex-1 flex flex-col p-6 overflow-hidden max-w-6xl mx-auto w-full">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Bell className="text-[#00f3ff]" />
            System Alerts & Diagnostics
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Real-time notifications from AI Log Analyzer and system health monitors.
          </p>
        </div>
        
        <button 
          onClick={fetchAlerts}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors border border-slate-700 disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 mb-6 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        {loading && alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-500">
            <RefreshCw className="animate-spin mb-4" size={32} />
            <p>Loading active alerts...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-500 border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
            <CheckCircle2 size={48} className="text-emerald-500/50 mb-4" />
            <p className="text-lg">All Systems Nominal</p>
            <p className="text-sm">No active alerts right now.</p>
          </div>
        ) : (
          alerts.map(alert => (
            <div 
              key={alert.id}
              className={`p-5 rounded-xl border transition-all duration-300 ${getLevelStyles(alert.level, alert.resolved)}`}
            >
              <div className="flex items-start gap-4">
                <div className="mt-1">
                  {getIcon(alert.level)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                        alert.level === 'error' ? 'bg-rose-500/20 text-rose-400' :
                        alert.level === 'warning' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-blue-400/20 text-blue-400'
                      }`}>
                        {alert.level}
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(alert.created_at).toLocaleString()}
                      </span>
                    </div>
                    
                    {!alert.resolved && (
                      <button 
                        onClick={() => handleResolve(alert.id)}
                        className="px-3 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded border border-emerald-500/30 transition-colors flex items-center gap-1.5"
                      >
                        <CheckCircle2 size={14} />
                        Mark Resolved
                      </button>
                    )}
                    {alert.resolved && (
                      <span className="text-xs text-slate-500 flex items-center gap-1.5">
                        <CheckCircle2 size={14} />
                        Resolved at {new Date(alert.resolved_at!).toLocaleString()}
                      </span>
                    )}
                  </div>
                  
                  {/* Message could contain markdown or newlines */}
                  <div className={`text-sm whitespace-pre-wrap ${alert.resolved ? 'text-slate-400' : 'text-slate-200'}`}>
                    {alert.message}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
