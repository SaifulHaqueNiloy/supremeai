import React from 'react';
import { Typography, Progress, Space, Tag, List, Statistic } from 'antd';
import { ThunderboltOutlined, DollarOutlined, AreaChartOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const QuotaTraffic: React.FC = () => {
    return (
        <div className="p-4 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Statistic 
                        title={<span className="text-[10px] font-black text-white/40 uppercase tracking-widest">Total Monthly Cost</span>}
                        value={142.50}
                        precision={2}
                        prefix={<DollarOutlined />}
                        valueStyle={{ color: '#fff', fontSize: '24px', fontWeight: '900', fontFamily: 'monospace' }}
                    />
                    <div className="mt-2 flex items-center gap-2">
                        <Tag color="error" className="text-[8px] font-black">+12.4% vs last month</Tag>
                    </div>
                </div>
                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Statistic 
                        title={<span className="text-[10px] font-black text-white/40 uppercase tracking-widest">Token Consumption</span>}
                        value={4.2}
                        suffix="M"
                        valueStyle={{ color: '#fff', fontSize: '24px', fontWeight: '900', fontFamily: 'monospace' }}
                    />
                    <div className="mt-2 flex items-center gap-2">
                        <Text className="text-[9px] text-emerald-500 font-bold uppercase">Within limit</Text>
                    </div>
                </div>
                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Statistic 
                        title={<span className="text-[10px] font-black text-white/40 uppercase tracking-widest">Global Requests</span>}
                        value={12450}
                        valueStyle={{ color: '#fff', fontSize: '24px', fontWeight: '900', fontFamily: 'monospace' }}
                    />
                    <div className="mt-2 flex items-center gap-2">
                        <Tag color="emerald" className="text-[8px] font-black">99.9% Success Rate</Tag>
                    </div>
                </div>
            </div>

            <div className="glass-card p-6 border border-white/5 bg-black/40">
                <Title level={5} className="!text-white !text-[12px] uppercase tracking-widest flex items-center gap-2 mb-6">
                    <ThunderboltOutlined className="text-yellow-400" /> Resource Quota by Model
                </Title>
                <List
                    grid={{ gutter: 16, column: 2 }}
                    dataSource={[
                        { name: 'GPT-4o', usage: 75, color: '#10b981' },
                        { name: 'Claude 3.5 Sonnet', usage: 42, color: '#3b82f6' },
                        { name: 'Gemini 1.5 Pro', usage: 12, color: '#a855f7' },
                        { name: 'Llama 3 (Local)', usage: 98, color: '#ef4444' }
                    ]}
                    renderItem={item => (
                        <List.Item>
                            <div className="p-4 bg-white/5 border border-white/10 rounded-xl">
                                <div className="flex justify-between items-center mb-2">
                                    <Text className="text-white font-black text-[10px] uppercase">{item.name}</Text>
                                    <Text className="text-white/60 font-mono text-[10px]">{item.usage}%</Text>
                                </div>
                                <Progress 
                                    percent={item.usage} 
                                    showInfo={false} 
                                    strokeColor={item.color}
                                    trailColor="rgba(255,255,255,0.05)"
                                    size="small"
                                />
                            </div>
                        </List.Item>
                    )}
                />
            </div>
        </div>
    );
};

export default QuotaTraffic;
