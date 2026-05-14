import React from 'react';
import { Modal, Form, Input, Select, Button, Space, message } from 'antd';
import { ThunderboltOutlined } from '@ant-design/icons';
import { Provider } from './types';
import AISuggestionInformer from '../AISuggestionInformer';
import { authUtils } from '../../lib/authUtils';

const { Option } = Select;

interface Props {
  visible: boolean;
  editingProvider: Provider | null;
  onCancel: () => void;
  onSubmit: (values: any) => void;
}

const ProviderModal: React.FC<Props> = ({ visible, editingProvider, onCancel, onSubmit }) => {
  const [form] = Form.useForm();

  React.useEffect(() => {
    if (visible) {
      if (editingProvider) {
        form.setFieldsValue({
          ...editingProvider,
          models: editingProvider.models?.join(', ')
        });
      } else {
        form.resetFields();
      }
    }
  }, [visible, editingProvider, form]);

  const handleSuggestRoles = async () => {
    if (!editingProvider?.id) return;
    try {
      const response = await authUtils.fetchWithAuth(`/api/admin/providers/${editingProvider.id}/suggest-roles`);
      if (response.ok) {
        const result = await response.json();
        const suggestions = result.data || [];
        form.setFieldsValue({ assignedRoles: suggestions });
        message.success(`সিস্টেম ${suggestions.join(', ')} রোলগুলো সাজেস্ট করেছে`);
      }
    } catch (err) {
      message.error('সাজেশন লোড করা যায়নি');
    }
  };

  return (
    <Modal
      title={editingProvider ? 'Edit Provider' : 'Add New Provider'}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={500}
    >
      <Form form={form} layout="vertical" onFinish={onSubmit}>
        <Form.Item name="name" label="Provider Name" rules={[{ required: true }]}>
          <Input placeholder="e.g., OpenAI" />
        </Form.Item>
        <Form.Item name="type" label="Type" rules={[{ required: true }]}>
          <Select placeholder="Select type">
            <Option value="openai">OpenAI</Option>
            <Option value="anthropic">Anthropic</Option>
            <Option value="google">Google AI</Option>
            <Option value="custom">Custom</Option>
          </Select>
        </Form.Item>
        <Form.Item name="baseUrl" label="Base URL" rules={[{ required: true }]}>
          <Input placeholder="https://api.openai.com/v1" />
        </Form.Item>
        <Form.Item name="apiKey" label="API Key">
          <Input.Password 
            placeholder="sk-..." 
            suffix={<AISuggestionInformer 
              context="provider_api_key" 
              onSelect={(val) => form.setFieldValue('apiKey', val)} 
            />}
          />
        </Form.Item>
        <Form.Item name="models" label="Models (comma-separated)">
          <Input 
            placeholder="gpt-4, gpt-3.5-turbo" 
            suffix={<AISuggestionInformer 
              context="provider_models" 
              onSelect={(val) => form.setFieldValue('models', val)} 
            />}
          />
        </Form.Item>
        <Form.Item name="status" label="Status" initialValue="active">
          <Select>
            <Option value="active">Active</Option>
            <Option value="inactive">Inactive</Option>
            <Option value="error">Error</Option>
          </Select>
        </Form.Item>
        <Form.Item label="Model Assignment (Work Roles)">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Form.Item name="assignedRoles" noStyle>
              <Select mode="multiple" placeholder="Select roles for this model">
                <Option value="coding">Coding & Software Dev</Option>
                <Option value="security">Security Audit & Hacking</Option>
                <Option value="reasoning">Advanced Reasoning</Option>
                <Option value="fast_chat">Fast Chat & UI Help</Option>
                <Option value="multimodal">Vision & Multimodal</Option>
                <Option value="general_chat">General Chat</Option>
              </Select>
            </Form.Item>
            {editingProvider?.id && (
              <Button 
                size="small" 
                icon={<ThunderboltOutlined />} 
                onClick={handleSuggestRoles}
                ghost
                type="primary"
              >
                Auto-Suggest Roles
              </Button>
            )}
          </Space>
        </Form.Item>
        <Form.Item style={{ marginTop: 24 }}>
          <Space>
            <Button type="primary" htmlType="submit">
              {editingProvider ? 'Update' : 'Add'}
            </Button>
            <Button onClick={onCancel}>Cancel</Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ProviderModal;
