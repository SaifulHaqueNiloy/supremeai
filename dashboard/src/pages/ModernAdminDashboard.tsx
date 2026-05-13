// ModernAdminDashboard.tsx - Cinematic AI Command Center
import React, { useState, useEffect, useRef } from 'react';
import { Layout, Menu, Button, Avatar, theme, Badge, Typography, Space, Tooltip, Progress, ConfigProvider, Drawer, message, Tag } from 'antd';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DashboardOutlined,
  RobotOutlined,
  CodeOutlined,
  BarChartOutlined,
  SettingOutlined,
  BulbOutlined,
  LogoutOutlined,
  LoginOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MenuOutlined,
  ThunderboltOutlined,
  GlobalOutlined,
  SafetyOutlined,
  ClusterOutlined,
  HddOutlined,
  LockOutlined,
  ApiOutlined,
  UserOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  LineChartOutlined,
  ChromeOutlined,
  PieChartOutlined,
  MobileOutlined,
  BellOutlined,
  SecurityScanOutlined,
  AuditOutlined,
  ToolOutlined,
  ExclamationCircleOutlined,
  HomeOutlined,
} from '@ant-design/icons';
import { Breadcrumb, Modal } from 'antd';
import { useRole } from '../contexts/RoleContext';
import { authUtils } from '../lib/authUtils';
import ChatWithAI from '../components/ChatWithAI';
import UserSettings from '../components/UserSettings';
import UserProfile from '../components/UserProfile';
import ActivityFeed from '../components/ActivityFeed';
import { ConnectionIndicator } from '../components/FeedbackSystem';
import AdminProjects from './AdminProjects';
import AdminSettings from './AdminSettings';
import AdminUsers from './AdminUsers';
import AdminProviders from './AdminProviders';
import AdminLogs from './AdminLogs';
import AdminMonitoring from './AdminMonitoring';
import AdminLearning from './AdminLearning';
import AdminSecurity from './AdminSecurity';
import AdminRules from './AdminRules';
import AdminAnalytics from './AdminAnalytics';
import AdminVPN from './AdminVPN';
import AdminBrowser from './AdminBrowser';
import AdminQuotas from './AdminQuotas';
import AdminNotifications from './AdminNotifications';
import AdminPerformance from './AdminPerformance';
import AdminBackup from './AdminBackup';
import AdminOCR from './AdminOCR';
import AdminSimulator from './AdminSimulator';
import AdminReverseEngineer from './AdminReverseEngineer';
import AdminReports from './AdminReports';

const { Header, Content, Sider } = Layout;
const { Text, Title } = Typography;

// --- Sub-components for Cinematic Feel ---

const Waveform = () => (
  <div className="waveform-container">
    {[...Array(12)].map((_, i) => (
      <div 
        key={i} 
        className="wave-bar" 
        style={{ animationDelay: `${i * 0.1}s` }} 
      />
    ))}
  </div>
);

const NeuralGraph = () => (
  <svg width="100%" height="150" viewBox="0 0 400 150">
    <circle cx="50" cy="75" r="5" fill="var(--neon-blue)" className="pulsing" />
    <circle cx="150" cy="40" r="4" fill="var(--neon-purple)" className="pulsing" />
    <circle cx="150" cy="110" r="4" fill="var(--neon-purple)" className="pulsing" />
    <circle cx="250" cy="75" r="5" fill="var(--neon-blue)" className="pulsing" />
    <circle cx="350" cy="75" r="8" fill="var(--neon-blue)" className="pulsing" />
    
    <line x1="50" y1="75" x2="150" y2="40" className="neural-line" />
    <line x1="50" y1="75" x2="150" y2="110" className="neural-line" />
    <line x1="150" y1="40" x2="250" y2="75" className="neural-line" />
    <line x1="150" y1="110" x2="250" y2="75" className="neural-line" />
    <line x1="250" y1="75" x2="350" y2="75" className="neural-line" />
  </svg>
);

