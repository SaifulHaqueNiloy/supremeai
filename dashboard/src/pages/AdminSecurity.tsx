import React, { useState, useEffect } from 'react';
import { Typography, Space, Row, Col, message, Spin, Badge, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';
import AISuggestionInformer from '../components/AISuggestionInformer';

// Modular Components
import HealthScoreCard from '../components/security/HealthScoreCard';
import SelfHealingPanel from '../components/security/SelfHealingPanel';
import CyberLearningPanel from '../components/security/CyberLearningPanel';
import SystemAuditPanel from '../components/security/SystemAuditPanel';
import SurveillancePanel from '../components/security/SurveillancePanel';

const { Title, Text } = Typography;

const AdminSecurity: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [healingStatus, setHealingStatus] = useState<any>(null);
  const [systemStats, setSystemStats] = useState<any>(null);
  const [testError, setTestError] = useState('');
  const [fixing, setFixing] = useState(false);
  const [fixResult, setFixResult] = useState<any>(null);
  const [cyberSkills, setCyberSkills] = useState<any[]>([]);
  const [protections, setProtections] = useState<any[]>([]);
  const [auditing, setAuditing] = useState(false);
  const [auditReport, setAuditReport] = useState<any>(null);
  const [learning, setLearning] = useState(false);
  const [learnTopic, setLearnTopic] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [healingRes, contractRes, skillsRes, protectRes] = await Promise.all([
        fetchWithAuth('/api/self-healing/status'),
        fetchWithAuth('/api/admin/dashboard/contract'),
        fetchWithAuth('/api/admin/security/cyber/skills'),
        fetchWithAuth('/api/admin/security/cyber/protections')
      ]);

      if (healingRes.ok) {
        setHealingStatus(await healingRes.json());
      }
      if (contractRes.ok) {
        const data = await contractRes.json();
        setSystemStats(data.data?.stats);
      }
      if (skillsRes.ok) {
        const data = await skillsRes.json();
        setCyberSkills(data.data || []);
      }
      if (protectRes.ok) {
        const data = await protectRes.json();
        setProtections(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching security data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const handleTestFix = async () => {
    if (!testError.trim()) {
      message.warning('অনুগ্রহ করে একটি এরর মেসেজ লিখুন');
      return;
    }

    setFixing(true);
    try {
      const response = await fetchWithAuth('/api/self-healing/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: testError })
      });

      if (response.ok) {
        const result = await response.json();
        setFixResult(result);
        message.success('সিস্টেম এররটি বিশ্লেষণ করেছে');
      } else {
        message.error('এরর ডিটেকশন ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    } finally {
      setFixing(false);
    }
  };

  const handleRunAudit = async () => {
    setAuditing(true);
    try {
      const response = await fetchWithAuth('/api/admin/security/cyber/audit', { method: 'POST' });
      if (response.ok) {
        const result = await response.json();
        setAuditReport(result.data);
        message.success('Self-Audit completed successfully');
      }
    } catch (error) {
      message.error('Audit failed');
    } finally {
      setAuditing(false);
    }
  };

  const handleStartLearning = async () => {
    if (!learnTopic.trim()) return;
    setLearning(true);
    try {
      const response = await fetchWithAuth('/api/admin/security/cyber/learn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: learnTopic })
      });
      if (response.ok) {
        message.success(`System started learning defense for: ${learnTopic}`);
        setLearnTopic('');
        fetchData();
      }
    } catch (error) {
      message.error('Learning cycle failed');
    } finally {
      setLearning(false);
    }
  };

  if (loading && !systemStats) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0a0a0a' }}>
        <Spin size="large" tip="সিকিউরিটি ডাটা লোড হচ্ছে..." />
      </div>
    );
  }

  const healthScore = systemStats?.systemHealthScore || 100;
  const healthStatus = systemStats?.systemHealthStatus || 'healthy';
  const healthReason = systemStats?.systemHealthReason || "All systems operational";

  return (
    <div style={{ padding: 24, background: '#0a0a0a', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#fff', fontWeight: 700 }}>
          সিকিউরিটি & রেজিলিয়েন্স
        </Title>
        <Space>
          <Badge status="processing" text={<Text style={{ color: '#10b981' }}>Cyber Guard Active</Text>} />
          <Button icon={<ReloadOutlined />} onClick={fetchData} ghost style={{ color: '#fff' }} />
        </Space>
      </div>

      <AISuggestionInformer 
        title="Active Threat Mitigation & Hardening"
        context="Cyber Guard & System Resilience"
        suggestions={[
          {
            id: 'block-ip-anomaly',
            title: 'Block Suspected Botnet IP',
            description: 'Detected 450+ failed login attempts from IP 103.45.12.89 in the last 10 minutes. Suggesting an immediate firewall block for this range.',
            impact: 'security',
            confidence: 0.98,
            autoExecutable: false
          },
          {
            id: 'rotate-keys',
            title: 'Rotate Stale API Secrets',
            description: 'Database credentials haven\'t been rotated in 90 days. System suggests a zero-downtime rotation to maintain security posture.',
            impact: 'security',
            confidence: 0.89,
            autoExecutable: true
          }
        ]}
        onApprove={(id) => message.success(`Security protocol initiated: ${id}`)}
        onDecline={(id) => message.info(`Security suggestion ${id} dismissed.`)}
      />

      <Row gutter={[24, 24]}>
        {/* System Health Score */}
        <Col xs={24} lg={8}>
          <HealthScoreCard 
            healthScore={healthScore} 
            healthStatus={healthStatus} 
            healthReason={healthReason} 
          />
        </Col>

        {/* Self-Healing Status */}
        <Col xs={24} lg={16}>
          <SelfHealingPanel 
            healingStatus={healingStatus}
            testError={testError}
            setTestError={setTestError}
            onTestFix={handleTestFix}
            fixing={fixing}
            fixResult={fixResult}
          />
        </Col>

        {/* Cyber Learning & Hacking Defense */}
        <Col xs={24} lg={12}>
          <CyberLearningPanel 
            learnTopic={learnTopic}
            setLearnTopic={setLearnTopic}
            onStartLearning={handleStartLearning}
            learning={learning}
            cyberSkills={cyberSkills}
          />
        </Col>

        {/* System Self-Audit */}
        <Col xs={24} lg={12}>
          <SystemAuditPanel 
            onRunAudit={handleRunAudit}
            auditing={auditing}
            auditReport={auditReport}
            protections={protections}
          />
        </Col>

        {/* Surveillance Panel */}
        <Col xs={24}>
          <SurveillancePanel />
        </Col>
      </Row>

      <style>{`
        .glass-card {
          border-radius: 16px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.2);
          transition: all 0.3s ease;
        }
        .glass-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 24px rgba(0,0,0,0.4);
          background: rgba(255,255,255,0.04) !important;
        }
        .ant-statistic-title {
          margin-bottom: 8px !important;
        }
      `}</style>
    </div>
  );
};

export default AdminSecurity;
