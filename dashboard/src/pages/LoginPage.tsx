// LoginPage.tsx - SupremeAI Authentication Portal
import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Space, Divider, Select, Avatar, Badge, Tabs, Modal } from 'antd';
import { UserOutlined, LockOutlined, RobotOutlined, CrownOutlined, LoginOutlined, MailOutlined, UserAddOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { motion } from 'framer-motion';
import { authUtils } from '../lib/authUtils';
import { useRole } from '../contexts/RoleContext';

const { Title, Text } = Typography;
const { Option } = Select;

interface LoginForm {
  email: string;
  password: string;
  role: 'guest' | 'user' | 'admin';
}

interface CreateUserForm {
  email: string;
  password: string;
  confirmPassword: string;
  fullName: string;
  role: 'user' | 'admin';
}

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [createUserLoading, setCreateUserLoading] = useState(false);
  const [createUserModalVisible, setCreateUserModalVisible] = useState(false);
  const [form] = Form.useForm<LoginForm>();
  const [createUserForm] = Form.useForm<CreateUserForm>();
  const { refreshUser } = useRole();

  const handleLogin = async (values: LoginForm) => {
    setLoading(true);
    try {
      // Simulate authentication - in real app, this would call your auth API
      if (values.role === 'guest') {
        // Guest mode - no authentication needed
        message.success('গেস্ট মোডে প্রবেশ করা হয়েছে!');
        setTimeout(() => {
          window.location.href = '/';
        }, 1000);
        return;
      }

      // For demo purposes, accept these credentials
      const validCredentials = {
        admin: { email: 'admin@supreme.ai', password: 'admin123' },
        user: { email: 'user@supreme.ai', password: 'user123' }
      };

      const roleCreds = validCredentials[values.role as keyof typeof validCredentials];
      if (!roleCreds) {
        throw new Error('Invalid role selected');
      }

      if (values.email !== roleCreds.email || values.password !== roleCreds.password) {
        throw new Error('Invalid credentials');
      }

      // Simulate successful authentication
      const token = `demo-token-${values.role}-${Date.now()}`;
      const userData = {
        uid: `demo-${values.role}-user`,
        email: values.email,
        role: values.role,
        tier: values.role,
        displayName: `${values.role.charAt(0).toUpperCase() + values.role.slice(1)} User`,
        photoURL: null,
        emailVerified: true
      };

      authUtils.setToken(token);
      authUtils.setCurrentUser(userData);

      message.success(`${values.role.charAt(0).toUpperCase() + values.role.slice(1)} মোডে লগইন সফল!`);
      refreshUser();

      setTimeout(() => {
        window.location.href = '/';
      }, 1500);

    } catch (error: any) {
      message.error(error.message || 'লগইন ব্যর্থ হয়েছে!');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (values: CreateUserForm) => {
    setCreateUserLoading(true);
    try {
      // Validate password confirmation
      if (values.password !== values.confirmPassword) {
        throw new Error('পাসওয়ার্ড মিলছে না!');
      }

      // Validate password strength
      if (values.password.length < 6) {
        throw new Error('পাসওয়ার্ড কমপক্ষে ৬ অক্ষর হতে হবে!');
      }

      // Simulate user creation - in real app, this would call your registration API
      const token = `user-${Date.now()}-${Math.random().toString(36).substring(7)}`;
      const userData = {
        uid: `user-${Date.now()}`,
        email: values.email,
        role: values.role,
        tier: values.role,
        displayName: values.fullName,
        photoURL: null,
        emailVerified: false
      };

      authUtils.setToken(token);
      authUtils.setCurrentUser(userData);

      message.success(`নতুন ${values.role === 'admin' ? 'অ্যাডমিন' : 'ইউজার'} অ্যাকাউন্ট তৈরি সফল!`);
      setCreateUserModalVisible(false);
      createUserForm.resetFields();

      refreshUser();

      setTimeout(() => {
        window.location.href = '/';
      }, 1500);

    } catch (error: any) {
      message.error(error.message || 'ইউজার তৈরি করতে ব্যর্থ হয়েছে!');
    } finally {
      setCreateUserLoading(false);
    }
  };

  const quickLogin = (role: 'guest' | 'user' | 'admin') => {
    if (role === 'guest') {
      message.success('গেস্ট মোডে প্রবেশ করা হয়েছে!');
      setTimeout(() => {
        window.location.href = '/';
      }, 500);
      return;
    }

    const demoCreds = {
      admin: { email: 'admin@supreme.ai', password: 'admin123' },
      user: { email: 'user@supreme.ai', password: 'user123' }
    };

    form.setFieldsValue({
      email: demoCreds[role].email,
      password: demoCreds[role].password,
      role: role
    });

    // Auto-submit after a brief delay
    setTimeout(() => {
      form.submit();
    }, 300);
  };

  return (
    <div className="login-container" style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0a0a0c 0%, #1a1a1f 50%, #0a0a0c 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background Effects */}
      <div className="bg-grid" />
      <div className="hex-grid" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        style={{ width: '100%', maxWidth: '420px', zIndex: 10 }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            style={{
              background: 'linear-gradient(135deg, var(--neon-blue), var(--neon-purple))',
              padding: '20px',
              borderRadius: '16px',
              boxShadow: '0 0 40px rgba(0, 243, 255, 0.3)',
              marginBottom: '24px'
            }}
          >
            <RobotOutlined style={{ fontSize: '48px', color: '#000', marginBottom: '16px' }} />
            <Title level={2} style={{ color: '#000', margin: 0, fontWeight: 900 }}>
              SUPREME AI
            </Title>
            <Text style={{ color: '#000', fontSize: '14px', opacity: 0.8 }}>
              কমান্ড সেন্টার অথেন্টিকেশন
            </Text>
          </motion.div>
        </div>

        {/* Login Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card
            className="glass-panel"
            style={{
              background: 'rgba(8, 8, 16, 0.9)',
              border: '1px solid rgba(0, 243, 255, 0.3)',
              borderRadius: '16px',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)'
            }}
          >
            <Tabs
              defaultActiveKey="login"
              centered
              style={{ color: 'var(--text-main)' }}
              tabBarStyle={{
                borderBottom: '1px solid rgba(255,255,255,0.1)',
                marginBottom: '20px'
              }}
            >
              <Tabs.TabPane tab="লগইন করুন" key="login">
                <Form
                  form={form}
                  layout="vertical"
                  onFinish={handleLogin}
                  initialValues={{ role: 'guest' }}
                  size="large"
                >
                  <Form.Item
                    name="role"
                    label={<Text style={{ color: 'var(--text-main)', fontWeight: 600 }}>অ্যাক্সেস লেভেল</Text>}
                  >
                    <Select
                      style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}
                      onChange={(value) => {
                        if (value === 'guest') {
                          form.setFieldsValue({ email: '', password: '' });
                        }
                      }}
                    >
                      <Option value="guest">
                        <Space>
                          <RobotOutlined />
                          <span>গেস্ট মোড (শুধুমাত্র দেখার জন্য)</span>
                        </Space>
                      </Option>
                      <Option value="user">
                        <Space>
                          <UserOutlined />
                          <span>ইউজার মোড (সীমিত অ্যাক্সেস)</span>
                        </Space>
                      </Option>
                      <Option value="admin">
                        <Space>
                          <CrownOutlined />
                          <span>অ্যাডমিন মোড (পূর্ণ অ্যাক্সেস)</span>
                        </Space>
                      </Option>
                    </Select>
                  </Form.Item>

                  <Form.Item
                    noStyle
                    shouldUpdate={(prevValues, currentValues) => prevValues.role !== currentValues.role}
                  >
                    {({ getFieldValue }) => getFieldValue('role') !== 'guest' && (
                      <>
                        <Form.Item
                          name="email"
                          rules={[
                            { required: true, message: 'ইমেইল প্রয়োজন!' },
                            { type: 'email', message: 'সঠিক ইমেইল ফরম্যাট দিন!' }
                          ]}
                        >
                          <Input
                            prefix={<MailOutlined style={{ color: 'var(--neon-blue)' }} />}
                            placeholder="ইমেইল অ্যাড্রেস"
                            style={{
                              background: 'rgba(255,255,255,0.05)',
                              border: '1px solid rgba(255,255,255,0.1)',
                              color: 'var(--text-main)'
                            }}
                          />
                        </Form.Item>

                        <Form.Item
                          name="password"
                          rules={[{ required: true, message: 'পাসওয়ার্ড প্রয়োজন!' }]}
                        >
                          <Input.Password
                            prefix={<LockOutlined style={{ color: 'var(--neon-blue)' }} />}
                            placeholder="পাসওয়ার্ড"
                            style={{
                              background: 'rgba(255,255,255,0.05)',
                              border: '1px solid rgba(255,255,255,0.1)',
                              color: 'var(--text-main)'
                            }}
                          />
                        </Form.Item>
                      </>
                    )}
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      block
                      size="large"
                      style={{
                        background: 'linear-gradient(135deg, var(--neon-blue), var(--neon-purple))',
                        border: 'none',
                        height: '48px',
                        fontWeight: 700,
                        fontSize: '16px',
                        borderRadius: '8px'
                      }}
                      icon={<LoginOutlined />}
                    >
                      {loading ? 'লগইন হচ্ছে...' : 'লগইন করুন'}
                    </Button>
                  </Form.Item>
                </Form>

                <Divider style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                  <Text style={{ color: 'var(--text-dim)' }}>অথবা দ্রুত লগইন</Text>
                </Divider>

                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button
                    onClick={() => quickLogin('guest')}
                    block
                    style={{
                      background: 'rgba(0, 243, 255, 0.1)',
                      border: '1px solid var(--neon-blue)',
                      color: 'var(--neon-blue)',
                      height: '40px'
                    }}
                    icon={<RobotOutlined />}
                  >
                    গেস্ট মোডে প্রবেশ করুন
                  </Button>

                  <Button
                    onClick={() => quickLogin('user')}
                    block
                    style={{
                      background: 'rgba(16, 185, 129, 0.1)',
                      border: '1px solid var(--success)',
                      color: 'var(--success)',
                      height: '40px'
                    }}
                    icon={<UserOutlined />}
                  >
                    ইউজার মোড ডেমো
                  </Button>

                  <Button
                    onClick={() => quickLogin('admin')}
                    block
                    style={{
                      background: 'rgba(188, 19, 254, 0.1)',
                      border: '1px solid var(--neon-purple)',
                      color: 'var(--neon-purple)',
                      height: '40px'
                    }}
                    icon={<CrownOutlined />}
                  >
                    অ্যাডমিন মোড ডেমো
                  </Button>
                </Space>

                <div style={{ marginTop: '24px', textAlign: 'center' }}>
                  <Text style={{ color: 'var(--text-dim)', fontSize: '12px' }}>
                    ডেমো ক্রেডেনশিয়ালস:
                    <br />
                    Admin: admin@supreme.ai / admin123
                    <br />
                    User: user@supreme.ai / user123
                  </Text>
                </div>
              </Tabs.TabPane>

              <Tabs.TabPane tab="নতুন ইউজার তৈরি করুন" key="register">
                <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                  <Text style={{ color: 'var(--text-dim)', fontSize: '14px' }}>
                    নতুন অ্যাকাউন্ট তৈরি করে SupremeAI এর পূর্ণ ফিচার ব্যবহার করুন
                  </Text>
                </div>

                <Form
                  form={createUserForm}
                  layout="vertical"
                  onFinish={handleCreateUser}
                  initialValues={{ role: 'user' }}
                  size="large"
                >
                  <Form.Item
                    name="fullName"
                    rules={[{ required: true, message: 'পূর্ণ নাম প্রয়োজন!' }]}
                  >
                    <Input
                      prefix={<UserOutlined style={{ color: 'var(--neon-blue)' }} />}
                      placeholder="পূর্ণ নাম"
                      style={{
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        color: 'var(--text-main)'
                      }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: 'ইমেইল প্রয়োজন!' },
                      { type: 'email', message: 'সঠিক ইমেইল ফরম্যাট দিন!' }
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined style={{ color: 'var(--neon-blue)' }} />}
                      placeholder="ইমেইল অ্যাড্রেস"
                      style={{
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        color: 'var(--text-main)'
                      }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[
                      { required: true, message: 'পাসওয়ার্ড প্রয়োজন!' },
                      { min: 6, message: 'পাসওয়ার্ড কমপক্ষে ৬ অক্ষর হতে হবে!' }
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined style={{ color: 'var(--neon-blue)' }} />}
                      placeholder="পাসওয়ার্ড"
                      style={{
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        color: 'var(--text-main)'
                      }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="confirmPassword"
                    rules={[
                      { required: true, message: 'পাসওয়ার্ড কনফার্ম করুন!' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('password') === value) {
                            return Promise.resolve();
                          }
                          return Promise.reject(new Error('পাসওয়ার্ড মিলছে না!'));
                        },
                      }),
                    ]}
                  >
                    <Input.Password
                      prefix={<CheckCircleOutlined style={{ color: 'var(--neon-blue)' }} />}
                      placeholder="পাসওয়ার্ড আবার লিখুন"
                      style={{
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        color: 'var(--text-main)'
                      }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="role"
                    label={<Text style={{ color: 'var(--text-main)', fontWeight: 600 }}>ইউজার টাইপ</Text>}
                  >
                    <Select style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                      <Option value="user">
                        <Space>
                          <UserOutlined />
                          <span>সাধারণ ইউজার</span>
                        </Space>
                      </Option>
                      <Option value="admin">
                        <Space>
                          <CrownOutlined />
                          <span>অ্যাডমিন ইউজার</span>
                        </Space>
                      </Option>
                    </Select>
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={createUserLoading}
                      block
                      size="large"
                      style={{
                        background: 'linear-gradient(135deg, var(--success), var(--neon-blue))',
                        border: 'none',
                        height: '48px',
                        fontWeight: 700,
                        fontSize: '16px',
                        borderRadius: '8px'
                      }}
                      icon={<UserAddOutlined />}
                    >
                      {createUserLoading ? 'তৈরি হচ্ছে...' : 'অ্যাকাউন্ট তৈরি করুন'}
                    </Button>
                  </Form.Item>
                </Form>

                <div style={{ marginTop: '16px', textAlign: 'center' }}>
                  <Text style={{ color: 'var(--text-dim)', fontSize: '12px' }}>
                    অ্যাকাউন্ট তৈরি করলে আপনি SupremeAI এর সব ফিচার ব্যবহার করতে পারবেন
                  </Text>
                </div>
              </Tabs.TabPane>
            </Tabs>
          </Card>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          style={{ textAlign: 'center', marginTop: '24px' }}
        >
          <Text style={{ color: 'var(--text-dim)', fontSize: '12px' }}>
            SupremeAI Command Center v4.2.0
          </Text>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default LoginPage;