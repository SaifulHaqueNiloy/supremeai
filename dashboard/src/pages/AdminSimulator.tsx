import React, { useState, useEffect } from 'react';
import { Typography, Card, Space, Table, Button, Tag, message, Statistic, Row, Col, InputNumber, Popconfirm } from 'antd';
import { MobileOutlined, ReloadOutlined, DatabaseOutlined, RocketOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';

const { Title, Text } = Typography;

interface DeploymentRecord {
  appId: string;
  deviceType: string;
  previewUrl: string;
  status: string;
  deployedAt: string;
}

const AdminSimulator: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [deployments, setDeployments] = useState<DeploymentRecord[]>([]);
  const [stats, setStats] = useState({
    totalDeployments: 0
  });

  const fetchUsage = async () => {
    setLoading(true);
    try {
      const response = await fetchWithAuth('/api/simulator/admin/usage');
      if (response.ok) {
        const data = await response.json();
        setDeployments(data.deployments || []);
        setStats({
          totalDeployments: data.totalDeployments || 0
        });
      } else {
        message.error('সিমুলেটর ব্যবহার ডাটা লোড করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      console.error('Error fetching simulator usage:', error);
      message.error('সার্ভারের সাথে যোগাযোগ বিচ্ছিন্ন');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsage();
  }, []);

  const handleSetQuota = async (userId: string, quota: number) => {
    try {
      const response = await fetchWithAuth(`/api/simulator/admin/set-quota/${userId}?quota=${quota}`, {
        method: 'POST'
      });
      if (response.ok) {
        message.success('কোটা সফলভাবে আপডেট করা হয়েছে');
        fetchUsage();
      } else {
        message.error('কোটা আপডেট করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    }
  };

  const columns = [
    { 
      title: 'অ্যাপ আইডি', 
      dataIndex: 'appId', 
      key: 'appId',
      render: (id: string) => <Text code>{id}</Text>
    },
    { 
      title: 'ডিভাইস টাইপ', 
      dataIndex: 'deviceType', 
      key: 'deviceType',
      render: (type: string) => <Tag color="blue">{type}</Tag>
    },
    { 
      title: 'স্ট্যাটাস', 
      dataIndex: 'status', 
      key: 'status', 
      render: (status: string) => (
        <Tag color={status === 'RUNNING' ? 'green' : status === 'FAILED' ? 'red' : 'orange'}>
          {status}
        </Tag>
      )
    },
    { 
      title: 'ডিপ্লয়মেন্ট সময়', 
      dataIndex: 'deployedAt', 
      key: 'deployedAt',
      render: (date: string) => new Date(date).toLocaleString()
    },
    { 
      title: 'অ্যাকশন', 
      key: 'actions', 
      render: (_: any, record: DeploymentRecord) => (
        <Space>
          <Button 
            size="small" 
            type="link" 
            href={record.previewUrl} 
            target="_blank"
            disabled={!record.previewUrl}
          >
            প্রিভিউ
          </Button>
        </Space>
      )
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={2} style={{ marginBottom: 24, fontWeight: 700 }}>
        সিমুলেটর ম্যানেজমেন্ট
      </Title>

      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card bordered={false} className="glass-card">
            <Statistic
              title="মোট ডিপ্লয়মেন্ট"
              value={stats.totalDeployments}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#60a5fa' }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card bordered={false} className="glass-card">
            <Statistic
              title="অ্যাক্টিভ সেশন"
              value={deployments.filter(d => d.status === 'RUNNING').length}
              prefix={<MobileOutlined />}
              valueStyle={{ color: '#10b981' }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        className="glass-card"
        style={{ borderRadius: 12 }}
        bodyStyle={{ padding: 24 }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Text type="secondary">
            গ্লোবাল সিমুলেটর ইউজেস এবং ডিপ্লয়মেন্ট স্ট্যাটাস
          </Text>
          <Button icon={<ReloadOutlined />} onClick={fetchUsage} loading={loading}>রিফ্রেশ</Button>
        </div>
        
        <Table 
          columns={columns} 
          dataSource={deployments} 
          rowKey="appId"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="middle"
        />
      </Card>

      <Card
        className="glass-card"
        style={{ borderRadius: 12, marginTop: 24 }}
        title={<><DatabaseOutlined /> কোটা অ্যাডমিনিস্ট্রেশন</>}
      >
        <Text type="secondary">
          সিমুলেটর কোটা ম্যানেজ করতে ইউজার আইডি ব্যবহার করুন:
        </Text>
        <div style={{ marginTop: 16 }}>
          <Space>
            <InputNumber 
              placeholder="Quota (1-20)" 
              min={1} 
              max={20} 
              id="quotaInput"
              style={{ width: 150 }}
            />
            <Button 
              type="primary"
              onClick={() => {
                const userId = window.prompt('User ID দিন:');
                const quota = (document.getElementById('quotaInput') as HTMLInputElement)?.value;
                if (userId && quota) handleSetQuota(userId, parseInt(quota));
              }}
            >
              কোটা সেট করুন
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default AdminSimulator;
