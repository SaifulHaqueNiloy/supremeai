import React from 'react';
import { Card, Form, Select, Switch, Slider, Typography, Space, Divider, message, Button } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Title, Text } = Typography;
const { Option } = Select;

interface UserSettingsProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
  chatFont: string;
  setChatFont: (value: string) => void;
}

const UserSettings: React.FC<UserSettingsProps> = ({ darkMode, setDarkMode, chatFont, setChatFont }) => {
  const { t, i18n } = useTranslation();
  const [form] = Form.useForm();

  const handleSave = (values: any) => {
    // Save language preference
    if (values.language) {
      i18n.changeLanguage(values.language);
      localStorage.setItem('preferredLanguage', values.language);
    }

    // Save theme preference
    if (typeof values.darkMode !== 'undefined') {
      setDarkMode(values.darkMode);
      localStorage.setItem('darkMode', String(values.darkMode));
    }

    // Save other preferences
    if (values.notifications !== undefined) {
      localStorage.setItem('notificationsEnabled', String(values.notifications));
    }
    if (values.focusMode !== undefined) {
      localStorage.setItem('focusMode', String(values.focusMode));
    }

    // Save chat font preference
    if (values.chatFont) {
      setChatFont(values.chatFont);
      localStorage.setItem('chatFont', values.chatFont);
    }

    message.success('Settings saved successfully');
  };

  React.useEffect(() => {
    // Load saved preferences
    const savedLanguage = localStorage.getItem('preferredLanguage') || i18n.language || 'en';
    const savedDarkMode = localStorage.getItem('darkMode') !== 'false'; // default true

    form.setFieldsValue({
      language: savedLanguage,
      darkMode: savedDarkMode,
      notifications: localStorage.getItem('notificationsEnabled') !== 'false',
      focusMode: localStorage.getItem('focusMode') === 'true',
      chatFont: localStorage.getItem('chatFont') || 'font-mono',
    });
  }, [form, i18n.language]);

  return (
    <div style={{ padding: 24 }}>
      <Title level={2} style={{ marginBottom: 24, fontWeight: 700 }}>
        {t('settings.userPreferences', 'User Settings')}
      </Title>

      <Card
        style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 12,
          marginBottom: 24
        }}
        bodyStyle={{ padding: 24 }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            language: i18n.language || 'en',
            darkMode: darkMode,
            notifications: true,
            focusMode: false,
          }}
        >
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div>
              <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }}>
                {t('settings.language', 'Language')}
              </Text>
              <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 12 }}>
                {t('settings.languageDescription', 'Choose your preferred language for the interface')}
              </Text>
              <Form.Item name="language" rules={[{ required: true }]}>
                <Select style={{ width: '100%', maxWidth: 300 }}>
                  <Option value="en">English</Option>
                  <Option value="bn">বাংলা (Bengali)</Option>
                </Select>
              </Form.Item>
            </div>

            <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '16px 0' }} />

            <div>
              <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }}>
                {t('settings.appearance', 'Appearance')}
              </Text>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {t('settings.darkMode', 'Dark Mode')}
                  </Text>
                  <Form.Item name="darkMode" valuePropName="checked" noStyle>
                    <Switch checked={darkMode} onChange={setDarkMode} />
                  </Form.Item>
                </Space>
                
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                    {t('settings.chatFont', 'AI Chat Font Style')}
                  </Text>
                  <Form.Item name="chatFont" style={{ marginBottom: 0 }}>
                    <Select style={{ width: '100%', maxWidth: 300 }}>
                      <Option value="font-mono">Standard Terminal (Mono)</Option>
                      <Option value="font-doodle">Doodle Art (Handwritten)</Option>
                      <Option value="font-floral">Floral Elegant (Cursive)</Option>
                      <Option value="font-cloudy">Cloudy Soft (Bold)</Option>
                      <Option value="font-bubble">Bubble Letters (Playful)</Option>
                      <Option value="font-sketch">Pencil Sketch (Artistic)</Option>
                    </Select>
                  </Form.Item>
                </div>
              </Space>
            </div>

            <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '16px 0' }} />

            <div>
              <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 16 }}>
                {t('settings.notifications', 'Notifications')}
              </Text>
              <Form.Item name="notifications" valuePropName="checked" style={{ marginBottom: 8 }}>
                <Switch />
              </Form.Item>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {t('settings.notificationsDescription', 'Receive notifications about system updates and alerts')}
              </Text>
            </div>

            <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '16px 0' }} />

            <div>
              <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 16 }}>
                {t('settings.focusMode', 'Focus Mode')}
              </Text>
              <Form.Item name="focusMode" valuePropName="checked" style={{ marginBottom: 8 }}>
                <Switch />
              </Form.Item>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {t('settings.focusModeDescription', 'Minimize distractions by reducing visual noise')}
              </Text>
            </div>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                  {t('settings.save', 'Save Settings')}
                </Button>
              </Space>
            </Form.Item>
          </Space>
        </Form>
      </Card>

      <Card
        style={{
          background: 'rgba(16,185,129,0.05)',
          border: '1px solid rgba(16,185,129,0.2)',
          borderRadius: 12
        }}
        bodyStyle={{ padding: 24 }}
      >
        <Title level={5} style={{ color: '#10b981', marginBottom: 12 }}>
          {t('settings.about', 'About')}
        </Title>
        <Text type="secondary" style={{ fontSize: 12 }}>
          SupremeAI Dashboard v1.0.0
          <br />
          © 2026 SupremeAI. All rights reserved.
        </Text>
      </Card>
    </div>
  );
};

export default UserSettings;
