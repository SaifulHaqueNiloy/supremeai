import React from 'react';
import { Card, Form, Input, Select, Button, Row, Col, Typography, Steps, Progress, Alert } from 'antd';
import { RocketOutlined, CodeOutlined, CloudServerOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { GenerationForm, GenerationStatus } from './types';

const { Option } = Select;
const { Title, Paragraph } = Typography;

interface AppGenerationCardProps {
  generationForm: GenerationForm;
  setGenerationForm: (form: GenerationForm) => void;
  generationStatus: GenerationStatus;
  generationStep: number;
  generationProgress: number;
  generationResult: any;
  onGenerate: () => void;
}

const AppGenerationCard: React.FC<AppGenerationCardProps> = ({
  generationForm,
  setGenerationForm,
  generationStatus,
  generationStep,
  generationProgress,
  generationResult,
  onGenerate
}) => {
  return (
    <Card 
      title={<><RocketOutlined style={{ marginRight: 8, color: '#1890ff' }} /> Generate New App</>} 
      style={{ marginTop: 24 }}
      className="glass-card"
    >
      <Row gutter={24}>
        <Col xs={24} lg={12}>
          <Title level={4}>App Requirements</Title>
          <Paragraph type="secondary">
            Describe the app you want to generate. SupremeAI will analyze your requirements and create a robust application structure.
          </Paragraph>
          
          <Form layout="vertical" onFinish={onGenerate}>
            <Form.Item label="App Name" required>
              <Input 
                placeholder="e.g., E-commerce Dashboard"
                value={generationForm.name}
                onChange={e => setGenerationForm({...generationForm, name: e.target.value})}
              />
            </Form.Item>
            
            <Form.Item label="Detailed Description" required>
              <Input.TextArea 
                rows={4}
                placeholder="What should the app do? Describe main features, user roles, etc..."
                value={generationForm.description}
                onChange={e => setGenerationForm({...generationForm, description: e.target.value})}
              />
            </Form.Item>
            
            <Form.Item label="Target Platform" required>
              <Select
                placeholder="Select target platform"
                value={generationForm.platform}
                onChange={val => setGenerationForm({...generationForm, platform: val})}
              >
                <Option value="web">Web Application (React)</Option>
                <Option value="android">Android App (Kotlin)</Option>
                <Option value="ios">iOS App (SwiftUI)</Option>
                <Option value="desktop">Desktop App (JavaFX)</Option>
                <Option value="fullstack">Full-Stack Web App (Backend + Frontend)</Option>
              </Select>
            </Form.Item>
            
            <Form.Item label="Database Preference">
              <Select
                placeholder="Select database engine"
                value={generationForm.database}
                onChange={val => setGenerationForm({...generationForm, database: val})}
              >
                <Option value="PostgreSQL">PostgreSQL (Relational)</Option>
                <Option value="MySQL">MySQL (Relational)</Option>
                <Option value="MongoDB">MongoDB (NoSQL)</Option>
                <Option value="Firebase">Firebase Firestore</Option>
              </Select>
            </Form.Item>

            <Form.Item>
              <div className="custom-checkbox-wrapper" style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={generationForm.useAI || false}
                    onChange={e => setGenerationForm({...generationForm, useAI: e.target.checked})}
                    style={{ width: '18px', height: '18px' }}
                  />
                  <div>
                    <div style={{ fontWeight: 'bold' }}>Use AI-Powered Generation</div>
                    <div style={{ fontSize: '11px', opacity: 0.7 }}>Generate custom entities and optimized code structure using SupremeAI</div>
                  </div>
                </label>
              </div>
            </Form.Item>
            
            <Form.Item style={{ marginTop: 24 }}>
              <Button 
                type="primary" 
                htmlType="submit"
                icon={<RocketOutlined />}
                loading={generationStatus === 'generating'}
                size="large"
                block
                className="pulse-button"
              >
                {generationStatus === 'generating' ? 'Orchestrating AI Agents...' : 'Initialize Generation'}
              </Button>
            </Form.Item>
          </Form>
        </Col>
        
        <Col xs={24} lg={12}>
          {generationStatus !== 'idle' ? (
            <div style={{ padding: '10px', background: 'rgba(0,0,0,0.1)', borderRadius: '12px', minHeight: '300px' }}>
              <Title level={4}>Generation Pipeline</Title>
              
              <Steps
                current={generationStep}
                direction="vertical"
                size="small"
                items={[
                  { title: 'Requirements Analysis', subTitle: 'Analyzing intent', icon: <CodeOutlined />, status: generationStep > 0 ? 'finish' : 'process' },
                  { title: 'Architectural Blueprint', subTitle: 'Designing services', icon: <CloudServerOutlined />, status: generationStep > 1 ? 'finish' : generationStep === 1 ? 'process' : 'wait' },
                  { title: 'Synthesizing Components', subTitle: 'Writing code', icon: <RocketOutlined />, status: generationStep > 2 ? 'finish' : generationStep === 2 ? 'process' : 'wait' },
                  { title: 'Finalizing Deployment', subTitle: 'Packaging app', icon: <CheckCircleOutlined />, status: generationStep > 3 ? 'finish' : generationStep === 3 ? 'process' : 'wait' },
                ]}
              />
              
              <div style={{ marginTop: 32 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>Overall Completion</span>
                  <span>{generationProgress}%</span>
                </div>
                <Progress 
                  percent={generationProgress} 
                  status={generationStatus === 'error' ? 'exception' : 'active'}
                  strokeColor={{
                    '0%': '#1890ff',
                    '100%': '#52c41a',
                  }}
                  showInfo={false}
                />
              </div>
              
              {generationStatus === 'success' && generationResult && (
                <Alert
                  message="System Synthesis Complete!"
                  description={`Your ${generationForm.platform} application has been successfully generated with ${generationResult.fileCount || 0} modular files.`}
                  type="success"
                  showIcon
                  style={{ marginTop: 24, border: '1px solid #52c41a' }}
                />
              )}
              
              {generationStatus === 'error' && (
                <Alert
                  message="Pipeline Disrupted"
                  description="An error occurred during the generation process. Please check logs and try again."
                  type="error"
                  showIcon
                  style={{ marginTop: 24, border: '1px solid #ff4d4f' }}
                />
              )}
            </div>
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.05)', borderRadius: '12px', padding: '40px' }}>
              <div style={{ textAlign: 'center' }}>
                <RocketOutlined style={{ fontSize: '48px', color: '#1890ff', opacity: 0.5, marginBottom: '16px' }} />
                <Paragraph type="secondary">
                  Configure your requirements on the left to start the automated application generation pipeline.
                </Paragraph>
              </div>
            </div>
          )}
        </Col>
      </Row>
    </Card>
  );
};

export default AppGenerationCard;
