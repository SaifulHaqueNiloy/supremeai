import React, { useState, useEffect } from 'react';
import { 
  Layout, 
  Typography, 
  Card, 
  Space, 
  Tag, 
  Progress, 
  Tabs, 
  Button, 
  List, 
  Badge, 
  message, 
  Spin, 
  Switch, 
  Tooltip,
  Statistic,
  Row,
  Col,
  Empty,
  Popconfirm
} from 'antd';
import { 
  BulbOutlined, 
  PlayCircleOutlined, 
  PauseCircleOutlined,
  ThunderboltOutlined,
  TrophyOutlined,
  BookOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  GlobalOutlined,
  RocketOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';
import AdminLayout from '../components/AdminLayout';
import { authUtils } from '../lib/authUtils';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface LearningStatus {
  mode: string;
  modeDescription: string;
  emergencyPaused: boolean;
  scrapingAllowed: boolean;
  autoApprovalAllowed: boolean;
  learningAllowed: boolean;
  quota: {
    totalUsage: number;
    dailyLimit: number;
    remaining: number;
    percentageUsed: number;
  };
}

interface KnowledgeDomain {
  id: string;
  name: string;
  status: string;
  keywords: string[];
  lastUpdateAt: string;
  knowledgeCount: number;
}

interface Recommendation {
  id: string;
  title: string;
  description: string;
  source: string;
  confidence: number;
  suggestedKeywords: string[];
  createdAt: string;
}

const AdminLearning: React.FC = () => {
  const [status, setStatus] = useState<LearningStatus | null>(null);
  const [domains, setDomains] = useState<KnowledgeDomain[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Learning Status
      const statusResp = await authUtils.fetchWithAuth('/api/admin/learning/status');
      if (statusResp.ok) {
        const statusData = await statusResp.json();
        setStatus(statusData);
      }

      // 2. Fetch Knowledge Domains
      const domainsResp = await authUtils.fetchWithAuth('/api/admin/knowledge/domains');
      if (domainsResp.ok) {
        const domainsData = await domainsResp.json();
        setDomains(domainsData.data || []);
      }

      // 3. Fetch Recommendations
      const recsResp = await authUtils.fetchWithAuth('/api/admin/knowledge/recommendations');
      if (recsResp.ok) {
        const recsData = await recsResp.json();
        setRecommendations(recsData.data || []);
      }
    } catch (error) {
      console.error('Error fetching learning data:', error);
      message.error('লার্নিং ডাটা লোড করতে সমস্যা হয়েছে');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleModeChange = async (mode: string) => {
    setActionLoading(true);
    try {
      const resp = await authUtils.fetchWithAuth('/api/admin/learning/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      if (resp.ok) {
        message.success(`লার্নিং মোড পরিবর্তন হয়েছে: ${mode}`);
        fetchData();
      } else {
        message.error('মোড পরিবর্তন ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('একটি ত্রুটি ঘটেছে');
    } finally {
      setActionLoading(false);
    }
  };

  const handleManualTrigger = async () => {
    setActionLoading(true);
    try {
      const resp = await authUtils.fetchWithAuth('/api/admin/learning/trigger', {
        method: 'POST'
      });
      if (resp.ok) {
        message.success('লার্নিং সাইকেল শুরু হয়েছে');
      } else {
        const err = await resp.json();
        message.error(err.error || 'ট্রিগার ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার এরর');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEmergencyPause = async () => {
    setActionLoading(true);
    try {
      const endpoint = status?.emergencyPaused ? '/api/admin/learning/resume' : '/api/admin/learning/emergency-pause';
      const resp = await authUtils.fetchWithAuth(endpoint, { method: 'POST' });
      if (resp.ok) {
        message.success(status?.emergencyPaused ? 'সিস্টেম রেজুম হয়েছে' : 'সিস্টেম পজ করা হয়েছে');
        fetchData();
      }
    } catch (error) {
      message.error('অপারেশন ব্যর্থ হয়েছে');
    } finally {
      setActionLoading(false);
    }
  };

  const renderStatusTab = () => (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Row gutter={16}>
        <Col span={8}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title="Current Mode" 
              value={status?.mode || 'UNKNOWN'} 
              valueStyle={{ color: 'var(--neon-blue)', fontWeight: 700 }}
              prefix={<ThunderboltOutlined />}
            />
            <Text type="secondary">{status?.modeDescription}</Text>
          </Card>
        </Col>
        <Col span={8}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title="Daily Quota Usage" 
              value={status?.quota.totalUsage || 0} 
              suffix={`/ ${status?.quota.dailyLimit || 0}`}
              valueStyle={{ color: '#10b981' }}
            />
            <Progress 
              percent={status?.quota.percentageUsed} 
              size="small" 
              strokeColor={{ '0%': '#10b981', '100%': '#3b82f6' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card bordered={false} className="glass-card">
            <Statistic 
              title="Status" 
              value={status?.emergencyPaused ? 'Paused' : 'Active'} 
              valueStyle={{ color: status?.emergencyPaused ? '#ef4444' : '#10b981' }}
              prefix={status?.emergencyPaused ? <PauseCircleOutlined /> : <CheckCircleOutlined />}
            />
            <Button 
              danger={!status?.emergencyPaused}
              type={status?.emergencyPaused ? 'primary' : 'default'}
              size="small"
              style={{ marginTop: 8 }}
              onClick={handleEmergencyPause}
              loading={actionLoading}
            >
              {status?.emergencyPaused ? 'Resume Learning' : 'Emergency Pause'}
            </Button>
          </Card>
        </Col>
      </Row>

      <Card title="Learning Mode Control" className="glass-card">
        <Space size="middle" wrap>
          <Button 
            type={status?.mode === 'AGGRESSIVE' ? 'primary' : 'default'} 
            onClick={() => handleModeChange('AGGRESSIVE')}
            loading={actionLoading}
          >
            Aggressive
          </Button>
          <Button 
            type={status?.mode === 'BALANCED' ? 'primary' : 'default'} 
            onClick={() => handleModeChange('BALANCED')}
            loading={actionLoading}
          >
            Balanced
          </Button>
          <Button 
            type={status?.mode === 'MANUAL' ? 'primary' : 'default'} 
            onClick={() => handleModeChange('MANUAL')}
            loading={actionLoading}
          >
            Manual
          </Button>
          <Button 
            type={status?.mode === 'PAUSED' ? 'primary' : 'default'} 
            onClick={() => handleModeChange('PAUSED')}
            loading={actionLoading}
            danger
          >
            Paused
          </Button>
          <div style={{ marginLeft: 24, borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: 24 }}>
            <Button 
              icon={<RocketOutlined />} 
              onClick={handleManualTrigger}
              disabled={status?.mode !== 'MANUAL' && status?.mode !== 'BALANCED'}
              loading={actionLoading}
            >
              Trigger Learning Cycle
            </Button>
          </div>
        </Space>
      </Card>

      <Card title="System Capabilities" className="glass-card">
        <Row gutter={[24, 24]}>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text><GlobalOutlined style={{ marginRight: 8 }} /> Web Scraping Allowed</Text>
                <Badge status={status?.scrapingAllowed ? 'processing' : 'default'} text={status?.scrapingAllowed ? 'ON' : 'OFF'} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text><SafetyCertificateOutlined style={{ marginRight: 8 }} /> Auto-Approval (Autonomous Mode)</Text>
                <Badge status={status?.autoApprovalAllowed ? 'warning' : 'default'} text={status?.autoApprovalAllowed ? 'ACTIVE' : 'DISABLED'} />
              </div>
            </Space>
          </Col>
        </Row>
      </Card>
    </Space>
  );

  const renderKnowledgeTab = () => (
    <Card bordered={false} className="glass-card">
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Title level={4} style={{ margin: 0, color: '#fff' }}>Knowledge Domains</Title>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>Refresh</Button>
      </div>
      <List
        dataSource={domains}
        renderItem={domain => (
          <List.Item
            actions={[
              <Button type="link" onClick={() => message.info('অপেক্ষমাণ')}>View Knowledge</Button>,
              <Button type="link" icon={<PlayCircleOutlined />}>Process Job</Button>
            ]}
          >
            <List.Item.Meta
              avatar={<BookOutlined style={{ fontSize: 24, color: 'var(--neon-blue)' }} />}
              title={<span style={{ color: '#fff', fontWeight: 600 }}>{domain.name}</span>}
              description={
                <Space wrap>
                  {domain.keywords.map(k => <Tag key={k}>{k}</Tag>)}
                </Space>
              }
            />
            <div style={{ textAlign: 'right', marginRight: 24 }}>
              <Tag color={domain.status === 'LEARNING' ? 'processing' : 'success'}>
                {domain.status}
              </Tag>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>Nodes: {domain.knowledgeCount}</Text>
            </div>
          </List.Item>
        )}
        locale={{ emptyText: <Empty description="কোনো ডোমেইন পাওয়া যায়নি" /> }}
      />
    </Card>
  );

  const renderRecommendationsTab = () => (
    <Card bordered={false} className="glass-card">
       <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, color: '#fff' }}>Improvement Proposals</Title>
        <Text type="secondary">সিস্টেম লার্নিং থেকে আসা নতুন রিকমেন্ডেশনসমূহ</Text>
      </div>
      <List
        dataSource={recommendations}
        renderItem={rec => (
          <Card 
            size="small" 
            style={{ marginBottom: 12, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <Text strong style={{ color: '#fff', fontSize: 16 }}>{rec.title}</Text>
                <Tag color="blue" style={{ marginLeft: 8 }}>{Math.round(rec.confidence * 100)}% Confidence</Tag>
                <div style={{ marginTop: 8 }}>
                  <Paragraph style={{ color: 'rgba(255,255,255,0.6)' }}>{rec.description}</Paragraph>
                </div>
                <Space wrap>
                  {rec.suggestedKeywords.map(k => <Tag key={k} size="small">{k}</Tag>)}
                </Space>
              </div>
              <Space direction="vertical" align="end">
                <Text type="secondary">{new Date(rec.createdAt).toLocaleDateString()}</Text>
                <Space>
                   <Popconfirm title="এই রিকমেন্ডেশনটি অ্যাপ্রুভ করবেন?">
                    <Button type="primary" size="small" icon={<CheckCircleOutlined />}>Approve</Button>
                   </Popconfirm>
                   <Button size="small" icon={<CloseCircleOutlined />} danger>Decline</Button>
                </Space>
              </Space>
            </div>
          </Card>
        )}
        locale={{ emptyText: <Empty description="কোনো নতুন রিকমেন্ডেশন নেই" /> }}
      />
    </Card>
  );

  return (
    <AdminLayout title="লার্নিং ম্যানেজমেন্ট">
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ fontWeight: 700, margin: 0 }}>লার্নিং ড্যাশবোর্ড</Title>
        <Text type="secondary">AI মডেল লার্নিং, নলেজ বেস এবং সিস্টেম ইমপ্রুভমেন্ট কন্ট্রোল</Text>
      </div>

      <Tabs defaultActiveKey="status" className="modern-tabs">
        <TabPane 
          tab={<span><ThunderboltOutlined /> Status & Control</span>} 
          key="status"
        >
          {loading ? <div style={{ padding: 40, textAlign: 'center' }}><Spin size="large" /></div> : renderStatusTab()}
        </TabPane>
        <TabPane 
          tab={<span><BookOutlined /> Knowledge Base</span>} 
          key="knowledge"
        >
          {loading ? <div style={{ padding: 40, textAlign: 'center' }}><Spin size="large" /></div> : renderKnowledgeTab()}
        </TabPane>
        <TabPane 
          tab={<span><TrophyOutlined /> Recommendations</span>} 
          key="recommendations"
        >
          {loading ? <div style={{ padding: 40, textAlign: 'center' }}><Spin size="large" /></div> : renderRecommendationsTab()}
        </TabPane>
      </Tabs>
    </AdminLayout>
  );
};

export default AdminLearning;
