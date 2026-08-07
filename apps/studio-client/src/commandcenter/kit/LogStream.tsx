import { useRef, useEffect, useState } from 'react';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Command Center — Log Stream Viewer
// বাংলা মন্তব্য: লাইভ লগ স্ট্রিম — অটো-স্ক্রল পজ, সিনট্যাক্স হাইলাইট
// ═══════════════════════════════════════════════════════════════════════════

interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
    source?: string;
}

interface LogStreamProps {
    entries: LogEntry[];
    maxHeight?: number;
    filterLevel?: string;
    loading?: boolean;
}

const LEVEL_COLORS: Record<string, string> = {
    debug: 'text-[#64748b]',
    info: 'text-[#00f3ff]',
    warning: 'text-[#f59e0b]',
    warn: 'text-[#f59e0b]',
    error: 'text-[#ef4444]',
    critical: 'text-[#ef4444] font-bold',
    success: 'text-[#10b981]',
};

export function LogStream({ entries, maxHeight = 240, filterLevel, loading }: LogStreamProps) {
    const [autoScroll, setAutoScroll] = useState(true);
    const containerRef = useRef<HTMLDivElement>(null);

    const filtered = filterLevel
        ? entries.filter(e => e.level.toLowerCase() === filterLevel.toLowerCase())
        : entries;

    useEffect(() => {
        if (autoScroll && containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
    }, [filtered, autoScroll]);

    const handleScroll = () => {
        if (!containerRef.current) return;
        const el = containerRef.current;
        const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 32;
        setAutoScroll(atBottom);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-4 text-[10px] text-[var(--sa-text-2)] font-mono">
                <span className="animate-pulse">LOADING LOGS...</span>
            </div>
        );
    }

    if (filtered.length === 0) {
        return (
            <div className="flex items-center justify-center p-4 text-[10px] text-[var(--sa-text-2)] font-mono">
                NO LOG ENTRIES
            </div>
        );
    }

    return (
        <div className="relative">
            {!autoScroll && (
                <button
                    onClick={() => setAutoScroll(true)}
                    className="absolute top-2 right-2 z-10 text-[9px] px-2 py-1 rounded bg-[var(--sa-bg-3)] text-[var(--sa-text-1)] font-mono border border-[var(--sa-line)] hover:border-[var(--sa-cyan)] transition-colors"
                >
                    AUTO-SCROLL ▼
                </button>
            )}
            <div
                ref={containerRef}
                onScroll={handleScroll}
                className="overflow-y-auto font-mono text-[10px] leading-relaxed p-2 rounded-lg bg-black/40 border border-[var(--sa-line)]"
                style={{ maxHeight }}
            >
                {filtered.map((entry, i) => (
                    <div key={i} className="flex gap-2 hover:bg-[var(--sa-bg-hover)] rounded px-1 py-0.5 transition-colors">
                        <span className="text-[var(--sa-text-3)] shrink-0">
                            [{entry.timestamp}]
                        </span>
                        <span className={`shrink-0 uppercase ${LEVEL_COLORS[entry.level.toLowerCase()] || 'text-[var(--sa-text-1)]'}`}>
                            {entry.level}
                        </span>
                        {entry.source && (
                            <span className="text-[var(--sa-text-3)] shrink-0">({entry.source})</span>
                        )}
                        <span className="text-[var(--sa-text-0)] break-all">{entry.message}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
