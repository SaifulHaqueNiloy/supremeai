// AdminMonitoring.tsx - Real-time System Monitoring

import React, { useState, useEffect } from 'react';
import { Layout, Card, Row, Col, Statistic, Progress, Alert, Spin, Typography, Tag, Descriptions, Button } from 'antd';
import { ThunderboltOutlined, HddOutlined, CloudServerOutlined, DatabaseOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import AdminLayout from '../components/AdminLayout';
import { authUtils } from '../lib/authUtils';

const { Title, Text } = Typography;

interface ResourceMetrics {
  memoryUsed: number;
  memoryMax: number;
  cpuLoad: number;
  availableProcessors: number;
  dbActiveConnections?: number;
  dbIdleConnections?: number;
  redisStatus?: string;
  timestamp: number;
}

import { useRole } from '../contexts/RoleContext';

const AdminMonitoring: React.FC = () => {
  const { isGuest } = useRole();
  const [metrics, setMetrics] = useState<ResourceMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    if (isGuest) return;
    setError(null);
    try {
      const response = await authUtils.fetchWithAuth('/api/system/metrics/resources');
      if (!response.ok) throw new Error(`Failed to fetch metrics: ${response.status}`);
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Server returned non-JSON response. The backend might be down or returning an error page.');
      }

      const result = await response.json();
      setMetrics(result.data || null);
    } catch (err) {
      console.error('[AdminMonitoring] Fetch Error:', err);
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const getSystemStatus = (): { status: 'healthy' | 'warning' | 'critical'; text: string } => {
    if (!metrics || !metrics.memoryMax || metrics.memoryMax <= 0) return { status: 'warning', text: 'Initializing...' };
    const memoryPercent = (metrics.memoryUsed / metrics.memoryMax) * 100;
    const cpuLoad = metrics.cpuLoad || 0;
    if (memoryPercent > 90 || cpuLoad > 80) return { status: 'critical', text: 'Critical' };
    if (memoryPercent > 75 || cpuLoad > 60) return { status: 'warning', text: 'Warning' };
    return { status: 'healthy', text: 'Healthy' };
  };

  const systemStatus = getSystemStatus();

  return (
    <AdminLayout title="System Monitoring">
      <Row gutter={[16, 16]}>
        {/* System Status Card */}
        <Col xs={24} sm={12} md={6}>
          <Card hoverable className="glass-card">
            <Statistic
              title="System Status"
              value={systemStatus.text}
              prefix={
                systemStatus.status === 'healthy' ? 
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> : 
                <WarningOutlined style={{ color: systemStatus.status === 'critical' ? '#f5222d' : '#faad14' }} />
              }
              valueStyle={{ color: systemStatus.status === 'healthy' ? '#52c41a' : systemStatus.status === 'critical' ? '#f5222d' : '#faad14' }}
            />
          </Card>
        </Col>

        {/* Memory */}
        <Col xs={24} sm={12} md={6}>
          <Card hoverable>
            <Statistic
              title="Memory Usage"
              value={metrics && metrics.memoryMax > 0 ? Math.round((metrics.memoryUsed / metrics.memoryMax) * 100) : 0}
              suffix="%"
              prefix={<HddOutlined />}
            />
            {metrics && metrics.memoryMax > 0 ? (
              <Progress 
                percent={Math.round((metrics.memoryUsed / metrics.memoryMax) * 100)} 
                status={ (metrics.memoryUsed / metrics.memoryMax) * 100 > 90 ? 'exception' : 'active' }
                style={{ marginTop: 8 }}
                strokeColor={(metrics.memoryUsed / metrics.memoryMax) * 100 > 90 ? '#f5222d' : '#1890ff'}
              />
            ) : (
              <Progress percent={0} style={{ marginTop: 8 }} />
            )}
          </Card>
        </Col>

        {/* CPU */}
        <Col xs={24} sm={12} md={6}>
          <Card hoverable>
            <Statistic
              title="CPU Load"
              value={metrics?.cpuLoad !== undefined ? metrics.cpuLoad.toFixed(1) : '0.0'}
              suffix={metrics?.availableProcessors ? `/ ${metrics.availableProcessors} cores` : ''}
              prefix={<ThunderboltOutlined />}
            />
            <Progress 
              percent={metrics && metrics.availableProcessors && metrics.availableProcessors > 0 ? Math.min((metrics.cpuLoad / metrics.availableProcessors) * 100, 100) : 0}
              style={{ marginTop: 8 }}
              strokeColor={metrics && metrics.cpuLoad > (metrics.availableProcessors || 1) * 0.8 ? '#faad14' : '#52c41a'}
            />
          </Card>
        </Col>

        {/* Database */}
        <Col xs={24} sm={12} md={6}>
          <Card hoverable>
            <Statistic
              title="DB Connections"
              value={metrics?.dbActiveConnections ?? '--'}
              prefix={<DatabaseOutlined />}
            />
            {metrics?.dbActiveConnections !== undefined && metrics?.dbIdleConnections !== undefined ? (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {metrics.dbIdleConnections} idle
              </Text>
            ) : (
              <Text type="secondary" style={{ fontSize: '12px' }}>Connection info unavailable</Text>
            )}
          </Card>
        </Col>

        {/* Redis Status */}
        <Col xs={24} sm={12} md={6}>
          <Card hoverable>
            <Statistic
              title="Redis Status"
              value={metrics?.redisStatus === 'PONG' ? 'Online' : (metrics?.redisStatus === 'DISABLED' ? 'Disabled' : 'Offline')}
              prefix={<CloudServerOutlined />}
              valueStyle={{
                color: metrics?.redisStatus === 'PONG' ? '#52c41a' : (metrics?.redisStatus === 'DISABLED' ? '#8c8c8c' : '#f5222d'),
              }}
            />
            <Tag color={metrics?.redisStatus === 'PONG' ? 'green' : (metrics?.redisStatus === 'DISABLED' ? 'default' : 'red')} style={{ marginTop: 8 }}>
              {metrics?.redisStatus === 'PONG' ? 'Operational' : (metrics?.redisStatus === 'DISABLED' ? 'Not Configured' : 'Disconnected')}
            </Tag>
          </Card>
        </Col>

        {/* Last Updated */}
        <Col xs={24} sm={12} md={6}>
          <Card hoverable>
            <Statistic
              title="Last Updated"
              value={metrics && metrics.timestamp ? new Date(metrics.timestamp).toLocaleTimeString() : 'Never'}
            />
          </Card>
        </Col>
      </Row>

      {error && (
        <Alert 
          type="error" 
          message="Monitoring Error" 
          description={error} 
          style={{ marginTop: 16 }} 
          showIcon
          action={<Button size="small" onClick={fetchMetrics}>Retry</Button>}
        />
      )}
      
      {loading && !metrics && <Spin size="large" style={{ display: 'block', margin: '40px auto' }} />}

      <Card title="Resource Details" style={{ marginTop: 24 }} className="glass-card">
        {metrics ? (
          <Descriptions bordered column={{ xs: 1, sm: 2, md: 3 }}>
            <Descriptions.Item label="Memory Used">
              {((metrics.memoryUsed ?? 0) / 1024 / 1024).toFixed(2)} MB
            </Descriptions.Item>
            <Descriptions.Item label="Memory Max">
              {((metrics.memoryMax ?? 0) / 1024 / 1024).toFixed(2)} MB
            </Descriptions.Item>
            <Descriptions.Item label="System Load">
              {metrics.cpuLoad?.toFixed(2) ?? 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Available Processors">
              {metrics.availableProcessors ?? 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="DB Active Connections">
              {metrics.dbActiveConnections ?? 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="DB Idle Connections">
              {metrics.dbIdleConnections ?? 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Redis Connection">
              {metrics.redisStatus === 'PONG' ? 'Active' : (metrics.redisStatus === 'DISABLED' ? 'Disabled' : 'Inactive')}
            </Descriptions.Item>
            <Descriptions.Item label="Data Freshness">
              {metrics.timestamp ? `${Math.floor((Date.now() - metrics.timestamp) / 1000)}s ago` : 'N/A'}
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin tip="Waiting for metrics data..." />
          </div>
        )}
      </Card>
    </AdminLayout>
  );
};

export default AdminMonitoring;
