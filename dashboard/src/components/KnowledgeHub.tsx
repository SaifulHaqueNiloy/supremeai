import React from 'react';
import { Typography, Input, Button, Tag, Space, List, Avatar } from 'antd';
import { DatabaseOutlined, SearchOutlined, CloudUploadOutlined, FilePdfOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const KnowledgeHub: React.FC = () => {
    return (
        <div className="p-4 animate-fade-in">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 glass-card p-6 border border-white/5 bg-black/40">
                    <div className="flex items-center justify-between mb-6">
                        <Title level={5} className="!text-white !text-[12px] uppercase tracking-widest flex items-center gap-2 m-0">
                            <DatabaseOutlined className="text-cyan-500" /> Vector Knowledge Base
                        </Title>
                        <Button 
                            icon={<CloudUploadOutlined />} 
                            className="bg-cyan-500/10 border-cyan-500/20 text-cyan-500 text-[9px] font-black uppercase"
                        >
                            Ingest Data
                        </Button>
                    </div>
                    
                    <div className="relative mb-6">
                        <Input 
                            prefix={<SearchOutlined className="text-white/20" />} 
                            placeholder="Semantic search across knowledge corpus..."
                            className="dark-input h-12 text-[12px] font-mono"
                        />
                    </div>

                    <List
                        itemLayout="horizontal"
                        dataSource={[
                            { title: 'Project_Alpha_Spec.pdf', size: '2.4 MB', chunks: 142, date: '2026-05-10' },
                            { title: 'User_Behavior_Patterns.csv', size: '15.8 MB', chunks: 1250, date: '2026-05-09' },
                            { title: 'SupremeAI_Internal_Wiki', size: '540 KB', chunks: 88, date: '2026-05-11' }
                        ]}
                        renderItem={item => (
                            <List.Item className="border-b border-white/5 px-4 hover:bg-white/[0.02] transition-all cursor-pointer rounded-lg mb-2">
                                <List.Item.Meta
                                    avatar={<Avatar icon={<FilePdfOutlined />} className="bg-red-500/10 text-red-500" />}
                                    title={<Text className="text-white font-bold text-[11px]">{item.title}</Text>}
                                    description={<Text className="text-white/30 text-[9px] uppercase">{item.size} • {item.chunks} Neural Chunks • Synced {item.date}</Text>}
                                />
                                <Tag color="cyan" className="text-[8px] font-black border-0 bg-cyan-500/10 text-cyan-500 uppercase">Vectorized</Tag>
                            </List.Item>
                        )}
                    />
                </div>

                <div className="glass-card p-6 border border-white/5 bg-black/40">
                    <Title level={5} className="!text-white !text-[12px] uppercase tracking-widest flex items-center gap-2 mb-6">
                        System RAG Config
                    </Title>
                    <div className="space-y-4">
                        <div className="p-4 bg-white/5 border border-white/10 rounded-xl">
                            <Text className="text-[9px] text-white/40 uppercase block mb-1">Top-K Retrieval</Text>
                            <Text className="text-[14px] text-white font-mono font-bold">5 Chunks</Text>
                        </div>
                        <div className="p-4 bg-white/5 border border-white/10 rounded-xl">
                            <Text className="text-[9px] text-white/40 uppercase block mb-1">Similarity Threshold</Text>
                            <Text className="text-[14px] text-white font-mono font-bold">0.82</Text>
                        </div>
                        <div className="p-4 bg-white/5 border border-white/10 rounded-xl">
                            <Text className="text-[9px] text-white/40 uppercase block mb-1">Embedding Model</Text>
                            <Text className="text-[12px] text-cyan-400 font-mono font-bold">text-embedding-3-small</Text>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default KnowledgeHub;
