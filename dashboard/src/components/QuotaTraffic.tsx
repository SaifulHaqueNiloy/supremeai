import React, { useState, useEffect } from 'react';
import { Typography, Progress, Space, Tag, List, Statistic, Spin, Divider } from 'antd';
import { ThunderboltOutlined, AreaChartOutlined, LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { authUtils } from '../lib/authUtils';

const { Text, Title } = Typography;

const QuotaTraffic: React.FC = () => {
    const [stats, setStats] = useState<any>(null);
    const [providers, setProviders] = useState<any[]>([]);
    const [rankings, setRankings] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [contractRes, providersRes, rankingsRes] = await Promise.all([
                    authUtils.fetchWithAuth('/api/admin/dashboard/contract'),
                    authUtils.fetchWithAuth('/api/admin/providers/configured'),
                    authUtils.fetchWithAuth('/api/admin/providers/rankings')
                ]);

                if (contractRes.success && contractRes.data?.stats) {
                    setStats(contractRes.data.stats);
                }

                if (providersRes.success && providersRes.data?.providers) {
                    setProviders(providersRes.data.providers);
                }

                if (rankingsRes.success && rankingsRes.data?.rankings) {
                    setRankings(rankingsRes.data.rankings);
                }
            } catch (error) {
                console.error('Failed to fetch quota data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, 5000); // Synchronized to 5s
        return () => clearInterval(interval);
    }, []);

    if (loading && !stats) return <div className="p-12 text-center"><Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} /></div>;

    return (
        <div className="p-4 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Statistic 
                        title={<span className="text-[10px] font-black text-white/40 uppercase tracking-widest">Total Active Users</span>}
                        value={stats?.activeUsers || 0}
                        prefix={<AreaChartOutlined />}
                        valueStyle={{ color: '#fff', fontSize: '24px', fontWeight: '900', fontFamily: 'monospace' }}
                    />
                    <div className="mt-2 flex items-center gap-2">
                        <Tag color="emerald" className="text-[8px] font-black">Out of {stats?.totalUsers || 0} total</Tag>
                    </div>
                </div>
                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Statistic 
                        title={<span className="text-[10px] font-black text-white/40 uppercase tracking-widest">System Health</span>}
                        value={stats?.systemHealthScore || 0}
                        suffix="%"
                        valueStyle={{ color: stats?.systemHealthScore > 90 ? '#10b981' : '#f59e0b', fontSize: '24px', fontWeight: '900', fontFamily: 'monospace' }}
                    />
                    <div className="mt-2 flex items-center gap-2">
                        <Text className="text-[9px] text-emerald-500 font-bold uppercase">{stats?.systemHealthStatus || 'Healthy'}</Text>
                    </div>
                </div>
                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Statistic 
                        title={<span className="text-[10px] font-black text-white/40 uppercase tracking-widest">Active Connections</span>}
                        value={stats?.activeConnections || 0}
                        valueStyle={{ color: '#fff', fontSize: '24px', fontWeight: '900', fontFamily: 'monospace' }}
                    />
                    <div className="mt-2 flex items-center gap-2">
                        <Tag color="cyan" className="text-[8px] font-black">{stats?.serverUptime || '0m'} Uptime</Tag>
                    </div>
                </div>
            </div>

            <div className="glass-card p-6 border border-white/5 bg-black/40">
                <Title level={5} className="!text-white !text-[12px] uppercase tracking-widest flex items-center gap-2 mb-6">
                    <ThunderboltOutlined className="text-yellow-400" /> Resource Quota by Provider
                </Title>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div>
                        <Text className="text-white/40 text-[9px] uppercase font-black block mb-4 tracking-tighter">Connected Infrastructure</Text>
                        <List
                            dataSource={providers}
                            renderItem={(item: any) => (
                                <List.Item className="border-b border-white/5 px-0 py-3">
                                    <div className="flex items-center justify-between w-full">
                                        <div className="flex items-center gap-3">
                                            {item.status === 'ONLINE' ? 
                                                <CheckCircleOutlined className="text-emerald-500 text-[10px]" /> : 
                                                <CloseCircleOutlined className="text-red-500 text-[10px]" />
                                            }
                                            <div className="flex flex-col">
                                                <Text className="text-white text-[11px] font-black uppercase tracking-tight">{item.name}</Text>
                                                <Text className="text-white/20 text-[8px] font-mono uppercase">{item.type || 'LLM'}</Text>
                                            </div>
                                        </div>
                                        <Tag className="text-[8px] font-black uppercase border-0 bg-white/5 text-white/50">{item.status}</Tag>
                                    </div>
                                </List.Item>
                            )}
                        />
                    </div>
                    
                    <div className="bg-white/[0.02] p-4 rounded-xl border border-white/5">
                        <Text className="text-white/40 text-[9px] uppercase font-black block mb-4 tracking-tighter">Neural Ranking Matrix</Text>
                        {rankings ? (
                            <div className="space-y-4">
                                {Object.entries(rankings).map(([name, data]: [string, any]) => {
                                    const successRate = (data.successCount / (data.totalTasks || 1)) * 100;
                                    return (
                                        <div key={name} className="space-y-1">
                                            <div className="flex justify-between items-end">
                                                <Text className="text-[10px] font-black text-white uppercase">{name}</Text>
                                                <Text className="text-[9px] font-mono text-cyan-400">{successRate.toFixed(1)}% SUCCESS</Text>
                                            </div>
                                            <Progress 
                                                percent={successRate} 
                                                showInfo={false} 
                                                size="small" 
                                                strokeColor={successRate > 90 ? '#10b981' : successRate > 70 ? '#f59e0b' : '#ef4444'}
                                                trailColor="rgba(255,255,255,0.05)"
                                            />
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="h-32 flex items-center justify-center">
                                <Text className="text-white/20 text-[10px] uppercase font-black">No ranking data synchronized</Text>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default QuotaTraffic;

