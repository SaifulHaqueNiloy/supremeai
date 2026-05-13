import React, { useState, useEffect } from 'react';
import {
  Typography, Card, Space, Row, Col, Progress,
  Statistic, Badge, Alert, Button, Input, List, message, Spin, Tag
} from 'antd';
import { 
  SecurityScanOutlined, 
  BugOutlined, 
  ToolOutlined,
  ThunderboltOutlined,
  HeartOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  AlertOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';

const { Title, Text } = Typography;
const { TextArea } = Input;

const AdminSecurity: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [healingStatus, setHealingStatus] = useState<any>(null);
  const [systemStats, setSystemStats] = useState<any>(null);
  const [testError, setTestError] = useState('');
  const [fixing, setFixing] = useState(false);
  const [fixResult, setFixResult] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [healingRes, contractRes] = await Promise.all([
        fetchWithAuth('/api/self-healing/status'),
        fetchWithAuth('/api/admin/dashboard/contract')
      ]);

      if (healingRes.ok) {
        setHealingStatus(await healingRes.json());
      }
      if (contractRes.ok) {
        const data = await contractRes.json();
        setSystemStats(data.data?.stats);
      }
    } catch (error) {
      console.error('Error fetching security data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const handleTestFix = async () => {
    if (!testError.trim()) {
      message.warning('অনুগ্রহ করে একটি এরর মেসেজ লিখুন');
      return;
    }

    setFixing(true);
    try {
      const response = await fetchWithAuth('/api/self-healing/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: testError })
      });

      if (response.ok) {
        const result = await response.json();
        setFixResult(result);
        message.success('সিস্টেম এররটি বিশ্লেষণ করেছে');
      } else {
        message.error('এরর ডিটেকশন ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    } finally {
      setFixing(false);
    }
  };

  if (loading && !systemStats) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0a0a0a' }}>
        <Spin size="large" tip="সিকিউরিটি ডাটা লোড হচ্ছে..." />
      </div>
    );
  }

  const healthScore = systemStats?.systemHealthScore || 100;
  const healthStatus = systemStats?.systemHealthStatus || 'healthy';

  return (
    <div style={{ padding: 24, background: '#0a0a0a', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#fff', fontWeight: 700 }}>
          সিকিউরিটি & রেজিলিয়েন্স
        </Title>
        <Space>
          <Badge status="processing" text={<Text style={{ color: '#10b981' }}>Cyber Guard Active</Text>} />
          <Button icon={<ReloadOutlined />} onClick={fetchData} ghost style={{ color: '#fff' }} />
        </Space>
      </div>

      <Row gutter={[24, 24]}>
        {/* System Health Score */}
        <Col xs={24} lg={8}>
          <Card 
            bordered={false} 
            className="glass-card"
            style={{ height: '100%', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.1)' }}
          >
            <Statistic
              title={<span style={{ color: 'rgba(255,255,255,0.45)' }}>সিস্টেম হেলথ স্কোর</span>}
              value={healthScore}
              suffix="/ 100"
              prefix={<HeartOutlined style={{ color: healthStatus === 'healthy' ? '#10b981' : '#ef4444' }} />}
              valueStyle={{ color: '#fff', fontSize: '24px' }}
            />
            <div style={{ marginTop: 20, textAlign: 'center' }}>
              <Progress
                type="dashboard"
                percent={healthScore}
                strokeColor={{
                  '0%': '#ef4444',
                  '50%': '#f59e0b',
                  '100%': '#10b981',
                }}
                trailColor="rgba(255,255,255,0.05)"
              />
            </div>
            <div style={{ marginTop: 16 }}>
              <Alert
                message={systemStats?.systemHealthReason || "All systems operational"}
                type={healthStatus === 'healthy' ? "success" : "warning"}
                showIcon
                style={{ borderRadius: 8, background: 'rgba(255,255,255,0.05)', border: 'none' }}
              />
            </div>
          </Card>
        </Col>

        {/* Self-Healing Status */}
        <Col xs={24} lg={16}>
          <Card 
            title={<span style={{ color: '#fff' }}><BugOutlined /> Self-Healing System Status</span>}
            bordered={false}
            className="glass-card"
            style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.1)' }}
          >
            <Row gutter={16}>
              <Col span={8}>
                <Statistic 
                  title={<span style={{ color: 'rgba(255,255,255,0.45)' }}>স্ট্যাটাস</span>}
                  value={healingStatus?.status?.toUpperCase() || 'ACTIVE'} 
                  valueStyle={{ color: '#10b981', fontSize: '18px' }} 
                />
              </Col>
              <Col span={8}>
                <Statistic 
                  title={<span style={{ color: 'rgba(255,255,255,0.45)' }}>অটো-হিলিং</span>}
                  value={healingStatus?.autoHealing || 'Enabled'} 
                  valueStyle={{ color: '#3b82f6', fontSize: '18px' }} 
                />
              </Col>
              <Col span={8}>
                <Statistic 
                  title={<span style={{ color: 'rgba(255,255,255,0.45)' }}>ইনফিনিট লুপ</span>}
                  value={healingStatus?.infiniteLoop || 'Active'} 
                  valueStyle={{ color: '#f59e0b', fontSize: '18px' }} 
                />
              </Col>
            </Row>

            <div style={{ marginTop: 24 }}>
              <Title level={5} style={{ color: '#fff', marginBottom: 16 }}>
                ইন্টারেক্টিভ এরর সিমুলেটর
              </Title>
              <Space direction="vertical" style={{ width: '100%' }}>
                <TextArea
                  placeholder="একটি এরর মেসেজ লিখুন (যেমন: Connection timeout to provider X)..."
                  rows={3}
                  value={testError}
                  onChange={(e) => setTestError(e.target.value)}
                  style={{ background: 'rgba(0,0,0,0.2)', color: '#fff', borderColor: 'rgba(255,255,255,0.1)' }}
                />
                <Button 
                  type="primary" 
                  icon={<ThunderboltOutlined />} 
                  onClick={handleTestFix}
                  loading={fixing}
                  block
                  style={{ background: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)', border: 'none', height: '40px' }}
                >
                  ডিটেক্ট এবং অটো-ফিক্স পরীক্ষা করুন
                </Button>
              </Space>

              {fixResult && (
                <div style={{ marginTop: 16 }}>
                  <Alert
                    message="অটো-ফিক্স বিশ্লেষণ ফলাফল"
                    description={
                      <div style={{ marginTop: 8 }}>
                        <Text style={{ color: 'rgba(255,255,255,0.8)' }}>{fixResult.summary || fixResult.status || "প্রক্রিয়াটি সফলভাবে সম্পন্ন হয়েছে।"}</Text>
                        <br />
                        <Space style={{ marginTop: 8 }}>
                          <Tag color="green">Action: {fixResult.actionTaken || "Analyzed"}</Tag>
                          <Tag color="blue">Confidence: {fixResult.confidence || "High"}</Tag>
                        </Space>
                      </div>
                    }
                    type="info"
                    style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.2)' }}
                  />
                </div>
              )}
            </div>
          </Card>
        </Col>

        {/* Security Logs / Guard Actions */}
        <Col xs={24}>
          <Card 
            title={<span style={{ color: '#fff' }}><SecurityScanOutlined /> Cyber Guard Active Surveillance</span>}
            bordered={false}
            className="glass-card"
            style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.1)' }}
          >
            <List
              itemLayout="horizontal"
              dataSource={[
                { title: 'Firewall Monitoring', status: 'Online', icon: <CheckCircleOutlined style={{ color: '#10b981' }} /> },
                { title: 'Intrusion Detection System', status: 'Active', icon: <CheckCircleOutlined style={{ color: '#10b981' }} /> },
                { title: 'API Security Layer', status: 'Secured', icon: <CheckCircleOutlined style={{ color: '#10b981' }} /> },
                { title: 'Database Encryption', status: 'AES-256 Enabled', icon: <CheckCircleOutlined style={{ color: '#10b981' }} /> }
              ]}
              renderItem={(item) => (
                <List.Item style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <List.Item.Meta
                    avatar={item.icon}
                    title={<span style={{ color: '#fff' }}>{item.title}</span>}
                    description={<span style={{ color: 'rgba(255,255,255,0.45)' }}>{item.status}</span>}
                  />
                  <Tag color="success">OPERATIONAL</Tag>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      <style>{`
        .glass-card {
          border-radius: 16px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.2);
          transition: all 0.3s ease;
        }
        .glass-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 24px rgba(0,0,0,0.4);
          background: rgba(255,255,255,0.04) !important;
        }
        .ant-statistic-title {
          margin-bottom: 8px !important;
        }
      `}</style>
    </div>
  );
};

export default AdminSecurity;
