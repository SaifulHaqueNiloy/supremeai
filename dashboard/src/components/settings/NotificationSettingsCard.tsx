import React from 'react';
import { Card, Form, Switch, Button, message } from 'antd';

const NotificationSettingsCard: React.FC = () => {
  return (
    <Card className="glass-card" style={{ marginTop: 16, borderRadius: '12px' }} title="Communication Preferences">
      <Form layout="vertical">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 500 }}>Email Notifications</div>
              <div style={{ fontSize: '12px', opacity: 0.6 }}>Send system updates and security alerts via email</div>
            </div>
            <Form.Item name="emailNotifications" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Switch />
            </Form.Item>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 500 }}>SMS Critical Alerts</div>
              <div style={{ fontSize: '12px', opacity: 0.6 }}>Immediate mobile alerts for system failures</div>
            </div>
            <Form.Item name="smsAlerts" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Switch />
            </Form.Item>
          </div>
        </div>

        <Button
          type="primary"
          onClick={() => {
            message.success('Notification preferences updated');
          }}
          style={{ borderRadius: '8px' }}
        >
          Save Preferences
        </Button>
      </Form>
    </Card>
  );
};

export default NotificationSettingsCard;
