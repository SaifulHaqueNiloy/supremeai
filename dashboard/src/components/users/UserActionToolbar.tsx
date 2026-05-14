import React from 'react';
import { Input, Button, Select } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { UserSortField } from './types';

const { Option } = Select;

interface UserActionToolbarProps {
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  sortBy: UserSortField | null;
  setSortBy: (value: UserSortField | null) => void;
  sortOrder: 'ascend' | 'descend';
  setSortOrder: (value: 'ascend' | 'descend') => void;
  onAddUser: () => void;
  onRefresh: () => void;
}

const UserActionToolbar: React.FC<UserActionToolbarProps> = ({
  searchTerm,
  setSearchTerm,
  sortBy,
  setSortBy,
  sortOrder,
  setSortOrder,
  onAddUser,
  onRefresh
}) => {
  return (
    <div className="glass-card" style={{ marginBottom: 16, padding: '16px', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', borderRadius: '12px' }}>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <Input
          placeholder="Search by email or name"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          style={{ width: 220, borderRadius: '8px' }}
        />
        <Button onClick={() => setSearchTerm('')} style={{ borderRadius: '8px' }}>
          Clear
        </Button>
      </div>
      
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <Select
          value={sortBy || ''}
          onChange={value => setSortBy(value === '' ? null : (value as UserSortField))}
          placeholder="Sort by"
          style={{ width: 140 }}
          className="custom-select"
        >
          <Option value="">No Sorting</Option>
          <Option value="email">Email</Option>
          <Option value="displayName">Name</Option>
          <Option value="tier">Role</Option>
          <Option value="isActive">Status</Option>
          <Option value="currentUsage">Usage</Option>
          <Option value="monthlyQuota">Quota</Option>
          <Option value="lastLoginAt">Last Login</Option>
        </Select>
        <Button 
          onClick={() => setSortOrder(sortOrder === 'ascend' ? 'descend' : 'ascend')}
          style={{ borderRadius: '8px' }}
        >
          {sortOrder === 'ascend' ? '▲' : '▼'}
        </Button>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={onAddUser} style={{ borderRadius: '8px' }}>
          Add User
        </Button>
        <Button icon={<ReloadOutlined />} onClick={onRefresh} style={{ borderRadius: '8px' }}>
          Refresh
        </Button>
      </div>
    </div>
  );
};

export default UserActionToolbar;
