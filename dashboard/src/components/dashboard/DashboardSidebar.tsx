import React from 'react';
import { Layout, Menu, Typography } from 'antd';
import { motion } from 'framer-motion';

const { Sider } = Layout;
const { Text } = Typography;

interface DashboardSidebarProps {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  activeKey: string;
  setActiveKey: (key: string) => void;
  menuItems: any[];
  isAdmin: boolean;
  isAuthenticated: boolean;
}

const DashboardSidebar: React.FC<DashboardSidebarProps> = ({
  collapsed,
  setCollapsed,
  activeKey,
  setActiveKey,
  menuItems,
  isAdmin,
  isAuthenticated
}) => {
  return (
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
  );
};

export default DashboardSidebar;
