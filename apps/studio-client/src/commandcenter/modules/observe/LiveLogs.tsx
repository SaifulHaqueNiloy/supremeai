import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../services/apiClient';
import { LogStream, EmptyState } from '../../kit';

interface LogEntry {
  timestamp: string;
  level: string;
  source: string;
  message: string;
}

export function LiveLogs() {
  const [autoScroll, setAutoScroll] = useState(true);
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [keyword, setKeyword] = useState('');

  const { data: logs, isLoading } = useQuery({
    queryKey: ['cmd', 'logs'],
    queryFn: () => apiClient.get<LogEntry[]>('/admin-api/logs?limit=200'),
    refetchInterval: 5000,
    enabled: !!localStorage.getItem('admin_token'),
  });

  const filtered = logs?.filter((log) => {
    if (levelFilter !== 'all' && log.level !== levelFilter) return false;
    if (keyword && !log.message.toLowerCase().includes(keyword.toLowerCase())) return false;
    return true;
  }) ?? [];

  if (isLoading && !logs) {
    return <EmptyState title="লগ লোড হচ্ছে..." message="SSE স্ট্রিম সংযোগ করা হচ্ছে..." loading />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-mono uppercase tracking-widest text-[var(--sa-text-2)]">Live Logs</h2>
        <div className="flex items-center gap-2">
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="bg-[var(--sa-bg-1)] border border-[var(--sa-line)] text-[10px] font-mono rounded px-2 py-1"
          >
            <option value="all">ALL</option>
            <option value="error">ERROR</option>
            <option value="warn">WARN</option>
            <option value="info">INFO</option>
            <option value="debug">DEBUG</option>
          </select>
          <input
            type="text"
            placeholder="Keyword..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="bg-[var(--sa-bg-1)] border border-[var(--sa-line)] text-[10px] font-mono rounded px-2 py-1 w-32"
          />
          <label className="flex items-center gap-1 text-[10px] font-mono text-[var(--sa-text-2)]">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded"
            />
            Auto-scroll
          </label>
        </div>
      </div>
      <LogStream logs={filtered} autoScroll={autoScroll} maxHeight={500} />
    </div>
  );
}
