import React from 'react';
import { Table, Space, Button, Tag, Popconfirm, Typography } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { Provider } from './types';

const { Text } = Typography;

interface Props {
  providers: Provider[];
  loading: boolean;
  onEdit: (provider: Provider) => void;
  onDelete: (id: string) => void;
}

const ProvidersTable: React.FC<Props> = ({ providers, loading, onEdit, onDelete }) => {
  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: 'Base URL',
      dataIndex: 'baseUrl',
      key: 'baseUrl',
      ellipsis: true,
    },
    {
      title: 'Models',
      dataIndex: 'models',
      key: 'models',
      render: (models: string[]) => models ? models.slice(0, 3).join(', ') + (models.length > 3 ? ` +${models.length - 3} more` : '') : '-',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'active' ? 'green' : status === 'error' ? 'red' : 'default';
        return <Tag color={color}>{status ? status.toUpperCase() : 'UNKNOWN'}</Tag>;
      },
    },
    {
      title: 'Roles',
      dataIndex: 'assignedRoles',
      key: 'assignedRoles',
      render: (roles: string[]) => (
        <div style={{ maxWidth: 150 }}>
          {roles?.map(r => <Tag key={r} color="purple" style={{ marginBottom: 4 }}>{r}</Tag>) || '-'}
        </div>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Provider) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => onEdit(record)}>
            Edit
          </Button>
          <Popconfirm title="Delete provider?" onConfirm={() => onDelete(record.id!)}>
            <Button size="small" danger icon={<DeleteOutlined />}>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={providers}
      rowKey="id"
      pagination={{ pageSize: 15 }}
      loading={loading}
    />
  );
};

export default ProvidersTable;
