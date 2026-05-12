// ModernAdminDashboard.tsx - Clean Interface with Access Control
import React, { useState } from 'react';
import { Layout, Menu, Button, Avatar, theme, Badge, Typography, Alert, Card, Space } from 'antd';
import {
  DashboardOutlined,
  RobotOutlined,
  CodeOutlined,
  BarChartOutlined,
  SettingOutlined,
  BulbOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MoonOutlined,
  SunOutlined,
  ExperimentOutlined,
  EyeOutlined,
  LockOutlined,
} from '@ant-design/icons';
import { useRole } from '../contexts/RoleContext';
import { authUtils } from '../lib/authUtils';
import ChatWithAI from '../components/ChatWithAI';
import KnowledgeHub from '../components/KnowledgeHub';
import APIManagement from '../components/APIManagement';
import AdminProjects from './AdminProjects';

const { Header, Content, Sider } = Layout;
const { Text } = Typography;

// Demo placeholder for restricted features
const RestrictedDemo: React.FC<{title: string; description: string; icon: React.ReactNode}> = ({ title, description, icon }) => (
  <div style={{
    padding: '60px 40px',
    textAlign: 'center',
    background: 'rgba(255,255,255,0.02)',
    border: '1px dashed rgba(255,255,255,0.2)',
    borderRadius: '16px',
    marginTop: '20px'
  }}>
    <LockOutlined style={{ fontSize: 64, color: '#f59e0b', marginBottom: 24, opacity: 0.8 }} />
    <h3 style={{ color: '#f59e0b', marginBottom: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
      ADMIN-ONLY MODULE
    </h3>
    <p style={{ color: 'rgba(255,255,255,0.6)', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.7 }}>
      <Text strong style={{ color: '#ef4444' }}>{title}</Text> requires administrator privileges.
      <br />Please sign in with an admin account to access this functionality.
    </p>
    <Space size="middle">
      <Button
        type="primary"
        icon={<EyeOutlined />}
        onClick={() => window.location.href = '/admin?login=true'}
        style={{ background: '#10b981', borderColor: '#10b981' }}
      >
        Login as Admin
      </Button>
      <Button
        onClick={() => window.location.href = '/'}
      >
        Back to Home
      </Button>
    </Space>
  </div>
);

export default function ModernAdminDashboard() {
  const { isAdmin, isAuthenticated } = useRole();
  const [collapsed, setCollapsed] = useState(false);
  const [activeKey, setActiveKey] = useState('dashboard');
  const [darkMode, setDarkMode] = useState(true);

  // All tabs available
  const allMenuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: 'ai', icon: <RobotOutlined />, label: 'AI Chat' },
    { key: 'projects', icon: <CodeOutlined />, label: 'Projects' },
    { key: 'analytics', icon: <BarChartOutlined />, label: 'Analytics', adminOnly: true },
    { key: 'knowledge', icon: <BulbOutlined />, label: 'Knowledge', adminOnly: true },
    { key: 'settings', icon: <SettingOutlined />, label: 'Settings', adminOnly: true },
  ];

  // Filter menu items based on admin status
  const menuItems = allMenuItems.filter(item => !item.adminOnly || isAdmin);

  const renderContent = () => {
    switch (activeKey) {
      case 'dashboard':
        return <DashboardHome />;
      case 'ai':
        return <ChatWithAI />;
      case 'projects':
        return <AdminProjects />;
      case 'analytics':
        return isAdmin ? <APIManagement /> : <RestrictedDemo title="Provider Management" description="AI provider registry and capability assignment requires admin access." icon={<ExperimentOutlined />} />;
      case 'knowledge':
        return isAdmin ? <KnowledgeHub /> : <RestrictedDemo title="Knowledge Hub" description="Access to knowledge base, rule engine, and plan management is restricted to administrators." icon={<ExperimentOutlined />} />;
      case 'settings':
        return isAdmin ? (
          <div style={{ padding: 24, background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
            <h2>System Settings</h2>
            <p>System configuration, user management, and security settings.</p>
          </div>
        ) : <RestrictedDemo title="System Settings" description="System configuration is only available to administrators." icon={<SettingOutlined />} />;
      default:
        return <DashboardHome />;
    }
  };

  function DashboardHome() {
    return (
      <div style={{ padding: 24 }}>
        <h1 style={{ fontSize: 28, marginBottom: 24, fontWeight: 800, letterSpacing: '-0.5px' }}>
          SupremeAI Command Center
        </h1>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 24
        }}>
          <div style={{
            padding: 24,
            background: 'rgba(255,255,255,0.03)',
            borderRadius: 12,
            border: '1px solid rgba(255,255,255,0.1)',
            transition: 'all 0.3s ease'
          }}>
            <h3 style={{ marginBottom: 12, color: 'var(--neon-blue)', fontWeight: 700 }}>AI Assistant</h3>
            <p style={{ color: 'rgba(255,255,255,0.6)', lineHeight: 1.6 }}>
              Chat with SupremeAI agents. Generate code, analyze requirements, and get intelligent assistance.
            </p>
            <Button
              type="primary"
              icon={<RobotOutlined />}
              style={{ marginTop: 16 }}
              onClick={() => setActiveKey('ai')}
            >
              Start Chatting
            </Button>
          </div>
          <div style={{
            padding: 24,
            background: 'rgba(255,255,255,0.03)',
            borderRadius: 12,
            border: '1px solid rgba(255,255,255,0.1)',
            transition: 'all 0.3s ease'
          }}>
            <h3 style={{ marginBottom: 12, color: 'var(--neon-purple)', fontWeight: 700 }}>Projects</h3>
            <p style={{ color: 'rgba(255,255,255,0.6)', lineHeight: 1.6 }}>
              View and manage your generated applications. Track progress, deploy, and monitor performance.
            </p>
            <Button
              style={{ marginTop: 16 }}
              icon={<CodeOutlined />}
              onClick={() => setActiveKey('projects')}
            >
              Browse Projects
            </Button>
          </div>
          {isAdmin && (
            <div style={{
              padding: 24,
              background: 'rgba(16,185,129,0.1)',
              borderRadius: 12,
              border: '1px solid rgba(16,185,129,0.3)',
              transition: 'all 0.3s ease'
            }}>
              <h3 style={{ marginBottom: 12, color: '#10b981', fontWeight: 700 }}>Admin Panel</h3>
              <p style={{ color: 'rgba(255,255,255,0.6)', lineHeight: 1.6 }}>
                Full access to provider management, system monitoring, configuration, and advanced analytics.
              </p>
              <Button
                style={{ marginTop: 16 }}
                icon={<BarChartOutlined />}
                onClick={() => setActiveKey('analytics')}
              >
                View Analytics
              </Button>
            </div>
          )}
          {!isAdmin && (
            <div style={{
              padding: 24,
              background: 'rgba(245,158,11,0.1)',
              borderRadius: 12,
              border: '1px solid rgba(245,158,11,0.3)',
              transition: 'all 0.3s ease'
            }}>
              <h3 style={{ marginBottom: 12, color: '#f59e0b', fontWeight: 700 }}>Upgrade to Admin</h3>
              <p style={{ color: 'rgba(255,255,255,0.6)', lineHeight: 1.6 }}>
                Admin users get access to AI provider management, system metrics, and advanced configuration.
              </p>
              <Button
                type="primary"
                danger
                icon={<ExperimentOutlined />}
                style={{ marginTop: 16 }}
                onClick={() => window.location.href = '/admin?login=true'}
              >
                Request Admin Access
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: darkMode ? '#0a0a0a' : '#f5f5f5' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme={darkMode ? 'dark' : 'light'}>
        <div style={{
          height: 32,
          margin: 16,
          background: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: darkMode ? '#10b981' : '#10b981',
          fontWeight: 700,
          fontSize: 12,
          letterSpacing: '0.1em'
        }}>
          {collapsed ? 'SA' : 'SUPREME AI'}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[activeKey]}
          onClick={(e) => setActiveKey(e.key)}
          items={menuItems}
          theme={darkMode ? 'dark' : 'light'}
        />
      </Sider>
      <Layout>
        <Header style={{
          padding: '0 24px',
          background: darkMode ? '#111' : '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: darkMode ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0,0,0,0.1)'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ color: darkMode ? '#fff' : '#000' }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Button
              type="text"
              icon={darkMode ? <SunOutlined /> : <MoonOutlined />}
              onClick={() => setDarkMode(!darkMode)}
              style={{ color: darkMode ? '#fff' : '#000' }}
            />
            <Avatar
              icon={<LogoutOutlined />}
              style={{
                backgroundColor: isAdmin ? '#10b981' : '#6b7280',
                cursor: 'pointer'
              }}
              onClick={() => {
                authUtils.clearAuth();
                window.location.href = '/';
              }}
            />
            {isAdmin && (
              <Badge color="#10b981" text={<Text style={{color: '#10b981', fontSize: 11, fontWeight: 700}}>ADMIN</Text>} />
            )}
            {!isAdmin && isAuthenticated && (
              <Badge color="#ff9800" text={<Text style={{color: '#ff9800', fontSize: 11, fontWeight: 700}}>USER</Text>} />
            )}
            {!isAuthenticated && (
              <Badge color="#6b7280" text={<Text style={{color: '#6b7280', fontSize: 11, fontWeight: 700}}>GUEST</Text>} />
            )}
          </div>
        </Header>
        <Content style={{ margin: '24px', overflow: 'auto' }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
}
