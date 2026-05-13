import React, { useState, useEffect } from 'react';
import { 
  Typography, Card, Space, Table, Progress, Statistic, Row, Col, 
  Button, message, Popconfirm, Tag, Select, Badge, Alert, Tooltip 
} from 'antd';
import { 
  PieChartOutlined, UserOutlined, ApartmentOutlined, 
  ReloadOutlined, WarningOutlined, StopOutlined, CheckCircleOutlined 
} from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';

const { Title, Text } = Typography;
const { Option } = Select;

interface UserQuota {
  uid: string;
  email: string;
  displayName: string;
  tier: string;
  isActive: boolean;
  currentUsage: number;
  monthlyQuota: number;
  createdAt: string;
}

const AdminQuotas: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<UserQuota[]>([]);
  const [warnings, setWarnings] = useState<any[]>([]);
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeQuotas: 0,
    overLimit: 0
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [accountsRes, warningsRes] = await Promise.all([
        fetchWithAuth('/api/accounts'),
        fetchWithAuth('/api/quota/warnings')
      ]);

      if (accountsRes.ok) {
        const data = await accountsRes.json();
        setUsers(data);
        
        // Calculate stats
        const total = data.length;
        const active = data.filter((u: any) => u.currentUsage > 0).length;
        const over = data.filter((u: any) => u.currentUsage >= u.monthlyQuota).length;
        
        setStats({
          totalUsers: total,
          activeQuotas: active,
          overLimit: over
        });
      }

      if (warningsRes.ok) {
        const warningData = await warningsRes.json();
        setWarnings(warningData.warnings || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      message.error('সার্ভারের সাথে যোগাযোগ বিচ্ছিন্ন');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleReset = async (userId: string) => {
    try {
      const response = await fetchWithAuth(`/api/quota/${userId}/reset`, {
        method: 'POST'
      });
      if (response.ok) {
        message.success('কোটা সফলভাবে রিসেট করা হয়েছে');
        fetchData();
      } else {
        message.error('কোটা রিসেট করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    }
  };

  const handleTierUpdate = async (userId: string, newTier: string) => {
    try {
      const response = await fetchWithAuth(`/api/accounts/${userId}/tier`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: newTier })
      });
      if (response.ok) {
        message.success(`ইউজার টিয়ার ${newTier} এ আপডেট করা হয়েছে`);
        fetchData();
      } else {
        message.error('টিয়ার আপডেট করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    }
  };

  const handleDeactivate = async (userId: string) => {
    try {
      const response = await fetchWithAuth(`/api/accounts/${userId}/deactivate`, {
        method: 'PUT'
      });
      if (response.ok) {
        message.warning('ইউজার অ্যাকাউন্ট ডিঅ্যাক্টিভ করা হয়েছে');
        fetchData();
      } else {
        message.error('অ্যাকাউন্ট ডিঅ্যাক্টিভ করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    }
  };

  const columns = [
    { 
      title: 'ইউজার', 
      dataIndex: 'email', 
      key: 'email',
      render: (email: string, record: UserQuota) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.displayName || 'No Name'}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>{email}</Text>
        </Space>
      )
    },
    { 
      title: 'টিয়ার ম্যানেজমেন্ট', 
      dataIndex: 'tier', 
      key: 'tier',
      width: 150,
      render: (tier: string, record: UserQuota) => (
        <Select 
          defaultValue={tier} 
          style={{ width: '100%' }}
          onChange={(value) => handleTierUpdate(record.uid, value)}
          size="small"
          dropdownStyle={{ borderRadius: 8 }}
        >
          <Option value="FREE"><Tag color="default">FREE</Tag></Option>
          <Option value="PRO"><Tag color="blue">PRO</Tag></Option>
          <Option value="ADMIN"><Tag color="gold">ADMIN</Tag></Option>
        </Select>
      )
    },
    { 
      title: 'API কল (ব্যবহার)', 
      dataIndex: 'currentUsage', 
      key: 'currentUsage', 
      render: (usage: number, record: UserQuota) => {
        const percent = Math.min(100, Math.round((usage / record.monthlyQuota) * 100));
        return (
          <div style={{ width: 150 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <Text style={{ fontSize: '12px' }}>{usage.toLocaleString()}</Text>
              <Text style={{ fontSize: '12px' }} type="secondary">/ {record.monthlyQuota.toLocaleString()}</Text>
            </div>
            <Progress 
              percent={percent} 
              size="small" 
              status={usage >= record.monthlyQuota ? 'exception' : 'active'}
              strokeColor={usage >= record.monthlyQuota ? '#ef4444' : usage > record.monthlyQuota * 0.8 ? '#f59e0b' : '#10b981'}
            />
          </div>
        );
      }
    },
    { 
      title: 'স্ট্যাটাস', 
      dataIndex: 'isActive', 
      key: 'isActive',
      render: (active: boolean) => (
        <Badge 
          status={active ? 'success' : 'error'} 
          text={<Text style={{ color: active ? '#10b981' : '#ef4444' }}>{active ? 'Active' : 'Inactive'}</Text>} 
        />
      )
    },
    { 
      title: 'অ্যাকশন', 
      key: 'actions', 
      render: (_: any, record: UserQuota) => (
        <Space>
          <Tooltip title="রিসেট কোটা">
            <Popconfirm
              title="আপনি কি নিশ্চিত যে আপনি এই ইউজারের কোটা রিসেট করতে চান?"
              onConfirm={() => handleReset(record.uid)}
              okText="হ্যাঁ"
              cancelText="না"
            >
              <Button size="small" shape="circle" icon={<ReloadOutlined />} />
            </Popconfirm>
          </Tooltip>
          
          {record.isActive && (
            <Tooltip title="ডিঅ্যাক্টিভ করুন">
              <Popconfirm
                title="অ্যাকাউন্ট ডিঅ্যাক্টিভ করতে চান?"
                onConfirm={() => handleDeactivate(record.uid)}
                okText="হ্যাঁ"
                cancelText="না"
                okButtonProps={{ danger: true }}
              >
                <Button size="small" shape="circle" danger icon={<StopOutlined />} />
              </Popconfirm>
            </Tooltip>
          )}
        </Space>
      )
    },
  ];

  return (
    <div style={{ padding: 24, background: '#0a0a0a', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#fff', fontWeight: 700 }}>
          কোটা ম্যানেজমেন্ট
        </Title>
        <Button 
          type="primary" 
          icon={<ReloadOutlined />} 
          onClick={fetchData} 
          loading={loading}
          style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', border: 'none' }}
        >
          রিফ্রেশ ডাটা
        </Button>
      </div>

      {warnings.length > 0 && (
        <Alert
          message="কোটা সতর্কতা"
          description={`${warnings.length} জন ইউজার তাদের মাসিক কোটা সীমার কাছাকাছি পৌঁছেছেন।`}
          type="warning"
          showIcon
          icon={<WarningOutlined />}
          style={{ marginBottom: 24, borderRadius: 12, background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)' }}
          action={
            <Button size="small" ghost onClick={() => message.info('সতর্কতা তালিকা চেক করুন')}>
              বিস্তারিত
            </Button>
          }
        />
      )}

      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card bordered={false} className="glass-card" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.45)' }}>মোট ইউজার</span>}
              value={stats.totalUsers}
              prefix={<UserOutlined style={{ color: '#3b82f6' }} />}
              valueStyle={{ color: '#fff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false} className="glass-card" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.45)' }}>অ্যাক্টিভ কোটা (ব্যবহারকারী)</span>}
              value={stats.activeQuotas}
              prefix={<PieChartOutlined style={{ color: '#10b981' }} />}
              valueStyle={{ color: '#fff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false} className="glass-card" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.45)' }}>কোটা লিমিট অতিক্রম</span>}
              value={stats.overLimit}
              prefix={<ApartmentOutlined style={{ color: '#ef4444' }} />}
              valueStyle={{ color: '#fff' }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        className="glass-card"
        style={{ 
          borderRadius: 16, 
          background: 'rgba(255,255,255,0.02)', 
          border: '1px solid rgba(255,255,255,0.1)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
        }}
        bodyStyle={{ padding: 0 }}
      >
        <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <Text style={{ color: 'rgba(255,255,255,0.45)' }}>
            ইউজার তালিকা এবং কোটা ব্যবহারের রিয়েল-টাইম স্ট্যাটাস
          </Text>
        </div>
        
        <Table 
          columns={columns} 
          dataSource={users} 
          rowKey="uid"
          loading={loading}
          pagination={{ pageSize: 10, showSizeChanger: true }}
          size="middle"
          className="admin-table-dark"
          style={{ padding: '8px' }}
        />
      </Card>

      <style>{`
        .admin-table-dark .ant-table {
          background: transparent !important;
          color: #fff !important;
        }
        .admin-table-dark .ant-table-thead > tr > th {
          background: rgba(255,255,255,0.03) !important;
          color: rgba(255,255,255,0.65) !important;
          border-bottom: 1px solid rgba(255,255,255,0.05) !important;
        }
        .admin-table-dark .ant-table-tbody > tr > td {
          border-bottom: 1px solid rgba(255,255,255,0.05) !important;
        }
        .admin-table-dark .ant-table-tbody > tr:hover > td {
          background: rgba(255,255,255,0.05) !important;
        }
        .admin-table-dark .ant-pagination-item, .admin-table-dark .ant-pagination-prev, .admin-table-dark .ant-pagination-next {
          background: transparent !important;
          border-color: rgba(255,255,255,0.2) !important;
        }
        .admin-table-dark .ant-pagination-item a {
          color: #fff !important;
        }
        .glass-card {
          transition: transform 0.2s ease;
        }
        .glass-card:hover {
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
};

export default AdminQuotas;
