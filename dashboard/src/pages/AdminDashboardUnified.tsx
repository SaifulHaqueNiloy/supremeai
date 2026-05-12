// AdminDashboardUnified.tsx - ULTRA-DENSE DARK COMMAND CENTER
// UNIFIED ADMIN DASHBOARD - Single Source of Truth Contract

import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Layout, Menu, Alert, Badge, Space, Tabs, Button, Modal, Input, message, Avatar, Dropdown, Typography, Divider, FloatButton, Progress, Tag, Tooltip, List } from 'antd';
import { 
    RobotOutlined, 
    DashboardOutlined, 
    CheckCircleOutlined, 
    SyncOutlined, 
    DesktopOutlined, 
    BulbOutlined, 
    BugOutlined, 
    NodeIndexOutlined, 
    ApiOutlined, 
    MenuUnfoldOutlined, 
    MenuFoldOutlined, 
    SearchOutlined, 
    BellOutlined, 
    UserOutlined, 
    SettingOutlined, 
    LogoutOutlined,
    GlobalOutlined,
    DatabaseOutlined,
    RocketOutlined,
    ClockCircleOutlined,
    CloudServerOutlined,
    InfoCircleOutlined,
    HistoryOutlined,
    MessageOutlined,
    ArrowUpOutlined,
    CheckCircleFilled,
    SafetyCertificateOutlined,
    ThunderboltOutlined,
    ChromeOutlined,
    MonitorOutlined,
    EyeOutlined,
    UploadOutlined,
    BarChartOutlined,
    FileTextOutlined,
    LoadingOutlined
} from '@ant-design/icons';
import { authUtils } from '../lib/authUtils';
import APIManagement from '../components/APIManagement';
import ScenarioOrchestration from '../components/ScenarioOrchestration';
import ThreeDashboard from '../components/ThreeDashboard';
import ChatWithAI from '../components/ChatWithAI';
import ConsensusMap from '../components/ConsensusMap';
import QuotaTraffic from '../components/QuotaTraffic';
import KnowledgeHub from '../components/KnowledgeHub';
import SelfHealingLogs from '../components/SelfHealingLogs';
import LearningHub from '../components/LearningHub';
import { notification } from 'antd';
import { Client } from '@stomp/stompjs';
import SockJS from 'sockjs-client';
import { 
  Chart as ChartJS, 
  ArcElement, 
  Tooltip as ChartTooltip, 
  Legend, 
  CategoryScale, 
  LinearScale, 
  BarElement,
  PointElement,
  LineElement,
  Filler
} from 'chart.js';
import { ApiResponse, DashboardContract } from '../types';
import { LogEntry } from '../components/NeuralTerminal';

// Register ChartJS
ChartJS.register(
  ArcElement, 
  ChartTooltip, 
  Legend, 
  CategoryScale, 
  LinearScale, 
  BarElement,
  PointElement,
  LineElement,
  Filler
);

const { Header, Content } = Layout;

// Helper icons for dynamic rendering if needed
const getIcon = (iconName: string) => {
    switch (iconName) {
        case 'DashboardOutlined': return <DashboardOutlined />;
        case 'RobotOutlined': return <RobotOutlined />;
        case 'BugOutlined': return <BugOutlined />;
        case 'ApiOutlined': return <ApiOutlined />;
        case 'DatabaseOutlined': return <DatabaseOutlined />;
        case 'GlobalOutlined': return <GlobalOutlined />;
        case 'CloudServerOutlined': return <CloudServerOutlined />;
        case 'ThunderboltOutlined': return <ThunderboltOutlined />;
        case 'RocketOutlined': return <RocketOutlined />;
        case 'HistoryOutlined': return <HistoryOutlined />;
        case 'FileTextOutlined': return <FileTextOutlined />;
        case 'SettingOutlined': return <SettingOutlined />;
        case 'MonitorOutlined': return <MonitorOutlined />;
        case 'EyeOutlined': return <EyeOutlined />;
        case 'UploadOutlined': return <UploadOutlined />;
        case 'SafetyCertificateOutlined': return <SafetyCertificateOutlined />;
        case 'NodeIndexOutlined': return <NodeIndexOutlined />;
        case 'DesktopOutlined': return <DesktopOutlined />;
        case 'ChromeOutlined': return <ChromeOutlined />;
        case 'BarChartOutlined': return <BarChartOutlined />;
        default: return <NodeIndexOutlined />;
    }
};

