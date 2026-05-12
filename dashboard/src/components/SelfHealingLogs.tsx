import React, { useState, useEffect } from 'react';
import { Typography, Badge, Space, List, Tag, Timeline, Spin } from 'antd';
import { BugOutlined, CheckCircleOutlined, WarningOutlined, SyncOutlined } from '@ant-design/icons';
import { authUtils } from '../lib/authUtils';

const { Text, Title } = Typography;

interface LogEntry {
    timestamp: number;
    severity: string;
    details: string;
    category: string;
}

const SelfHealingLogs: React.FC = () => {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchLogs = async () => {
        try {
            const response = await authUtils.fetchWithAuth('/api/logs?pageSize=20');
            if (response.success && response.data?.logs) {
                setLogs(response.data.logs);
            }
        } catch (error) {
            console.error('Failed to fetch self-healing logs:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    const getSeverityColor = (severity: string) => {
        switch (severity.toUpperCase()) {
            case 'CRITICAL':
            case 'ERROR': return 'red';
            case 'WARN':
            case 'WARNING': return 'yellow';
            case 'INFO': return 'emerald';
            case 'ACTION': return 'blue';
            default: return 'white';
        }
    };

    return (
        <div className="p-4 animate-fade-in">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 glass-card p-6 border border-white/5 bg-black/40">
                    <Title level={5} className="!text-white !text-[12px] uppercase tracking-widest flex items-center gap-2 mb-6">
                        <BugOutlined className="text-red-500" /> Neural System Trace
                    </Title>
                    
                    <div className="bg-black/40 rounded-xl p-4 font-mono text-[10px] h-[500px] overflow-y-auto custom-scrollbar border border-white/5">
                        {loading && logs.length === 0 ? (
                            <div className="h-full flex items-center justify-center">
                                <Spin size="small" />
                            </div>
                        ) : (
                            logs.map((log, i) => (
                                <div key={i} className="mb-2 flex gap-4 border-l border-white/10 pl-4">
                                    <span className="text-white/20 whitespace-nowrap">
                                        [{new Date(log.timestamp).toLocaleTimeString()}]
                                    </span>
                                    <span className={`text-${getSeverityColor(log.severity)}-500 font-black w-16 uppercase`}>
                                        {log.severity}
                                    </span>
                                    <span className="text-white/60">{log.details}</span>
                                    <Tag className="text-[8px] bg-white/5 border-white/10 text-white/40 ml-auto uppercase">
                                        {log.category}
                                    </Tag>
                                </div>
                            ))
                        )}
                        <div className="flex items-center gap-2 mt-4 animate-pulse">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            <span className="text-emerald-500/40 italic">Listening for new telemetry pulses...</span>
                        </div>
                    </div>
                </div>

                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Title level={5} className="!text-white !text-[12px] uppercase tracking-widest mb-6">
                        Auto-Healing Logic
                    </Title>
                    <Timeline 
                        pending={<span className="text-[9px] text-white/20 uppercase">Monitoring Real-time...</span>}
                        className="dark-timeline"
                        items={logs.filter(l => l.severity === 'ACTION' || l.category === 'AUTO_HEALING').slice(0, 5).map(log => ({
                            dot: <CheckCircleOutlined className="text-emerald-500" />,
                            children: (
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-white font-bold uppercase">{log.category}</span>
                                    <span className="text-[9px] text-white/30 uppercase">{log.details}</span>
                                </div>
                            )
                        }))}
                    />
                    {logs.filter(l => l.severity === 'ACTION' || l.category === 'AUTO_HEALING').length === 0 && (
                        <div className="text-center py-8 opacity-20">
                            <SyncOutlined spin className="text-2xl mb-2" />
                            <div className="text-[10px] uppercase">No active healing events</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SelfHealingLogs;
