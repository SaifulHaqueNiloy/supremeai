// ModernAdminDashboard.tsx - Redesigned Clean Interface
import { useState } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, theme, ConfigProvider } from 'antd';
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
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import ChatWithAI from '../components/ChatWithAI';
import KnowledgeHub from '../components/KnowledgeHub';
import APIManagement from '../components/APIManagement';
import AdminProjects from './AdminProjects';

const { Header, Content, Sider } = Layout;

export default function ModernAdminDashboard() {
  const { t } = useTranslation();
  const [collapsed, setCollapsed] = useState(false);
  const [activeKey, setActiveKey] = useState('dashboard');
  const { token } = theme.useToken();

  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: t('nav.dashboard') },
    { key: 'ai', icon: <RobotOutlined />, label: t('nav.ai') },
    { key: 'projects', icon: <CodeOutlined />, label: t('nav.projects') },
    { key: 'analytics', icon: <BarChartOutlined />, label: t('nav.analytics') },
    { key: 'knowledge', icon: <BulbOutlined />, label: t('nav.knowledge') },
    { key: 'settings', icon: <SettingOutlined />, label: t('nav.settings') },
  ];

  const renderContent = () => {
    switch (activeKey) {
      case 'dashboard':
        return <DashboardHome />;
      case 'ai':
        return <ChatWithAI />;
      case 'projects':
        return <AdminProjects />;
      case 'analytics':
        return <KnowledgeHub />;
      case 'knowledge':
        return <APIManagement />;
      default:
        return <DashboardHome />;
    }
  };

  return (
    <ConfigProvider
      theme={{
        algorithm: token.colorBgBase === '#141414' ? theme.darkAlgorithm : theme.defaultAlgorithm,
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
          <div style={{ height: 32, margin: 16, background: 'rgba(255,255,255,0.2)' }} />
          <Menu
            mode="inline"
            selectedKeys={[activeKey]}
            onClick={(e) => setActiveKey(e.key)}
            items={menuItems}
            theme="dark"
          />
        </Sider>
        <Layout>
          <Header style={{ padding: 0, background: token.colorBgContainer }}>
            <div style={{ float: 'right', marginRight: 24 }}>
              <Avatar icon={<LogoutOutlined />} onClick={() => {}} />
            </div>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
            />
          </Header>
          <Content style={{ margin: '16px' }}>{renderContent()}</Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

function DashboardHome() {
  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>SupremeAI Dashboard</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
        <div style={{ padding: 24, background: '#fff', borderRadius: 8 }}>
          <h3>AI Assistant</h3>
          <p>Chat with AI to generate projects</p>
        </div>
        <div style={{ padding: 24, background: '#fff', borderRadius: 8 }}>
          <h3>Projects</h3>
          <p>View and manage your projects</p>
        </div>
      </div>
    </div>
  );
}