const AdminDashboardUnified: React.FC = () => {
    const { t } = useTranslation();
    const [contract, setContract] = useState<DashboardContract | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [chatVisible, setChatVisible] = useState(false);
    const [liveStream, setLiveStream] = useState<any[]>([]);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key.toLowerCase() === 'c' && (e.target as HTMLElement).tagName !== 'INPUT' && (e.target as HTMLElement).tagName !== 'TEXTAREA') {
                setChatVisible(prev => !prev);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    useEffect(() => {
        fetchContract();
        const interval = setInterval(fetchContract, 30000);
        
        const connectWebSocket = () => {
          try {
            const wsPath = import.meta.env.VITE_WS_URL || '/ws';
            const wsUrl = wsPath.startsWith('http') || wsPath.startsWith('ws') 
                ? wsPath 
                : `${window.location.protocol === 'https:' ? 'https:' : 'http'}://${window.location.host}${wsPath.startsWith('/') ? '' : '/'}${wsPath}`;
            
            const socket = new SockJS(wsUrl);
            const stompClient = new Client({
              webSocketFactory: () => socket,
              reconnectDelay: 5000,
              onConnect: () => {
                stompClient.subscribe('/topic/notifications', (message) => {
                  const data = JSON.parse(message.body);
                  const newLog: LogEntry = {
                    id: Math.random().toString(36).substr(2, 9),
                    timestamp: new Date().toLocaleTimeString(),
                    level: data.level || 'INFO',
                    source: data.source || 'SYSTEM',
                    message: data.message || JSON.stringify(data)
                  };
                  setLiveStream(prev => [newLog, ...prev].slice(0, 100));
                  
                  if (data.type === 'GITHUB_PIPELINE') {
                    if (data.status === 'success') {
                      notification.success({ message: '🚀 Deployment Successful', description: data.message });
                    } else if (data.status === 'failure') {
                      notification.error({ message: '🚨 Deployment Failed', description: data.message });
                    }
                  }
                });
              }
            });
            stompClient.activate();
            return () => stompClient.deactivate();
          } catch (err) {
            console.error("WebSocket connection error", err);
          }
        };
        
        const cleanup = connectWebSocket();
        return () => {
          clearInterval(interval);
          if (cleanup) cleanup();
        };
    }, []);

    const fetchContract = async () => {
        try {
            const resp = await authUtils.fetchWithAuth('/api/admin/dashboard/contract');
            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) {
                    authUtils.clearAuth();
                    window.location.href = '/admin';
                    return;
                }
                throw new Error('Failed to fetch contract');
            }
            const response = await resp.json() as ApiResponse<DashboardContract>;
            if (response.success && response.data) {
                setContract(response.data);
                setError(null);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        authUtils.clearAuth();
        window.location.reload();
    };



    if (loading) return (
        <div className="h-screen bg-[#050505] flex flex-col items-center justify-center font-mono">
            <div className="w-16 h-16 border-t-2 border-emerald-500 rounded-full animate-spin mb-4"></div>
            <div className="text-[10px] text-emerald-500 uppercase tracking-[0.3em] animate-pulse">INIT_COMMAND_CENTER</div>
        </div>
    );

    if (error || !contract) return <Alert message="System Offline" description={error} type="error" showIcon />;

    const stats = contract.stats;

    return (
        <Layout className="min-h-screen bg-[#050505] text-white">
            <Layout className="bg-transparent flex flex-col flex-1">
                <Header className="bg-black/90 backdrop-blur-2xl border-b border-white/5 h-16 px-6 flex items-center justify-between sticky top-0 z-50">
                    <div className="flex items-center gap-6">
                        <div className="flex flex-col gap-0.5 min-w-[200px]">
                            <span className="text-[12px] font-black uppercase tracking-[0.2em] text-white">SupremeAI Command Center</span>
                            <span className="text-[9px] font-black text-yellow-400 uppercase tracking-[0.3em]">AI_MODEL_SCENARIO_PROTOCOL</span>
                        </div>
                        <div className="h-8 w-[1px] bg-white/10 mx-2"></div>
                        <div className="hidden sm:flex flex-col">
                            <span className="text-[9px] text-cyan-400 uppercase font-black tracking-widest">REGISTRY</span>
                            <span className="text-[12px] text-white font-mono font-bold">OPTIMIZED_SYNC</span>
                        </div>
                        <div className="hidden md:flex flex-col">
                            <span className="text-[10px] text-white font-black uppercase tracking-tighter">SERVER_UPTIME</span>
                            <span className="text-[14px] text-yellow-400 font-mono font-bold">{stats.serverUptime || '00:00:00'}</span>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                        <div className="hidden lg:flex items-center gap-4 bg-white/10 border border-white/20 rounded-lg px-4 py-2">
                            <div className="flex flex-col">
                                <div className="flex items-center gap-2">
                                    <DatabaseOutlined className={`text-[12px] ${stats.databaseConnected ? 'text-emerald-500' : 'text-red-500'}`} />
                                    <span className="text-[10px] font-black uppercase text-white">DB: {stats.databaseConnected ? 'ONLINE' : 'OFFLINE'}</span>
                                </div>
                                <span className="text-[9px] text-cyan-400 font-mono font-bold text-left">{stats.databaseConnected ? 'SYNC_OPTIMAL' : 'RECONNECTING...'}</span>
                            </div>
                            <div className="w-[1px] h-8 bg-white/20"></div>
                            <div className="flex flex-col">
                                <div className="flex items-center gap-2">
                                    <CloudServerOutlined className={`text-[12px] ${stats.backendConnected ? 'text-emerald-500' : 'text-red-500'}`} />
                                    <span className="text-[10px] font-black uppercase text-white">SRV: {stats.backendConnected ? 'ACTIVE' : 'INACTIVE'}</span>
                                </div>
                                <span className="text-[9px] text-yellow-400 font-mono font-bold text-left">UPTIME_LIVE</span>
                            </div>
                        </div>
                        <div className="h-6 w-[1px] bg-white/5 mx-1"></div>
                        <div className="flex items-center gap-2 px-2 py-1 bg-white/[0.03] border border-white/10 rounded-full hover:bg-white/10 transition-all cursor-pointer">
                            <Avatar size={28} className="bg-white text-black border-2 border-white font-bold text-[12px]">AD</Avatar>
                            <span className="hidden sm:inline-block text-[12px] font-black uppercase tracking-tighter text-white mr-1">ADMIN</span>
                        </div>
                        <Tooltip title="Logout">
                            <Button 
                                type="text" 
                                icon={<LogoutOutlined />} 
                                onClick={handleLogout} 
                                className="text-white/40 hover:text-red-500 border border-white/5" 
                            />
                        </Tooltip>
                    </div>
                </Header>

                <Content className="p-6 overflow-y-auto min-h-[calc(100vh-64px)] bg-[#0c0c0c]">
                    <div className="space-y-6 max-w-[1600px] mx-auto animate-fade-in">
                        {/* Module Header */}
                        <div className="glass-card px-6 py-4 flex items-center justify-between border-l-4 border-emerald-500 bg-black/40">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.15)]">
                                    <RobotOutlined className="text-lg" />
                                </div>
                                <div className="flex flex-col">
                                    <h1 className="text-lg font-black uppercase tracking-[0.2em] text-white m-0">AI Model Scenario Management</h1>
                                    <p className="text-[10px] font-bold text-emerald-500/60 uppercase tracking-widest m-0">Orchestrate Communication, Execution & Voting Protocols</p>
                                </div>
                            </div>
                            <div className="hidden md:flex items-center gap-6">
                                <div className="flex flex-col items-end">
                                    <span className="text-[9px] font-black text-white/30 uppercase tracking-widest">Registry Status</span>
                                    <Tag color="emerald" className="m-0 text-[10px] font-black border-0 rounded bg-emerald-500/10 text-emerald-500">SYNC_OPTIMAL</Tag>
                                </div>
                            </div>
                        </div>

                        {/* Main AI Management View with Tabs */}
                        <div className="glass-card p-6 border border-white/5 bg-black/20">
                            <Tabs 
                                defaultActiveKey="registry" 
                                className="dark-tabs"
                                items={[
                                    {
                                        key: 'registry',
                                        label: (
                                            <span className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest">
                                                <DatabaseOutlined /> {t('dashboard.pillar_registry')}
                                            </span>
                                        ),
                                        children: <APIManagement />
                                    },
                                    {
                                        key: 'orchestration',
                                        label: (
                                            <span className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest">
                                                <NodeIndexOutlined /> {t('dashboard.pillar_orchestration')}
                                            </span>
                                        ),
                                        children: <ScenarioOrchestration />
                                    },
                                    {
                                        key: 'telemetry',
                                        label: (
                                            <span className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest">
                                                <BarChartOutlined /> {t('dashboard.pillar_telemetry')}
                                            </span>
                                        ),
                                        children: (
                                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
                                                <div className="lg:col-span-2 glass-card border border-white/5 overflow-hidden relative group">
                                                    <div className="absolute top-4 left-4 z-[110] flex flex-col gap-1">
                                                        <span className="text-[10px] font-black uppercase text-emerald-500 tracking-[0.2em] drop-shadow-md">System Neural Map</span>
                                                        <span className="text-[8px] text-white/40 uppercase font-mono drop-shadow-md">Real-time Node Interaction Stream</span>
                                                    </div>
                                                    <ThreeDashboard />
                                                </div>
                                                <div className="space-y-6 overflow-y-auto custom-scrollbar pr-2">
                                                    <div className="bg-white/[0.02] border border-white/5 p-4 rounded-xl">
                                                        <h4 className="text-[10px] font-black uppercase text-white/40 mb-4 tracking-widest flex items-center gap-2">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                                                            Neural Latency Matrix
                                                        </h4>
                                                        <div className="space-y-4">
                                                            {[
                                                                { label: 'GPT-4o', value: '142ms', color: 'emerald' },
                                                                { label: 'Claude 3.5', value: '189ms', color: 'blue' },
                                                                { label: 'Gemini 1.5', value: '256ms', color: 'purple' }
                                                            ].map((m, i) => (
                                                                <div key={i} className="flex flex-col gap-1">
                                                                    <div className="flex justify-between text-[10px] font-mono uppercase">
                                                                        <span className="text-white/60">{m.label}</span>
                                                                        <span className={`text-${m.color}-500`}>{m.value}</span>
                                                                    </div>
                                                                    <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                                                                        <div className={`h-full bg-${m.color}-500/50`} style={{ width: `${Math.random() * 40 + 60}%` }} />
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <div className="bg-white/[0.02] border border-white/5 p-4 rounded-xl">
                                                        <h4 className="text-[10px] font-black uppercase text-white/40 mb-4 tracking-widest flex items-center gap-2">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" />
                                                            Ensemble Voting
                                                        </h4>
                                                        <div className="py-8 text-center border border-dashed border-white/5 rounded-lg">
                                                            <SafetyCertificateOutlined className="text-2xl text-purple-500/20 mb-2" />
                                                            <p className="text-[9px] text-white/20 uppercase">Stream Waiting for active consensus session</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )
                                    },
                                    {
                                        key: 'consensus',
                                        label: (
                                            <span className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest">
                                                <SafetyCertificateOutlined /> {t('dashboard.pillar_consensus')}
                                            </span>
                                        ),
                                        children: <ConsensusMap />
                                    },
                                    {
                                        key: 'traffic',
                                        label: (
                                            <span className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest">
                                                <GlobalOutlined /> {t('dashboard.pillar_traffic')}
                                            </span>
                                        ),
                                        children: <QuotaTraffic />
                                    },
                                    {
                                        key: 'knowledge',
                                        label: (
                                            <span className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest">
                                                <BulbOutlined /> {t('dashboard.pillar_knowledge')}
                                            </span>
                                        ),
                                        children: <KnowledgeHub />
                                    },
                                    {
                                        key: 'logs',
                                        label: (
                                            <span className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest">
                                                <BugOutlined /> {t('dashboard.pillar_healing')}
                                            </span>
                                        ),
                                        children: <SelfHealingLogs />
                                    },
                                    {
                                        key: 'learning',
                                        label: (
                                            <span className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest">
                                                <RocketOutlined /> {t('dashboard.pillar_learning')}
                                            </span>
                                        ),
                                        children: <LearningHub />
                                    }
                                ]}
                            />
                        </div>
                    </div>
                </Content>

                <Modal
                    title={<span className="text-white text-[14px] font-black uppercase tracking-widest">Neural Link Chat</span>}
                    open={chatVisible}
                    onCancel={() => setChatVisible(false)}
                    footer={null}
                    width={800}
                    className="dark-modal"
                    styles={{ body: { padding: 0, backgroundColor: '#050505' } }}
                    centered
                >
                    <ChatWithAI />
                </Modal>
            </Layout>
        </Layout>
    );
};

export default AdminDashboardUnified;
