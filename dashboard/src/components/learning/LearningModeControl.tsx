import React from 'react';
import { Card, Space, Button } from 'antd';
import { RocketOutlined } from '@ant-design/icons';

interface LearningModeControlProps {
  currentMode: string | undefined;
  onModeChange: (mode: string) => void;
  onManualTrigger: () => void;
  actionLoading: boolean;
}

const LearningModeControl: React.FC<LearningModeControlProps> = ({
  currentMode,
  onModeChange,
  onManualTrigger,
  actionLoading,
}) => {
  return (
    <Card title="Learning Mode Control" className="glass-card">
      <Space size="middle" wrap>
        <Button 
          type={currentMode === 'AGGRESSIVE' ? 'primary' : 'default'} 
          onClick={() => onModeChange('AGGRESSIVE')}
          loading={actionLoading}
        >
          Aggressive
        </Button>
        <Button 
          type={currentMode === 'BALANCED' ? 'primary' : 'default'} 
          onClick={() => onModeChange('BALANCED')}
          loading={actionLoading}
        >
          Balanced
        </Button>
        <Button 
          type={currentMode === 'MANUAL' ? 'primary' : 'default'} 
          onClick={() => onModeChange('MANUAL')}
          loading={actionLoading}
        >
          Manual
        </Button>
        <Button 
          type={currentMode === 'PAUSED' ? 'primary' : 'default'} 
          onClick={() => onModeChange('PAUSED')}
          loading={actionLoading}
          danger
        >
          Paused
        </Button>
        <div style={{ marginLeft: 24, borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: 24 }}>
          <Button 
            icon={<RocketOutlined />} 
            onClick={onManualTrigger}
            disabled={currentMode !== 'MANUAL' && currentMode !== 'BALANCED'}
            loading={actionLoading}
          >
            Trigger Neural Training
          </Button>
        </div>
      </Space>
    </Card>
  );
};

export default LearningModeControl;
