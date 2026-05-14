import React, { useState, useEffect } from 'react';
import { 
  Typography, Card, Space, Table, Button, Tag, message, Modal, Form, Input, 
  InputNumber, Popconfirm, Select, Tooltip, Breadcrumb 
} from 'antd';
import { 
  PlusOutlined, 
  DeleteOutlined,
  ReloadOutlined,
  GlobalOutlined,
  SearchOutlined,
  SortAscendingOutlined,
  SortDescendingOutlined,
  CloseOutlined,
  DashboardOutlined,
  CloudServerOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';

const { Title, Text } = Typography;
const { Option } = Select;

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

  // Search and Sort State
  const [searchText, setSearchText] = useState('');
  const [sortBy, setSortBy] = useState<keyof VPNConnection | null>('name');
  const [sortOrder, setSortOrder] = useState<'ascend' | 'descend'>('ascend');

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

  const processedConnections = React.useMemo(() => {
    let result = connections.filter(conn => {
      const searchLower = searchText.toLowerCase();
      return (
        conn.name?.toLowerCase().includes(searchLower) ||
        conn.host?.toLowerCase().includes(searchLower) ||
        conn.username?.toLowerCase().includes(searchLower)
      );
    });

    if (sortBy) {
      result.sort((a, b) => {
        const aVal = (a as any)[sortBy] ?? '';
        const bVal = (b as any)[sortBy] ?? '';

        if (sortBy === 'createdAt') {
          return sortOrder === 'ascend' 
            ? new Date(aVal).getTime() - new Date(bVal).getTime()
            : new Date(bVal).getTime() - new Date(aVal).getTime();
        }

        if (typeof aVal === 'string' && typeof bVal === 'string') {
          return sortOrder === 'ascend' 
            ? aVal.localeCompare(bVal) 
            : bVal.localeCompare(aVal);
        }
        
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortOrder === 'ascend' ? aVal - bVal : bVal - aVal;
        }

        return 0;
      });
    }

    return result;
  }, [connections, searchText, sortBy, sortOrder]);

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
      title: <span className="text-[11px] uppercase tracking-wider opacity-60">নাম</span>, 
      dataIndex: 'name', 
      key: 'name',
      render: (text: string) => <Text strong style={{ color: 'rgba(255,255,255,0.9)' }}>{text}</Text>
    },
    { 
      title: <span className="text-[11px] uppercase tracking-wider opacity-60">সার্ভার হোস্ট</span>, 
      dataIndex: 'host', 
      key: 'host',
      render: (host: string, record: VPNConnection) => (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <Text style={{ color: '#60a5fa', fontFamily: 'monospace', fontSize: '12px' }}>{host}</Text>
          <Text style={{ color: 'rgba(255,255,255,0.2)', fontSize: '10px' }}>পোর্ট: {record.port}</Text>
        </div>
      )
    },
    { 
      title: <span className="text-[11px] uppercase tracking-wider opacity-60">স্ট্যাটাস</span>, 
      dataIndex: 'status', 
      key: 'status', 
      render: (status: string) => (
        <Tag color={status === 'CONNECTED' ? 'green' : 'default'} style={{ borderRadius: '20px', padding: '0 12px', border: 'none', background: status === 'CONNECTED' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.05)' }}>
          {status || 'IDLE'}
        </Tag>
      )
    },
    { 
      title: <span className="text-[11px] uppercase tracking-wider opacity-60">তৈরির তারিখ</span>, 
      dataIndex: 'createdAt', 
      key: 'createdAt',
      render: (date: string) => <span style={{ color: 'rgba(255,255,255,0.4)', fontFamily: 'monospace', fontSize: '11px' }}>{date ? new Date(date).toLocaleString() : 'N/A'}</span>
    },
    { 
      title: <span className="text-[11px] uppercase tracking-wider opacity-60 text-right">অ্যাকশন</span>, 
      key: 'actions', 
      align: 'right' as const,
      render: (_: any, record: VPNConnection) => (
        <Space>
          <Popconfirm
            title="আপনি কি নিশ্চিত যে আপনি এই VPN কানেকশনটি ডিলিট করতে চান?"
            onConfirm={() => record.id && handleDelete(record.id)}
            okText="হ্যাঁ"
            cancelText="না"
            overlayClassName="dark-popconfirm"
          >
            <Button 
              type="text"
              size="small" 
              icon={<DeleteOutlined />} 
              danger 
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            />
          </Popconfirm>
        </Space>
      )
    },
  ];

  return (
    <div style={{ padding: '24px', background: '#050505', minHeight: '100vh', color: '#fff' }}>
      {/* Header Section */}
      <div style={{ marginBottom: 32 }}>
        <Breadcrumb separator=">" style={{ marginBottom: 16, opacity: 0.7 }}>
          <Breadcrumb.Item href=""><DashboardOutlined /> ড্যাশবোর্ড</Breadcrumb.Item>
          <Breadcrumb.Item><CloudServerOutlined /> ইনফ্রাস্ট্রাকচার</Breadcrumb.Item>
          <Breadcrumb.Item>VPN গেটওয়ে</Breadcrumb.Item>
        </Breadcrumb>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <Title level={2} style={{ margin: 0, color: '#fff', fontWeight: 800, fontSize: '32px', letterSpacing: '-0.5px' }}>
              VPN ম্যানেজমেন্ট <span style={{ color: '#3b82f6', fontSize: '14px', fontWeight: 400, verticalAlign: 'middle', marginLeft: '8px', opacity: 0.8 }}>SECURE GATEWAY</span>
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.45)', fontSize: '16px' }}>
              নিরাপদ নেটওয়ার্ক ইনফ্রাস্ট্রাকচার এবং VPN কানেকশন নিয়ন্ত্রণ করুন
            </Text>
          </div>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => setIsModalVisible(true)}
            style={{ 
              height: '42px',
              padding: '0 24px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', 
              border: 'none',
              fontWeight: 600,
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
            }}
          >
            নতুন VPN যোগ করুন
          </Button>
        </div>
      </div>

      {/* Modern Toolbar */}
      <div className="glass-toolbar" style={{ 
        padding: '16px 24px', 
        marginBottom: '24px',
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid rgba(255, 255, 255, 0.05)', 
        borderRadius: '20px',
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        flexWrap: 'wrap', 
        gap: '20px',
        backdropFilter: 'blur(20px)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ 
            background: 'rgba(59, 130, 246, 0.1)', 
            padding: '8px', 
            borderRadius: '10px',
            border: '1px solid rgba(59, 130, 246, 0.2)'
          }}>
            <SearchOutlined style={{ color: '#3b82f6', fontSize: '18px' }} />
          </div>
          <Input
            placeholder="নাম বা হোস্ট দিয়ে খুঁজুন..."
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            variant="borderless"
            style={{ 
              width: 320, 
              height: '42px',
              fontSize: '15px',
              color: '#fff' 
            }}
            className="dark-input-minimal"
          />
        </div>
        
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <Tooltip title="রিফ্রেশ করুন">
            <Button 
              icon={<ReloadOutlined />} 
              onClick={fetchConnections} 
              loading={loading}
              style={{ 
                height: '42px',
                width: '42px',
                borderRadius: '12px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              className="hover-bright"
            />
          </Tooltip>

          <div className="toolbar-separator" />
          
          <Space size="middle">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Text style={{ 
                color: 'rgba(255,255,255,0.35)', 
                fontSize: '11px', 
                textTransform: 'uppercase', 
                letterSpacing: '1px', 
                fontWeight: 700 
              }}>সর্টিং</Text>
              <Select
                value={sortBy}
                onChange={val => setSortBy(val)}
                style={{ width: 160 }}
                className="premium-select"
                dropdownClassName="premium-dropdown"
              >
                <Option value="name">নাম</Option>
                <Option value="status">স্ট্যাটাস</Option>
                <Option value="host">সার্ভার হোস্ট</Option>
                <Option value="createdAt">তৈরির তারিখ</Option>
              </Select>
            </div>

            <Tooltip title={sortOrder === 'ascend' ? 'ক্রমানুসারে' : 'বিপরীত ক্রমানুসারে'}>
              <Button 
                onClick={() => setSortOrder(sortOrder === 'ascend' ? 'descend' : 'ascend')}
                icon={sortOrder === 'ascend' ? <SortAscendingOutlined /> : <SortDescendingOutlined />}
                style={{ 
                  height: '42px',
                  width: '42px',
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                className="hover-bright"
              />
            </Tooltip>
          </Space>
        </div>
      </div>

      <Card
        className="glass-card"
        style={{ 
          borderRadius: 24, 
          background: 'rgba(255,255,255,0.02)', 
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.3)',
          overflow: 'hidden'
        }}
        bodyStyle={{ padding: 0 }}
      >
        <Table 
          columns={columns} 
          dataSource={processedConnections} 
          rowKey="id"
          loading={loading}
          pagination={{ 
            pageSize: 10,
            className: 'admin-pagination p-4'
          }}
          size="middle"
          className="admin-table-dark"
        />
      </Card>

      <Modal
        title={
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: '#fff', fontWeight: 800, fontSize: '18px' }}>নতুন VPN কানেকশন</span>
            <span style={{ color: 'rgba(255,255,255,0.2)', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase' }}>Secure Node Configuration</span>
          </div>
        }
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
        okText="সেভ করুন"
        cancelText="বাতিল"
        centered
        className="dark-modal"
        okButtonProps={{ style: { background: '#2563eb', border: 'none', height: '40px', padding: '0 24px', borderRadius: '8px', fontWeight: 700 } }}
        cancelButtonProps={{ style: { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.6)', height: '40px', padding: '0 24px', borderRadius: '8px' } }}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate} style={{ marginTop: 24 }}>
          <Form.Item name="name" label={<Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: '12px', fontWeight: 700 }}>কানেকশন নাম</Text>} rules={[{ required: true }]}>
            <Input placeholder="e.g. SG-HighSpeed-01" className="dark-input" />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <Form.Item name="host" label={<Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: '12px', fontWeight: 700 }}>সার্ভার হোস্ট</Text>} rules={[{ required: true }]}>
              <Input placeholder="1.2.3.4" className="dark-input" style={{ fontFamily: 'monospace' }} />
            </Form.Item>
            <Form.Item name="port" label={<Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: '12px', fontWeight: 700 }}>পোর্ট</Text>} rules={[{ required: true }]} initialValue={443}>
              <InputNumber style={{ width: '100%' }} className="dark-input" />
            </Form.Item>
          </div>
          <Form.Item name="username" label={<Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: '12px', fontWeight: 700 }}>ইউজারনেম (অপশনাল)</Text>}>
            <Input placeholder="admin" className="dark-input" />
          </Form.Item>
        </Form>
      </Modal>

      <style>{`
        .glass-card {
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
        
        .dark-input-minimal::placeholder {
          color: rgba(255,255,255,0.2) !important;
        }
        
        .toolbar-separator {
          height: 24px;
          width: 1px;
          background: rgba(255,255,255,0.08);
          margin: 0 8px;
        }

        .premium-select .ant-select-selector {
          background: rgba(255,255,255,0.05) !important;
          border: 1px solid rgba(255,255,255,0.1) !important;
          border-radius: 12px !important;
          height: 42px !important;
          display: flex !important;
          align-items: center !important;
          color: #fff !important;
        }

        .premium-dropdown {
          background: #141414 !important;
          border: 1px solid rgba(255,255,255,0.1) !important;
          border-radius: 12px !important;
        }

        .premium-dropdown .ant-select-item {
          color: rgba(255,255,255,0.65) !important;
        }

        .hover-bright:hover {
          background: rgba(255,255,255,0.1) !important;
          border-color: rgba(255,255,255,0.2) !important;
          transform: translateY(-1px);
        }

        /* Table Style Unified */
        .admin-table-dark .ant-table {
          background: transparent !important;
          color: #fff !important;
        }
        .admin-table-dark .ant-table-thead > tr > th {
          background: rgba(255,255,255,0.02) !important;
          color: rgba(255,255,255,0.4) !important;
          border-bottom: 1px solid rgba(255,255,255,0.05) !important;
          font-size: 11px !important;
          text-transform: uppercase !important;
          letter-spacing: 1px !important;
          font-weight: 700 !important;
          padding: 16px 24px !important;
        }
        .admin-table-dark .ant-table-tbody > tr > td {
          border-bottom: 1px solid rgba(255,255,255,0.02) !important;
          padding: 16px 24px !important;
        }
        .admin-table-dark .ant-table-tbody > tr:hover > td {
          background: rgba(255,255,255,0.02) !important;
        }

        .dark-input {
          background: rgba(255,255,255,0.05) !important;
          border: 1px solid rgba(255,255,255,0.1) !important;
          border-radius: 10px !important;
          color: #fff !important;
          height: 42px !important;
        }
        .dark-input:focus {
          border-color: #3b82f6 !important;
          box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
        }

        .dark-modal .ant-modal-content {
          background: #141414 !important;
          border: 1px solid rgba(255,255,255,0.08) !important;
          border-radius: 20px !important;
        }
        .dark-modal .ant-modal-header {
          background: transparent !important;
          border-bottom: 1px solid rgba(255,255,255,0.05) !important;
        }
      `}</style>
    </div>
  );
};

export default AdminVPN;

