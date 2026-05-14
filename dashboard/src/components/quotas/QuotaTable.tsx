import React from 'react';
import { Table, Space, Typography, Tag, Select, Progress, Badge, Tooltip, Popconfirm, Button } from 'antd';
import { ReloadOutlined, StopOutlined } from '@ant-design/icons';
import { UserQuota } from './types';

const { Text } = Typography;
const { Option } = Select;

interface QuotaTableProps {
  users: UserQuota[];
  loading: boolean;
  onReset: (userId: string) => void;
  onTierUpdate: (userId: string, tier: string) => void;
  onDeactivate: (userId: string) => void;
}

const QuotaTable: React.FC<QuotaTableProps> = ({ 
  users, 
  loading, 
  onReset, 
  onTierUpdate, 
  onDeactivate 
}) => {
  const columns = [
    { 
      title: 'ইউজার', 
      dataIndex: 'email', 
      key: 'email',
      render: (email: string, record: UserQuota) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ color: '#fff' }}>{record.displayName || 'No Name'}</Text>
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
          onChange={(value) => onTierUpdate(record.uid, value)}
          size="small"
          dropdownStyle={{ borderRadius: 8, background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)' }}
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
              <Text style={{ fontSize: '12px', color: 'rgba(255,255,255,0.85)' }}>{usage.toLocaleString()}</Text>
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
              onConfirm={() => onReset(record.uid)}
              okText="হ্যাঁ"
              cancelText="না"
            >
              <Button size="small" shape="circle" icon={<ReloadOutlined />} style={{ background: 'rgba(255,255,255,0.05)', border: 'none', color: '#fff' }} />
            </Popconfirm>
          </Tooltip>
          
          {record.isActive && (
            <Tooltip title="ডিঅ্যাক্টিভ করুন">
              <Popconfirm
                title="অ্যাকাউন্ট ডিঅ্যাক্টিভ করতে চান?"
                onConfirm={() => onDeactivate(record.uid)}
                okText="হ্যাঁ"
                cancelText="না"
                okButtonProps={{ danger: true }}
              >
                <Button size="small" shape="circle" danger icon={<StopOutlined />} style={{ border: 'none' }} />
              </Popconfirm>
            </Tooltip>
          )}
        </Space>
      )
    },
  ];

  return (
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
  );
};

export default QuotaTable;
