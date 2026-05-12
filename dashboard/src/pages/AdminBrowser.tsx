import React from 'react';
import { Layout, Typography, Card, Space, Button, Tag, Timeline } from 'antd';
import { 
  ChromeOutlined, 
  PlayCircleOutlined, 
  PauseCircleOutlined,
  StopOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

const AdminBrowser: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <Title level={2} style={{ marginBottom: 24, fontWeight: 700 }}>
        ব্রাউজার অটোমেশন
      </Title>

      <Card
        style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 12,
          marginBottom: 24
        }}
        bodyStyle={{ padding: 24 }}
      >
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlayCircleOutlined />}>Start Browsing</Button>
          <Button icon={<PauseCircleOutlined />}>Pause</Button>
          <Button icon={<StopOutlined />} danger>Stop All</Button>
        </Space>
        <Text type="secondary">
          Backend: /api/browser/*
        </Text>
      </Card>

      <Card
        style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 12
        }}
        bodyStyle={{ padding: 24 }}
      >
        <Title level={4} style={{ color: '#fff', marginBottom: 16 }}>Recent Activity</Title>
        <Timeline
          items={[
            { children: <Text>Visited: https://example.com</Text>, color: 'green' },
            { children: <Text>Form filled: Login page</Text> },
            { children: <Text>Data scraped from 3 pages</Text>, color: 'blue' },
          ]}
        />
      </Card>
    </div>
  );
};

export default AdminBrowser;