const DataStream = () => {
  const [streams, setStreams] = useState<any[]>([]);
  
  useEffect(() => {
    const newStreams = Array.from({ length: 20 }).map((_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      delay: `${Math.random() * 5}s`,
      duration: `${5 + Math.random() * 10}s`,
      content: Math.random().toString(2).substring(2, 10)
    }));
    setStreams(newStreams);
  }, []);

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 0 }}>
      {streams.map(s => (
        <div 
          key={s.id} 
          className="data-stream" 
          style={{ left: s.left, animationDelay: s.delay, animationDuration: s.duration }}
        >
          {s.content}
        </div>
      ))}
    </div>
  );
};

const TerminalLogs = () => {
  const [logs, setLogs] = useState<string[]>([
    "[SYSTEM] Initializing SupremeAI Kernel v4.2.0...",
    "[NETWORK] Establishing secure uplink to Node-07...",
    "[AUTH] Permission level: ADMINISTRATIVE",
    "[SECURITY] Firewall active. Zero-day monitoring enabled.",
  ]);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      const messages = [
        `[PROCESS] Request handled in ${Math.floor(Math.random() * 50)}ms`,
        "[DB] Firestore sync complete",
        "[AI] Model weight recalibration successful",
        "[USER] New session detected in SG region",
        "[WARN] Latency spike detected in EU-West-2",
        "[SYSTEM] Memory optimization routine started",
      ];
      setLogs(prev => [...prev.slice(-15), messages[Math.floor(Math.random() * messages.length)]]);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="terminal-box" style={{ height: 250 }}>
      <div className="terminal-header">
        <span>কোর_লগ_স্ট্রিম (CORE_LOGS)</span>
        <span>{new Date().toLocaleTimeString()}</span>
      </div>
      <div style={{ overflowY: 'auto', height: '180px' }}>
        {logs.map((log, i) => (
          <div key={i} style={{ marginBottom: 4, opacity: (i + 1) / logs.length, fontSize: 11 }}>
            <span style={{ color: log.includes('WARN') ? 'var(--warning)' : log.includes('SYSTEM') ? 'var(--neon-purple)' : 'var(--neon-blue)' }}>{"> "}</span>
            {log}
          </div>
        ))}
        <div ref={logEndRef} />
        <span className="terminal-cursor" />
      </div>
    </div>
  );
};

const NeuralCore = () => (
  <div className="neural-node pulsing">
    <svg viewBox="0 0 200 200">
      <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#00f3ff', stopOpacity: 1 }} />
          <stop offset="100%" style={{ stopColor: '#bc13fe', stopOpacity: 1 }} />
        </linearGradient>
      </defs>
      <circle cx="100" cy="100" r="80" fill="none" stroke="url(#grad1)" strokeWidth="0.5" strokeDasharray="10 5" className="rotating" />
      <circle cx="100" cy="100" r="60" fill="none" stroke="url(#grad1)" strokeWidth="1" strokeDasharray="5 5" className="rotating" style={{ animationDirection: 'reverse' }} />
      <path d="M100 40 L100 160 M40 100 L160 100" stroke="url(#grad1)" strokeWidth="0.5" opacity="0.3" />
      <circle cx="100" cy="100" r="10" fill="url(#grad1)" className="pulsing" />
    </svg>
  </div>
);

