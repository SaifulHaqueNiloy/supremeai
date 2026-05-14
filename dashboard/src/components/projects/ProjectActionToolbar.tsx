import React from 'react';
import { Button, Space } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';

interface ProjectActionToolbarProps {
  onNewProject: () => void;
  onRefresh: () => void;
  loading: boolean;
}

const ProjectActionToolbar: React.FC<ProjectActionToolbarProps> = ({
  onNewProject,
  onRefresh,
  loading
}) => {
  return (
    <div style={{ marginBottom: 16 }}>
      <Space>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={onNewProject}
        >
          New Project
        </Button>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={onRefresh}
          loading={loading}
        >
          Refresh
        </Button>
      </Space>
    </div>
  );
};

export default ProjectActionToolbar;
