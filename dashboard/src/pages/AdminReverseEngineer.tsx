import React, { useState, useEffect } from 'react';
import {
  Typography, Card, Space, Table, Button, Tag, message, Row, Col,
  Input, Select, Progress, Modal, Descriptions, Spin, Empty, Timeline, Tooltip
} from 'antd';
import {
  CloudServerOutlined, CheckCircleOutlined, CloseCircleOutlined,
  PlayCircleOutlined, DownloadOutlined, ReloadOutlined, EyeOutlined,
  DeleteOutlined, CodeOutlined, ApartmentOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface Job {
  jobId: string;
  url: string;
  status: string;
  progress: number;
  currentPhase?: string;
  submittedAt: string;
  startedAt?: string;
  completedAt?: string;
  error?: string;
  results?: {
    observation?: any;
    auth?: any;
    endpoints?: string[];
    connectors?: Record<string, { code: string; filename: string; status: string; validation?: any }>;
  };
}

const AdminReverseEngineer: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [ submitting, setSubmitting ] = useState(false);
  const [url, setUrl] = useState('');
  const [languages, setLanguages] = useState(['python', 'typescript', 'java', 'swift', 'csharp', 'go']);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewCode, setPreviewCode] = useState('');
  const [previewLang, setPreviewLang] = useState('');

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth('/api/reverse-engineer/history?limit=50');
      if (res.ok) {
        const data = await res.json();
        setJobs(data.jobs || []);
      }
    } catch (e) {
      message.error('Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    // Poll every 10 sec
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  const submitJob = async () => {
    if (!url.trim()) {
      message.error('Please enter a URL');
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetchWithAuth('/api/reverse-engineer/submit', {
        method: 'POST',
        body: JSON.stringify({
          url,
          target_languages: languages,
          user_id: 'admin' // TODO: get from auth context
        })
      });
      if (res.ok) {
        message.success('Job submitted successfully');
        setUrl('');
        fetchJobs();
      } else {
        message.error('Failed to submit job');
      }
    } catch (e) {
      message.error('Network error');
    } finally {
      setSubmitting(false);
    }
  };

  const cancelJob = async (jobId: string) => {
    try {
      const res = await fetchWithAuth(`/api/reverse-engineer/job/${jobId}`, { method: 'DELETE' });
      if (res.ok) {
        message.success('Job cancelled');
        fetchJobs();
      }
    } catch (e) {
      message.error('Failed to cancel');
    }
  };

  const columns = [
    {
      title: 'Job ID',
      dataIndex: 'jobId',
      key: 'jobId',
      render: (id: string) => <Text code copyable>{id.slice(0, 8)}</Text>
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      render: (url: string) => <Text ellipsis style={{ maxWidth: 200 }}>{url}</Text>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'COMPLETED' ? 'green' : status === 'FAILED' ? 'red' : status === 'CANCELLED' ? 'orange' : 'blue';
        return <Tag color={color}>{status}</Tag>;
      }
    },
    {
      title: 'Progress',
      dataIndex: 'progress',
      key: 'progress',
      render: (p: number) => (
        <Progress percent={Math.round(p)} size="small" status={p === 100 ? 'success' : 'active'} />
      )
    },
    {
      title: 'Phase',
      dataIndex: 'currentPhase',
      key: 'currentPhase',
      render: (phase?: string) => phase ? <Text type="secondary">{phase}</Text> : '-'
    },
    {
      title: 'Submitted',
      dataIndex: 'submittedAt',
      key: 'submittedAt',
      render: (ts: string) => new Date(ts).toLocaleTimeString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Job) => (
        <Space>
          {record.status === 'COMPLETED' && record.results && (
            <>
              <Tooltip title="View Connectors">
                <Button size="small" icon={<CodeOutlined />} onClick={() => {
                  setSelectedJob(record);
                  setPreviewOpen(true);
                }} />
              </Tooltip>
              <Tooltip title="Download All">
                <Button size="small" icon={<DownloadOutlined />} onClick={() => {
                  // TODO: ZIP download endpoint
                  message.info('Download all not yet implemented');
                }} />
              </Tooltip>
            </>
          )}
          {(record.status === 'PENDING' || record.status === 'ANALYZING' || record.status === 'GENERATING') && (
            <Tooltip title="Cancel">
              <Button size="small" danger icon={<DeleteOutlined />} onClick={() => cancelJob(record.jobId)} />
            </Tooltip>
          )}
          <Button size="small" icon={<ReloadOutlined />} onClick={fetchJobs} />
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={2} style={{ marginBottom: 24, fontWeight: 700 }}>
        <ApartmentOutlined /> Website Reverse Engineering
      </Title>

      <Card bordered={false} className="glass-card" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={4}>Submit New Analysis</Title>
          <Input.Search
            placeholder="https://example.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onSearch={submitJob}
            loading={submitting}
            enterButton={<><CloudServerOutlined /> Analyze</>}
            size="large"
          />
          <div>
            <Text type="secondary">Target Languages: </Text>
            <Select
              mode="multiple"
              value={languages}
              onChange={setLanguages}
              style={{ width: 400 }}
              placeholder="Select languages"
            >
              <Option value="python">Python</Option>
              <Option value="typescript">TypeScript</Option>
              <Option value="java">Java</Option>
              <Option value="swift">Swift</Option>
              <Option value="csharp">C#</Option>
              <Option value="go">Go</Option>
            </Select>
          </div>
        </Space>
      </Card>

      <Card
        className="glass-card"
        title={<><CloudServerOutlined /> Analysis Jobs</>}
        extra={<Button icon={<ReloadOutlined />} onClick={fetchJobs} loading={loading}>Refresh</Button>}
      >
        <Table
          columns={columns}
          dataSource={jobs}
          rowKey="jobId"
          loading={loading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: <Empty description="No jobs yet" /> }}
        />
      </Card>

      {/* Connectors Preview Modal */}
      <Modal
        title="Generated Connectors"
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setPreviewOpen(false)}>Close</Button>
        ]}
      >
        {selectedJob && selectedJob.results?.connectors && (
          <Row gutter={[16, 16]}>
            {Object.entries(selectedJob.results.connectors).map(([lang, connector]: [string, any]) => (
              <Col span={12} key={lang}>
                <Card
                  size="small"
                  title={lang.toUpperCase()}
                  extra={
                    connector.status === 'VALIDATED' ?
                      <Tag color="green" icon={<CheckCircleOutlined />}>Valid</Tag> :
                      <Tag color="red" icon={<CloseCircleOutlined />}>Failed</Tag>
                  }
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text code>{connector.filename}</Text>
                    <Button
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => {
                        setPreviewCode(connector.code);
                        setPreviewLang(lang);
                      }}
                    >
                      View Code
                    </Button>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        )}

        {/* Code preview */}
        {previewCode && (
          <div style={{ marginTop: 24 }}>
            <Title level={5}>Code Preview ({previewLang})</Title>
            <pre style={{
              background: '#1e1e1e',
              color: '#d4d4d4',
              padding: 16,
              borderRadius: 8,
              overflow: 'auto',
              maxHeight: 400
            }}>
              <code>{previewCode}</code>
            </pre>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AdminReverseEngineer;
