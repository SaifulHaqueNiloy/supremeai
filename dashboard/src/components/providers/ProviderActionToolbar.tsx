import React from 'react';
import { Space, Button, Popconfirm } from 'antd';
import { PlusOutlined, ReloadOutlined, ThunderboltOutlined, DeleteOutlined } from '@ant-design/icons';

interface Props {
  loading: boolean;
  testingAll: boolean;
  deadCount: number;
  onAdd: () => void;
  onRefresh: () => void;
  onTestAll: () => void;
  onRemoveDead: () => void;
}

const ProviderActionToolbar: React.FC<Props> = ({ 
  loading, 
  testingAll, 
  deadCount, 
  onAdd, 
  onRefresh, 
  onTestAll, 
  onRemoveDead 
}) => {
  return (
    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={onAdd}>
          Add Provider
        </Button>
        <Button icon={<ReloadOutlined />} onClick={onRefresh} loading={loading}>
          Refresh
        </Button>
      </Space>
      <Space>
        <Button 
          icon={<ThunderboltOutlined />} 
          onClick={onTestAll} 
          loading={testingAll}
          style={{ background: '#f6ffed', borderColor: '#b7eb8f', color: '#389e0d' }}
        >
          Test All Active Keys
        </Button>
        {deadCount > 0 && (
          <Popconfirm title="Remove all dead providers?" onConfirm={onRemoveDead}>
            <Button danger icon={<DeleteOutlined />}>
              Remove {deadCount} Dead Keys
            </Button>
          </Popconfirm>
        )}
      </Space>
    </div>
  );
};

export default ProviderActionToolbar;
