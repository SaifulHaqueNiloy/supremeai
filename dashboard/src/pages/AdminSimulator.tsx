import React, { useState, useEffect } from 'react';
import { Typography, Card, Space, Table, Button, Tag, message, Statistic, Row, Col, InputNumber, Select, Drawer } from 'antd';
import { MobileOutlined, ReloadOutlined, DatabaseOutlined, RocketOutlined, EyeOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';
import { useRole } from '../contexts/RoleContext';
import SimulatorPreview from '../components/SimulatorPreview';

const { Title, Text } = Typography;
const { Option } = Select;

interface DeploymentRecord {
  appId: string;
  deviceType: string;
  previewUrl: string;
  status: string;
  deployedAt: string;
}

interface Project {
  id: string;
  name: string;
  type: string;
}

const AdminSimulator: React.FC = () => {
  const { isAdmin, isGuest, user } = useRole();
  console.log('[AdminSimulator] User:', user?.email, 'isAdmin:', isAdmin, 'isGuest:', isGuest);
  const [loading, setLoading] = useState(false);
  const [deployments, setDeployments] = useState<DeploymentRecord[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string | undefined>();
  const [previewOpen, setPreviewOpen] = useState(false);
  const [stats, setStats] = useState({
    totalDeployments: 0
  });

  const fetchData = async () => {
    if (isGuest) {
      setLoading(false);
      return;
    }
    
    setLoading(true);
    try {
      // Fetch deployments based on role
      const endpoint = isAdmin ? '/api/simulator/admin/usage' : '/api/simulator/installed';
      const usageRes = await fetchWithAuth(endpoint);
      
      if (usageRes.ok) {
        const data = await usageRes.json();
        // Backend returns slightly different shapes for admin vs user
        if (isAdmin) {
          setDeployments(data.deployments || []);
          setStats({
            totalDeployments: data.totalDeployments || 0
          });
        } else {
          // Normal user response from /installed has 'installedApps'
          const apps = data.installedApps || [];
          setDeployments(apps.map((a: any) => ({
            appId: a.appId,
            deviceType: a.deviceType || 'UNKNOWN',
            previewUrl: a.previewUrl,
            status: a.status,
            deployedAt: a.installedAt
          })));
          setStats({
            totalDeployments: apps.length
          });
        }
      }

      // Fetch projects to allow simulation
      const projectsRes = await fetchWithAuth('/api/projects');
      if (projectsRes.ok) {
        const data = await projectsRes.json();
        setProjects(data.projects || []);
      }
    } catch (error) {
      console.error('Error fetching simulator data:', error);
      message.error('সার্ভারের সাথে যোগাযোগ বিচ্ছিন্ন');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [isAdmin, isGuest]);

  const handleSimulate = (appId: string) => {
    setSelectedAppId(appId);
    setPreviewOpen(true);
  };

  const handleSetQuota = async (userId: string, quota: number) => {
    try {
      const response = await fetchWithAuth(`/api/simulator/admin/set-quota/${userId}?quota=${quota}`, {
        method: 'POST'
      });
      if (response.ok) {
        message.success('কোটা সফলভাবে আপডেট করা হয়েছে');
        fetchData();
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
            type="primary" 
            icon={<EyeOutlined />}
            onClick={() => handleSimulate(record.appId)}
          >
            লাইভ প্রিভিউ
          </Button>
          <Button 
            size="small" 
            href={record.previewUrl} 
            target="_blank"
            disabled={!record.previewUrl}
          >
            এক্সটার্নাল
          </Button>
        </Space>
      )
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      {isGuest && (
        <Alert
          message="গেস্ট মোড প্রিভিউ"
          description="সিমুলেটর ম্যানেজমেন্টের অ্যাডভান্সড ফিচারগুলো ব্যবহারের জন্য অনুগ্রহ করে লগইন করুন।"
          type="warning"
          showIcon
          style={{ marginBottom: 24, borderRadius: 8 }}
          action={
            <Button size="small" type="primary" onClick={() => window.location.href = '/login'}>
              লগইন করুন
            </Button>
          }
        />
      )}
      <Row gutter={[24, 24]}>
        <Col span={16}>
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
            title={<><RocketOutlined /> নতুন সিমুলেশন শুরু করুন</>}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text type="secondary">একটি প্রজেক্ট সিলেক্ট করুন যা আপনি সিমুলেট করতে চান:</Text>
              <Space>
                <Select 
                  placeholder="প্রজেক্ট নির্বাচন করুন" 
                  style={{ width: 300 }}
                  onChange={setSelectedAppId}
                  value={selectedAppId}
                >
                  {projects.map(p => (
                    <Option key={p.id} value={p.id}>{p.name} ({p.type})</Option>
                  ))}
                </Select>
                <Button 
                  type="primary" 
                  icon={<PlayCircleOutlined />} 
                  disabled={!selectedAppId}
                  onClick={() => setPreviewOpen(true)}
                >
                  সিমুলেটর ওপেন করুন
                </Button>
              </Space>
            </Space>
          </Card>

          <Card
            className="glass-card"
            style={{ borderRadius: 12, marginTop: 24 }}
            title={<><MobileOutlined /> রিসেন্ট সেশনসমূহ</>}
            extra={<Button icon={<ReloadOutlined />} onClick={fetchData} loading={loading}>রিফ্রেশ</Button>}
          >
            <Table 
              columns={columns} 
              dataSource={deployments} 
              rowKey="appId"
              loading={loading}
              pagination={{ pageSize: 5 }}
              size="middle"
            />
          </Card>
        </Col>

        <Col span={8}>
          <SimulatorPreview appId={selectedAppId} />
          
          {isAdmin && (
            <Card
              className="glass-card"
              style={{ borderRadius: 12, marginTop: 24 }}
              title={<><DatabaseOutlined /> কোটা অ্যাডমিনিস্ট্রেশন</>}
            >
              <Text type="secondary" style={{ fontSize: 12 }}>
                সিমুলেটর কোটা ম্যানেজ করতে ইউজার আইডি ব্যবহার করুন:
              </Text>
              <div style={{ marginTop: 16 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <InputNumber 
                    placeholder="Quota (1-20)" 
                    min={1} 
                    max={20} 
                    id="quotaInput"
                    style={{ width: '100%' }}
                  />
                  <Button 
                    type="primary"
                    block
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
          )}
        </Col>
      </Row>

      <Drawer
        title={`সিমুলেটর প্রিভিউ: ${selectedAppId}`}
        placement="right"
        width="80%"
        onClose={() => setPreviewOpen(false)}
        open={previewOpen}
        bodyStyle={{ background: '#0a0a0c', padding: 0 }}
      >
        <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', background: '#000' }}>
          <SimulatorPreview appId={selectedAppId} />
        </div>
      </Drawer>
    </div>
  );
};

export default AdminSimulator;
