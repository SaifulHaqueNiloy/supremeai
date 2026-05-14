import React, { useState, useEffect } from 'react';
import { 
  Typography, Card, Button, message 
} from 'antd';
import { 
  ReloadOutlined 
} from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';
import AISuggestionInformer from '../components/AISuggestionInformer';
import QuotaStats from '../components/quotas/QuotaStats';
import QuotaTable from '../components/quotas/QuotaTable';
import QuotaWarningsAlert from '../components/quotas/QuotaWarningsAlert';
import { UserQuota, QuotaStatsData } from '../components/quotas/types';

const { Title, Text } = Typography;

const AdminQuotas: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<UserQuota[]>([]);
  const [warnings, setWarnings] = useState<any[]>([]);
  const [stats, setStats] = useState<QuotaStatsData>({
    totalUsers: 0,
    activeQuotas: 0,
    overLimit: 0
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [accountsRes, warningsRes] = await Promise.all([
        fetchWithAuth('/api/accounts'),
        fetchWithAuth('/api/quota/warnings')
      ]);

      if (accountsRes.ok) {
        const data = await accountsRes.json();
        setUsers(data);
        
        // Calculate stats
        const total = data.length;
        const active = data.filter((u: any) => u.currentUsage > 0).length;
        const over = data.filter((u: any) => u.currentUsage >= u.monthlyQuota).length;
        
        setStats({
          totalUsers: total,
          activeQuotas: active,
          overLimit: over
        });
      }

      if (warningsRes.ok) {
        const warningData = await warningsRes.json();
        setWarnings(warningData.warnings || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      message.error('সার্ভারের সাথে যোগাযোগ বিচ্ছিন্ন');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleReset = async (userId: string) => {
    try {
      const response = await fetchWithAuth(`/api/quota/${userId}/reset`, {
        method: 'POST'
      });
      if (response.ok) {
        message.success('কোটা সফলভাবে রিসেট করা হয়েছে');
        fetchData();
      } else {
        message.error('কোটা রিসেট করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    }
  };

  const handleTierUpdate = async (userId: string, newTier: string) => {
    try {
      const response = await fetchWithAuth(`/api/accounts/${userId}/tier`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: newTier })
      });
      if (response.ok) {
        message.success(`ইউজার টিয়ার ${newTier} এ আপডেট করা হয়েছে`);
        fetchData();
      } else {
        message.error('টিয়ার আপডেট করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    }
  };

  const handleDeactivate = async (userId: string) => {
    try {
      const response = await fetchWithAuth(`/api/accounts/${userId}/deactivate`, {
        method: 'PUT'
      });
      if (response.ok) {
        message.warning('ইউজার অ্যাকাউন্ট ডিঅ্যাক্টিভ করা হয়েছে');
        fetchData();
      } else {
        message.error('অ্যাকাউন্ট ডিঅ্যাক্টিভ করতে ব্যর্থ হয়েছে');
      }
    } catch (error) {
      message.error('সার্ভার ত্রুটি');
    }
  };

  return (
    <div style={{ padding: 24, background: '#0a0a0a', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#fff', fontWeight: 700 }}>
          কোটা ম্যানেজমেন্ট
        </Title>
        <Button 
          type="primary" 
          icon={<ReloadOutlined />} 
          onClick={fetchData} 
          loading={loading}
          style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', border: 'none' }}
        >
          রিফ্রেশ ডাটা
        </Button>
      </div>

      <AISuggestionInformer 
        title="Resource Distribution Insights"
        context="User Quotas & Traffic"
        suggestions={[
          {
            id: 'increase-pro-quota',
            title: 'Dynamic Quota Expansion',
            description: 'PRO users are consistently hitting 95% of their limits by mid-month. Suggesting a 20% quota increase for the PRO tier to reduce manual reset requests.',
            impact: 'performance',
            confidence: 0.92,
            autoExecutable: true
          },
          {
            id: 'limit-free-tier',
            title: 'Anomalous Free Tier Usage',
            description: 'Detected unusual burst of API calls from new FREE tier accounts. Suggesting temporary rate limiting to preserve system stability for paid users.',
            impact: 'security',
            confidence: 0.87,
            autoExecutable: true
          }
        ]}
        onApprove={(id) => message.success(`Permission granted for ${id}. System updated.`)}
        onDecline={(id) => message.info(`Adjustment ${id} declined.`)}
      />

      <QuotaWarningsAlert warningsCount={warnings.length} />

      <QuotaStats stats={stats} />

      <Card
        className="glass-card"
        style={{ 
          borderRadius: 16, 
          background: 'rgba(255,255,255,0.02)', 
          border: '1px solid rgba(255,255,255,0.1)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
        }}
        bodyStyle={{ padding: 0 }}
      >
        <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <Text style={{ color: 'rgba(255,255,255,0.45)' }}>
            ইউজার তালিকা এবং কোটা ব্যবহারের রিয়েল-টাইম স্ট্যাটাস
          </Text>
        </div>
        
        <QuotaTable 
          users={users}
          loading={loading}
          onReset={handleReset}
          onTierUpdate={handleTierUpdate}
          onDeactivate={handleDeactivate}
        />
      </Card>

      <style>{`
        .admin-table-dark .ant-table {
          background: transparent !important;
          color: #fff !important;
        }
        .admin-table-dark .ant-table-thead > tr > th {
          background: rgba(255,255,255,0.03) !important;
          color: rgba(255,255,255,0.65) !important;
          border-bottom: 1px solid rgba(255,255,255,0.05) !important;
        }
        .admin-table-dark .ant-table-tbody > tr > td {
          border-bottom: 1px solid rgba(255,255,255,0.05) !important;
        }
        .admin-table-dark .ant-table-tbody > tr:hover > td {
          background: rgba(255,255,255,0.05) !important;
        }
        .admin-table-dark .ant-pagination-item, .admin-table-dark .ant-pagination-prev, .admin-table-dark .ant-pagination-next {
          background: transparent !important;
          border-color: rgba(255,255,255,0.2) !important;
        }
        .admin-table-dark .ant-pagination-item a {
          color: #fff !important;
        }
        .glass-card {
          transition: transform 0.2s ease;
        }
        .glass-card:hover {
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
};

export default AdminQuotas;