const RestrictedDemo: React.FC<{title: string; description: string; icon: React.ReactNode}> = ({ title, description, icon }) => (
  <motion.div 
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 1, scale: 1 }}
    className="glass-panel"
    style={{
      padding: '80px 40px',
      textAlign: 'center',
      marginTop: '40px',
      maxWidth: '800px',
      margin: '40px auto',
      border: '1px solid rgba(255, 152, 0, 0.3)',
      boxShadow: '0 0 40px rgba(255, 152, 0, 0.1)'
    }}
  >
    <div className="pulsing" style={{ marginBottom: 32 }}>
      <LockOutlined style={{ fontSize: 80, color: '#f59e0b', opacity: 0.8 }} />
    </div>
    <Title level={2} style={{ color: 'var(--warning)', marginBottom: 16, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.2em' }}>
      অ্যাক্সেস প্রত্যাখ্যান করা হয়েছে
    </Title>
    <p style={{ color: 'var(--text-dim)', maxWidth: 600, margin: '0 auto 40px', fontSize: 18, lineHeight: 1.8 }}>
      নিরাপত্তা প্রোটোকল <Text code style={{ color: 'var(--warning)' }}>LVL-4</Text> সক্রিয়। 
      মডিউল <Text strong style={{ color: 'var(--text-main)' }}>{title}</Text> শুধুমাত্র প্রশাসকদের জন্য এনক্রিপ্ট করা হয়েছে।
    </p>
    <Space size="large">
      <Button
        className="cyber-button"
        icon={<SecurityScanOutlined />}
        onClick={() => window.location.href = '/login'}
        style={{ height: 'auto', padding: '12px 30px' }}
      >
        অ্যাডমিন যাচাই করুন
      </Button>
      <Button
        ghost
        onClick={() => window.location.href = '/'}
        style={{ height: 'auto', padding: '12px 30px', borderRadius: 4, borderColor: 'rgba(255,255,255,0.3)' }}
      >
        পিছনে যান
      </Button>
    </Space>
  </motion.div>
);

// --- Main Dashboard Component ---

export default function ModernAdminDashboard() {
  const { isAdmin, isAuthenticated, user, refreshUser } = useRole();
  const [collapsed, setCollapsed] = useState(false);
  const [activeKey, setActiveKey] = useState('dashboard');
  const [darkMode, setDarkMode] = useState(true);
  const [chatFont, setChatFont] = useState(localStorage.getItem('chatFont') || 'font-mono');
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogout = () => {
    Modal.confirm({
      title: <Text style={{ color: 'var(--text-main)', fontSize: 18, fontWeight: 700 }}>লগআউট নিশ্চিত করুন</Text>,
      icon: <ExclamationCircleOutlined style={{ color: 'var(--warning)', fontSize: 24 }} />,
      content: (
        <div style={{ marginTop: 12 }}>
          <Text style={{ color: 'var(--text-dim)' }}>আপনি কি নিশ্চিতভাবে আপনার বর্তমান সেশনটি শেষ করতে চান? সকল সেভ না করা পরিবর্তন হারিয়ে যেতে পারে।</Text>
        </div>
      ),
      okText: 'লগআউট',
      cancelText: 'ফিরে যান',
      centered: true,
      okButtonProps: { 
        className: 'cyber-button', 
        style: { background: 'var(--warning)', border: 'none', color: '#000' } 
      },
      cancelButtonProps: { 
        style: { background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)' } 
      },
      onOk: async () => {
        try {
          await authUtils.logout();
          refreshUser();
          message.success('নিরাপদে লগআউট করা হয়েছে।');
        } catch (error) {
          message.error('লগআউট করতে সমস্যা হয়েছে।');
        }
      },
    });
  };

  const getBreadcrumbs = () => {
    const activeItem = allMenuItems.find(item => item.key === activeKey);
    return [
      { title: <><HomeOutlined /> <span>কমান্ড</span></>, key: 'home' },
      { title: activeItem?.label || 'ড্যাশবোর্ড', key: 'active' }
    ];
  };

  const allMenuItems = [
    // Universal tabs (all roles)
    { key: 'dashboard', icon: <DashboardOutlined />, label: 'কমান্ড সেন্টার', roles: ['guest', 'user', 'admin'] },
    { key: 'ai', icon: <RobotOutlined />, label: 'নিউরাল চ্যাট', roles: ['guest', 'user', 'admin'] },
    { key: 'projects', icon: <CodeOutlined />, label: 'ডিপ্লয়মেন্টস', roles: ['user', 'admin'] },
    { key: 'settings', icon: <SettingOutlined />, label: 'কনফিগ', roles: ['guest', 'user', 'admin'] },
    
    // Admin-only tabs
    { key: 'providers', icon: <ApiOutlined />, label: 'AI প্রোভাইডার', roles: ['admin'] },
    { key: 'users', icon: <UserOutlined />, label: 'ইউজার ম্যানেজমেন্ট', roles: ['admin'] },
    { key: 'monitoring', icon: <HddOutlined />, label: 'সিস্টেম মনিটরিং', roles: ['admin'] },
    { key: 'learning', icon: <BulbOutlined />, label: 'লার্নিং ম্যানেজমেন্ট', roles: ['admin'] },
    { key: 'security', icon: <SecurityScanOutlined />, label: 'সিকিউরিটি', roles: ['admin'] },
    { key: 'rules', icon: <AuditOutlined />, label: 'সিস্টেম রুলস', roles: ['admin'] },
    { key: 'analytics', icon: <LineChartOutlined />, label: 'এনালাইটিক্স', roles: ['admin'] },
    { key: 'logs', icon: <FileTextOutlined />, label: 'সিস্টেম লগ', roles: ['admin'] },
    { key: 'vpn', icon: <GlobalOutlined />, label: 'VPN কানেকশন', roles: ['admin'] },
    { key: 'browser', icon: <ChromeOutlined />, label: 'ব্রাউজার', roles: ['guest', 'user', 'admin'] },
    { key: 'quotas', icon: <PieChartOutlined />, label: 'কোটা ম্যানেজমেন্ট', roles: ['admin'] },
    { key: 'simulator', icon: <MobileOutlined />, label: 'সিমুলেটর', roles: ['guest', 'user', 'admin'] },
    { key: 'reverse', icon: <CodeOutlined />, label: 'রিভার্স ইঞ্জিনিয়ারিং', roles: ['admin'] },
    { key: 'notifications', icon: <BellOutlined />, label: 'নোটিফিকেশন', roles: ['admin'] },
    { key: 'reports', icon: <BarChartOutlined />, label: 'রিপোর্টস', roles: ['admin'] },
    { key: 'performance', icon: <ClusterOutlined />, label: 'পারফরম্যান্স', roles: ['admin'] },
    { key: 'backup', icon: <DatabaseOutlined />, label: 'ব্যাকআপ', roles: ['admin'] },
    { key: 'ocr', icon: <FileTextOutlined />, label: 'OCR টুল', roles: ['admin'] },
  ];

  const currentRole = isAdmin ? 'admin' : (isAuthenticated ? 'user' : 'guest');
  const menuItems = allMenuItems.filter(item => Array.isArray(item.roles) && item.roles.includes(currentRole));

  const renderContent = () => {
    const activeItem = allMenuItems.find(item => item.key === activeKey);
    const hasAccess = activeItem?.roles.includes(currentRole);

    console.log(`[Navigation] ActiveKey: ${activeKey}, Role: ${currentRole}, HasAccess: ${hasAccess}`);

    if (!hasAccess && activeKey !== 'dashboard') {
      return <RestrictedDemo title={activeItem?.label || "Unknown"} description="Security clearance insufficient." icon={<LockOutlined />} />;
    }

    return (
      <div style={{ height: '100%', padding: '0 0 40px 0' }}>
        {(() => {
          switch (activeKey) {
            case 'dashboard': return <DashboardHome isAdmin={isAdmin} setActiveKey={setActiveKey} />;
            case 'ai': return <ChatWithAI chatFont={chatFont} />;
            case 'projects': return <AdminProjects />;
            
            // Admin tabs
            case 'providers': return <AdminProviders />;
            case 'users': return <AdminUsers />;
            case 'monitoring': return <AdminMonitoring />;
            case 'learning': return <AdminLearning />;
            case 'security': return <AdminSecurity />;
            case 'rules': return <AdminRules />;
            case 'analytics': return <AdminAnalytics />;
            case 'logs': return <AdminLogs />;
            case 'vpn': return <AdminVPN />;
            case 'browser': return <AdminBrowser />;
             case 'quotas': return <AdminQuotas />;
             case 'simulator': return <AdminSimulator />;
             case 'reverse': return <AdminReverseEngineer />;
             case 'notifications': return <AdminNotifications />;
            case 'reports': return <AdminReports />;
            case 'performance': return <AdminPerformance />;
            case 'backup': return <AdminBackup />;
            case 'ocr': return <AdminOCR />;
            
            case 'settings': return isAdmin ? <AdminSettings darkMode={darkMode} setDarkMode={setDarkMode} chatFont={chatFont} setChatFont={setChatFont} /> : <UserSettings darkMode={darkMode} setDarkMode={setDarkMode} chatFont={chatFont} setChatFont={setChatFont} />;
            default: return <DashboardHome isAdmin={isAdmin} setActiveKey={setActiveKey} />;
          }
        })()}
      </div>
    );
  };


  if (!mounted) return null;

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#00f3ff',
          colorBgBase: '#020205',
          colorTextBase: '#ffffff',
          borderRadius: 8,
          colorLink: '#00f3ff',
        },
        components: {
          Layout: {
            colorBgHeader: 'rgba(0,0,0,0.6)',
            colorBgBody: 'transparent',
            colorBgTrigger: '#00f3ff',
          },
          Menu: {
            colorItemBg: 'transparent',
            colorItemText: '#cbd5e1',
            colorItemTextSelected: '#00f3ff',
            colorItemBgSelected: 'rgba(0, 243, 255, 0.1)',
          },
          Progress: {
            remainingColor: 'rgba(255,255,255,0.05)',
          },
          Table: {
            colorBgContainer: 'rgba(13, 13, 18, 0.5)',
            colorTextHeading: '#00f3ff',
          }
        }
      }}
    >
      <Layout className="animated-bg" style={{ minHeight: '100vh', position: 'relative' }}>
        <div className="bg-grid" />
        <div className="hex-grid" />
        <DataStream />
        <div className="scanline" />
        
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          theme="dark"
          className="glass-panel responsive-sidebar"
          width={260}
          breakpoint="lg"
          collapsedWidth={0}
          style={{
            margin: 16,
            borderRadius: 16,
            height: 'calc(100vh - 32px)',
            border: '1px solid rgba(255,255,255,0.05)',
            background: 'rgba(0,0,0,0.6)',
            zIndex: 10
          }}
        >
          <div style={{
            height: 80,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0 24px',
            borderBottom: '1px solid rgba(255,255,255,0.05)'
          }}>
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              style={{
                background: 'linear-gradient(135deg, var(--neon-blue), var(--neon-purple))',
                padding: '10px 16px',
                borderRadius: 8,
                boxShadow: '0 0 20px rgba(0, 243, 255, 0.4)',
                color: '#000',
                fontWeight: 900,
                fontSize: collapsed ? 14 : 20,
                letterSpacing: 3,
                fontFamily: 'JetBrains Mono, monospace'
              }}
            >
              {collapsed ? 'S' : 'SUPREME'}
            </motion.div>
          </div>
          
          <Menu
            mode="inline"
            selectedKeys={[activeKey]}
            onClick={(e) => setActiveKey(e.key)}
            items={menuItems}
            theme="dark"
            style={{ background: 'transparent', borderRight: 'none', marginTop: 24 }}
          />
          
          {!collapsed && (
            <div style={{ position: 'absolute', bottom: 80, left: 24, right: 24 }}>
              <div style={{ padding: 16, background: 'rgba(255,255,255,0.03)', borderRadius: 12, border: '1px solid rgba(255,255,255,0.05)' }}>
                <Text style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: 1 }}>অথোরাইজেশন ট্রেস</Text>
                <div style={{ display: 'flex', gap: 4, marginTop: 12 }}>
                  {[1,2,3,4,5,6,7,8].map(i => (
                    <div key={i} style={{ 
                      height: 6, 
                      flex: 1, 
                      background: i <= (isAdmin ? 8 : (isAuthenticated ? 4 : 1)) ? 'var(--neon-blue)' : 'rgba(255,255,255,0.05)',
                      boxShadow: i <= (isAdmin ? 8 : (isAuthenticated ? 4 : 1)) ? '0 0 10px var(--neon-blue)' : 'none',
                      borderRadius: 1
                    }} />
                  ))}
                </div>
              </div>
            </div>
          )}
        </Sider>

        <Drawer
          title={null}
          placement="left"
          closable={false}
          open={mobileDrawerOpen}
          onClose={() => setMobileDrawerOpen(false)}
          className="mobile-drawer"
          width={260}
          bodyStyle={{ padding: 0, background: 'rgba(0,0,0,0.8)' }}
        >
          <div style={{
            height: 80,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0 24px',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            background: 'linear-gradient(135deg, var(--neon-blue), var(--neon-purple))',
            color: '#000',
            fontWeight: 900,
            fontSize: 20,
            letterSpacing: 3,
            fontFamily: 'JetBrains Mono, monospace'
          }}>
            SUPREME
          </div>

          <Menu
            mode="inline"
            selectedKeys={[activeKey]}
            onClick={(e) => {
              setActiveKey(e.key);
              setMobileDrawerOpen(false);
            }}
            items={menuItems}
            theme="dark"
            style={{ background: 'transparent', borderRight: 'none', marginTop: 24 }}
          />

          <div style={{ position: 'absolute', bottom: 80, left: 24, right: 24 }}>
            <div style={{ padding: 16, background: 'rgba(255,255,255,0.03)', borderRadius: 12, border: '1px solid rgba(255,255,255,0.05)' }}>
              <Text style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: 1 }}>অথোরাইজেশন ট্রেস</Text>
              <div style={{ display: 'flex', gap: 4, marginTop: 12 }}>
                {[1,2,3,4,5,6,7,8].map(i => (
                  <div key={i} style={{
                    height: 6,
                    flex: 1,
                    background: i <= (isAdmin ? 8 : (isAuthenticated ? 4 : 1)) ? 'var(--neon-blue)' : 'rgba(255,255,255,0.05)',
                    boxShadow: i <= (isAdmin ? 8 : (isAuthenticated ? 4 : 1)) ? '0 0 10px var(--neon-blue)' : 'none',
                    borderRadius: 1
                  }} />
                ))}
              </div>
            </div>
          </div>
        </Drawer>

        <Layout className="responsive-layout" style={{ background: 'transparent' }}>
          <Header className="responsive-header" style={{
            padding: '0 40px',
            background: 'rgba(0,0,0,0.4)',
            backdropFilter: 'blur(20px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            height: 80,
            zIndex: 5
          }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="mobile-menu-button"
              style={{ color: 'rgba(255,255,255,0.6)', fontSize: 20 }}
            />
            
            <div className="header-breadcrumbs" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <Breadcrumb 
                items={getBreadcrumbs()} 
                style={{ color: 'var(--text-dim)', fontSize: '14px' }}
              />
              <div className="divider" style={{ width: '1px', height: '24px', background: 'rgba(255,255,255,0.1)' }} />
              <ConnectionIndicator />
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 12 }}>
                  {!isAuthenticated && <Tag color="warning" style={{ margin: 0, borderRadius: 4, background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#f59e0b' }}>সীমাবদ্ধ_অ্যাক্সেস</Tag>}
                  <Text style={{ display: 'block', color: 'var(--text-main)', fontWeight: 600, fontSize: 15, letterSpacing: 1 }}>
                    {isAdmin ? 'সিস্টেম আর্কিটেক্ট' : (isAuthenticated ? 'নিউরাল অপারেটর' : 'গেস্ট এনটিটি')}
                  </Text>
                </div>
                <Text style={{ fontSize: 12, color: isAdmin ? 'var(--success)' : (isAuthenticated ? 'var(--neon-purple)' : 'var(--text-dim)'), fontFamily: 'var(--font-mono)' }}>
                  {isAuthenticated ? `AUTH: ${user?.email || 'Authenticated'}` : 'MODE: GUEST_BYPASS'}
                </Text>
              </div>

              <Space>
                {!isAuthenticated && (
                  <Button
                    type="primary"
                    size="small"
                    icon={<LoginOutlined />}
                    onClick={() => window.location.href = '/login'}
                    style={{
                      background: 'var(--neon-blue)',
                      border: 'none',
                      fontSize: '12px'
                    }}
                  >
                    লগইন
                  </Button>
                )}

                <Tooltip title={isAuthenticated ? "লগআউট করুন" : "গেস্ট মোড থেকে সুইচ করুন"}>
                  <Avatar
                    size={52}
                    icon={isAuthenticated ? <LogoutOutlined /> : <RobotOutlined />}
                    className={isAuthenticated ? "glow-blue" : "glow-purple"}
                    style={{
                      background: isAuthenticated ? 'rgba(0, 243, 255, 0.1)' : 'rgba(188, 19, 254, 0.1)',
                      border: `1px solid ${isAuthenticated ? 'var(--neon-blue)' : 'var(--neon-purple)'}`,
                      color: isAuthenticated ? 'var(--neon-blue)' : 'var(--neon-purple)',
                      cursor: 'pointer',
                      transition: 'all 0.3s'
                    }}
                    onClick={() => {
                      if (isAuthenticated) {
                        handleLogout();
                      } else {
                        window.location.href = '/login';
                      }
                    }}
                  />
                </Tooltip>
              </Space>
            </div>
          </Header>
          
          <Content style={{ overflow: 'auto', position: 'relative' }}>
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

// --- Moved DashboardHome outside to prevent re-mounting on toggle ---
function DashboardHome({ isAdmin, setActiveKey }: { isAdmin: boolean, setActiveKey: (key: string) => void }) {
  return (
    <div className="dashboard-container" style={{ padding: 'clamp(20px, 5vw, 40px)', position: 'relative', zIndex: 1 }}>
      <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 48 }}>
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="title-section"
        >
          <Title level={1} className="text-gradient text-high-vis main-title" style={{ margin: 0, fontSize: 'clamp(32px, 8vw, 48px)', fontWeight: 800, letterSpacing: '-1px' }}>
            SupremeAI অর্কেস্ট্রেটর
          </Title>
          <Space align="center" style={{ marginTop: 8 }} className="status-info">
            <div className="cyber-badge" style={{ background: 'var(--success)', color: '#000', fontWeight: 'bold' }}>সক্রিয়</div>
            <Text style={{ color: 'var(--text-main)', fontSize: 14, letterSpacing: 1, textTransform: 'uppercase', fontWeight: 500 }}>
              কার্নেল আইডি: <Text style={{ color: 'var(--neon-blue)', fontWeight: 'bold' }}>SAI-X900</Text> | ভার্সন: <Text style={{ color: 'var(--neon-purple)', fontWeight: 'bold' }}>4.2.0</Text>
            </Text>
          </Space>
        </motion.div>

        <div className="neural-core-container">
           <NeuralCore />
        </div>
      </div>

      <div 
        className="dashboard-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: 32
        }}
      >
        {/* Main Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          <motion.div whileHover={{ scale: 1.02 }} className="ai-card" style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24, alignItems: 'center' }}>
              <RobotOutlined style={{ fontSize: 32, color: 'var(--neon-blue)' }} />
              <Waveform />
            </div>
            <Title level={3} style={{ color: 'var(--text-main)', marginBottom: 12 }}>নিউরাল নেক্সাস</Title>
            <p style={{ color: 'var(--text-dim)', lineHeight: 1.8, fontSize: 15, marginBottom: 24 }}>
              সিস্টেম ইন্টেলিজেন্সের সাথে সরাসরি যোগাযোগ করুন। মাল্টি-মোডাল ফ্লো এবং এজেন্টিক যুক্তি কার্যকর করুন।
            </p>
            <Button className="cyber-button" icon={<ThunderboltOutlined />} onClick={() => setActiveKey('ai')} style={{ width: '100%' }}>
              লিঙ্ক শুরু করুন
            </Button>
          </motion.div>

          <ActivityFeed />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {/* User Profile Summary */}
          <UserProfile />

          {/* Dynamic Metrics */}
          <motion.div className="ai-card glass-panel" style={{ background: 'rgba(188, 19, 254, 0.08)' }}>
             <Title level={4} style={{ color: 'var(--text-main)', marginBottom: 20 }}>সিস্টেম লোড ম্যাট্রিক্স</Title>
             <div style={{ marginBottom: 20 }}>
               <div style={{ display:'flex', justifyContent:'space-between', marginBottom: 8 }}><Text style={{color:'var(--text-dim)'}}>নিউরাল প্রসেসিং (NPU)</Text><Text style={{color:'var(--neon-purple)'}}>64%</Text></div>
               <Progress percent={64} status="active" strokeColor="var(--neon-purple)" trailColor="rgba(255,255,255,0.05)" showInfo={false} />
             </div>
             <div style={{ marginBottom: 20 }}>
               <div style={{ display:'flex', justifyContent:'space-between', marginBottom: 8 }}><Text style={{color:'var(--text-dim)'}}>মেমোরি অ্যালোকোশন</Text><Text style={{color:'var(--neon-blue)'}}>42%</Text></div>
               <Progress percent={42} status="active" strokeColor="var(--neon-blue)" trailColor="rgba(255,255,255,0.05)" showInfo={false} />
             </div>
             <div>
               <div style={{ display:'flex', justifyContent:'space-between', marginBottom: 8 }}><Text style={{color:'var(--text-dim)'}}>কোয়ান্টাম ক্যাশে</Text><Text style={{color:'var(--success)'}}>89%</Text></div>
               <Progress percent={89} status="active" strokeColor="var(--success)" trailColor="rgba(255,255,255,0.05)" showInfo={false} />
             </div>
          </motion.div>

          {/* Quick Actions */}
          <div className="quick-actions" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
             <Button className="glass-panel" icon={<GlobalOutlined />} onClick={() => setActiveKey('vpn')} style={{ height: 80, border: '1px solid rgba(255,255,255,0.1)', color:'#fff' }}>নোডস</Button>
             <Button className="glass-panel" icon={<SafetyOutlined />} onClick={() => setActiveKey('security')} style={{ height: 80, border: '1px solid rgba(255,255,255,0.1)', color:'#fff' }}>সিকিউর</Button>
             <Button className="glass-panel" icon={<BarChartOutlined />} onClick={() => setActiveKey('monitoring')} style={{ height: 80, border: '1px solid rgba(255,255,255,0.1)', color:'#fff' }}>মেট্রিক্স</Button>
             <Button className="glass-panel" icon={<ToolOutlined />} onClick={() => setActiveKey('settings')} style={{ height: 80, border: '1px solid rgba(255,255,255,0.1)', color:'#fff' }}>শেল</Button>
          </div>
        </div>
      </div>
      
      {/* Statistics Bar */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="glass-panel stat-bar" 
        style={{ marginTop: 40, padding: '24px clamp(24px, 5vw, 40px)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
      >
        <div style={{ display: 'flex', gap: 60 }}>
          <div>
            <Text style={{ display: 'block', color: 'var(--text-dim)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1 }}>আপটাইম</Text>
            <Title level={4} style={{ color: 'var(--neon-blue)', margin: 0 }}>99.998%</Title>
          </div>
          <div>
            <Text style={{ display: 'block', color: 'var(--text-dim)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1 }}>ল্যাটেন্সি</Text>
            <Title level={4} style={{ color: 'var(--neon-purple)', margin: 0 }}>24ms</Title>
          </div>
          <div>
            <Text style={{ display: 'block', color: 'var(--text-dim)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1 }}>এজেন্ট</Text>
            <Title level={4} style={{ color: 'var(--text-main)', margin: 0 }}>1,204</Title>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <Text style={{ display: 'block', color: 'var(--text-dim)', fontSize: 11, textTransform: 'uppercase' }}>সিকিউরিটি লেভেল</Text>
          <Text style={{ color: isAdmin ? 'var(--success)' : 'var(--warning)', fontWeight: 800 }}>{isAdmin ? 'কার্নেল_অ্যাক্সেস_অনুমোদিত' : 'সীমাবদ্ধ_অ্যাক্সেস'}</Text>
        </div>
      </motion.div>
    </div>
  );
}

