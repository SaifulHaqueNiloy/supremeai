import React from 'react';
import { Typography, Badge, Space, List, Tag, Timeline } from 'antd';
import { BugOutlined, CheckCircleOutlined, WarningOutlined, SyncOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const SelfHealingLogs: React.FC = () => {
    return (
        <div className="p-4 animate-fade-in">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 glass-card p-6 border border-white/5 bg-black/40">
                    <Title level={5} className="!text-white !text-[12px] uppercase tracking-widest flex items-center gap-2 mb-6">
                        <BugOutlined className="text-red-500" /> Neural System Trace
                    </Title>
                    
                    <div className="bg-black/40 rounded-xl p-4 font-mono text-[10px] h-[500px] overflow-y-auto custom-scrollbar border border-white/5">
                        {[
                            { time: '14:22:01', level: 'INFO', msg: 'System heartbeat normal. All 5 models responding.', color: 'emerald' },
                            { time: '14:22:15', level: 'WARN', msg: 'GPT-4o latency spike detected: 850ms. Rerouting traffic...', color: 'yellow' },
                            { time: '14:22:16', level: 'ACTION', msg: 'Auto-healing: Switched primary provider to Claude-3.5.', color: 'blue' },
                            { time: '14:23:45', level: 'ERROR', msg: 'Ollama local node timeout. Attempting container restart.', color: 'red' },
                            { time: '14:24:02', level: 'INFO', msg: 'Ollama node recovered. State: HEALTHY.', color: 'emerald' },
                        ].map((log, i) => (
                            <div key={i} className="mb-2 flex gap-4 border-l border-white/10 pl-4">
                                <span className="text-white/20 whitespace-nowrap">[{log.time}]</span>
                                <span className={`text-${log.color}-500 font-black w-16`}>{log.level}</span>
                                <span className="text-white/60">{log.msg}</span>
                            </div>
                        ))}
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
                        items={[
                            {
                                dot: <CheckCircleOutlined className="text-emerald-500" />,
                                children: (
                                    <div className="flex flex-col gap-1">
                                        <span className="text-[10px] text-white font-bold uppercase">DB Sync Recovery</span>
                                        <span className="text-[9px] text-white/30 uppercase">Resolved Firestore connection glitch automatically</span>
                                    </div>
                                )
                            },
                            {
                                dot: <WarningOutlined className="text-yellow-500" />,
                                children: (
                                    <div className="flex flex-col gap-1">
                                        <span className="text-[10px] text-white font-bold uppercase">Rate Limit Mitigation</span>
                                        <span className="text-[9px] text-white/30 uppercase">Implemented 2s cooling period for Claude API</span>
                                    </div>
                                )
                            }
                        ]}
                    />
                </div>
            </div>
        </div>
    );
};

export default SelfHealingLogs;
