import React, { useState, useEffect } from 'react';
import { Typography, Card, Space, Table, Button, Tag, message, Modal, Form, Input, InputNumber, Popconfirm } from 'antd';
import { 
  PlusOutlined, 
  DeleteOutlined,
  ReloadOutlined,
  GlobalOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';

const { Title, Text } = Typography;

interface VPNConnection {
  id?: string;
  name: string;
  host: string;
  port: number;
  username?: string;
  status?: string;
  createdAt?: string;
}

const AdminVPN: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [connections, setConnections] = useState<VPNConnection[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchConnections = async () => {
    setLoading(true);
    try {
      const response = await fetchWithAuth('/api/admin/vpn');
      if (response.ok) {
        const result = await response.json();
        setConnections(result.data?.connections || []);
      } else {
        message.error('VPN কানেকশন লোড করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      console.error('Error fetching VPNs:', error);
      message.error('সার্ভারের সাথে যোগাযোগ বিচ্ছিন্ন');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  const handleCreate = async (values: VPNConnection) => {
    try {
      const response = await fetchWithAuth('/api/admin/vpn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });
      if (response.ok) {
        message.success('VPN কানেকশন তৈরি হয়েছে');
        setIsModalVisible(false);
        form.resetFields();
        fetchConnections();
      } else {
        message.error('VPN তৈরি করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const response = await fetchWithAuth(`/api/admin/vpn/${id}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        message.success('VPN ডিলিট করা হয়েছে');
        fetchConnections();
      } else {
        message.error('ডিলিট করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    }
  };

  const columns = [
    { 
      title: 'নাম', 
      dataIndex: 'name', 
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    { 
      title: 'সার্ভার হোস্ট', 
      dataIndex: 'host', 
      key: 'host',
      render: (host: string, record: VPNConnection) => (
        <Text type="secondary">{host}:{record.port}</Text>
      )
    },
    { 
      title: 'স্ট্যাটাস', 
      dataIndex: 'status', 
      key: 'status', 
      render: (status: string) => (
        <Tag color={status === 'CONNECTED' ? 'green' : 'default'}>
          {status || 'IDLE'}
        </Tag>
      )
    },
    { 
      title: 'তৈরির তারিখ', 
      dataIndex: 'createdAt', 
      key: 'createdAt',
      render: (date: string) => date ? new Date(date).toLocaleString() : 'N/A'
    },
    { 
      title: 'অ্যাকশন', 
      key: 'actions', 
      render: (_: any, record: VPNConnection) => (
        <Space>
          <Popconfirm
            title="আপনি কি নিশ্চিত যে আপনি এই VPN কানেকশনটি ডিলিট করতে চান?"
            onConfirm={() => record.id && handleDelete(record.id)}
            okText="হ্যাঁ"
            cancelText="না"
          >
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      )
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={2} style={{ marginBottom: 24, fontWeight: 700 }}>
        VPN কানেকশন ম্যানেজমেন্ট
      </Title>

      <Card
        className="glass-card"
        style={{ borderRadius: 12, marginBottom: 24 }}
        bodyStyle={{ padding: 24 }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
              নতুন VPN যোগ করুন
            </Button>
            <Button icon={<ReloadOutlined />} onClick={fetchConnections} loading={loading}>
              রিফ্রেশ
            </Button>
          </Space>
          <Text type="secondary">
            <GlobalOutlined /> সিস্টেম প্রক্সি এবং সিকিউর টানেল কন্ট্রোল
          </Text>
        </div>
      </Card>

      <Card
        className="glass-card"
        style={{ borderRadius: 12 }}
        bodyStyle={{ padding: 24 }}
      >
        <Table 
          columns={columns} 
          dataSource={connections} 
          rowKey="id"
          loading={loading}
          pagination={false}
          size="middle"
        />
      </Card>

      <Modal
        title="নতুন VPN কানেকশন যোগ করুন"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
        okText="সেভ করুন"
        cancelText="বাতিল"
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="কানেকশন নাম" rules={[{ required: true }]}>
            <Input placeholder="e.g. SG-HighSpeed-01" />
          </Form.Item>
          <Form.Item name="host" label="সার্ভার হোস্ট (IP/Domain)" rules={[{ required: true }]}>
            <Input placeholder="1.2.3.4 or vpn.example.com" />
          </Form.Item>
          <Form.Item name="port" label="পোর্ট" rules={[{ required: true }]} initialValue={443}>
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="username" label="ইউজারনেম (অপশনাল)">
            <Input placeholder="admin" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AdminVPN;
