import React from 'react';
import { Typography, Progress, Button, Space, Card, Tag, Empty } from 'antd';
import { BulbOutlined, RocketOutlined, ExperimentOutlined, HistoryOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const LearningHub: React.FC = () => {
    return (
        <div className="p-4 animate-fade-in">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Title level={5} className="!text-white !text-[12px] uppercase tracking-widest flex items-center gap-2 mb-6">
                        <ExperimentOutlined className="text-orange-500" /> Active Fine-Tuning Jobs
                    </Title>
                    <div className="space-y-6">
                        <div className="p-5 bg-white/5 border border-white/10 rounded-2xl">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h4 className="text-white font-black text-[12px] uppercase m-0">Supreme-Coder-V2</h4>
                                    <span className="text-[9px] text-white/30 uppercase tracking-tighter">Base: Llama-3-70B • Dataset: Internal Repos</span>
                                </div>
                                <Tag color="orange" className="text-[9px] font-black uppercase border-0 bg-orange-500/10 text-orange-500">In Progress</Tag>
                            </div>
                            <div className="flex justify-between text-[10px] font-mono text-white/60 mb-2">
                                <span>Epoch 3/5</span>
                                <span>Loss: 0.142</span>
                            </div>
                            <Progress 
                                percent={65} 
                                status="active" 
                                strokeColor="#f97316" 
                                trailColor="rgba(255,255,255,0.05)"
                            />
                        </div>
                        
                        <Button 
                            block 
                            icon={<RocketOutlined />} 
                            className="h-12 bg-white/5 border-white/10 text-white font-black uppercase tracking-widest text-[10px] hover:bg-white/10"
                        >
                            Start New Training Session
                        </Button>
                    </div>
                </div>

                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Title level={5} className="!text-white !text-[12px] uppercase tracking-widest flex items-center gap-2 mb-6">
                        <HistoryOutlined className="text-white/40" /> Model Performance History
                    </Title>
                    <Empty 
                        image={Empty.PRESENTED_IMAGE_SIMPLE} 
                        description={<span className="text-[10px] text-white/20 uppercase tracking-widest font-black">No completed training jobs recorded</span>}
                        className="py-12"
                    />
                </div>
            </div>
        </div>
    );
};

export default LearningHub;
