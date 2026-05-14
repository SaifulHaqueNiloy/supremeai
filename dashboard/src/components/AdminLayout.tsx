// AdminLayout.tsx - Minimal layout wrapper for admin pages
// Provides consistent page styling and DOES NOT include navigation/header
// Navigation is handled by parent ModernAdminDashboard component

import React from 'react';
import { Layout, Typography } from 'antd';
import type { ReactNode } from 'react';

const { Content } = Layout;
const { Title } = Typography;

interface AdminLayoutProps {
  title: string;
  children: ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ title, children }) => {
  return (
    <Content style={{ padding: '24px', background: '#080808' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="flex flex-col">
          <h1 style={{ fontSize: '20px', fontWeight: 900, color: '#fff', margin: 0, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            {title}
          </h1>
          <div className="h-1 w-12 bg-emerald-500 mt-1" />
        </div>
      </div>
      {children}
    </Content>
  );
};

export default AdminLayout;
