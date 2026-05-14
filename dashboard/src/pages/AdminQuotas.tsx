import React, { useState, useEffect } from 'react';
import { 
  Typography, Card, Button, message, Input, Select, Space, Tooltip, Breadcrumb
} from 'antd';
import { 
  ReloadOutlined,
  SearchOutlined,
  SortAscendingOutlined,
  SortDescendingOutlined,
  DashboardOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';
import { fetchWithAuth } from '../lib/authUtils';
import AISuggestionInformer from '../components/AISuggestionInformer';
import QuotaStats from '../components/quotas/QuotaStats';
import QuotaTable from '../components/quotas/QuotaTable';
import QuotaWarningsAlert from '../components/quotas/QuotaWarningsAlert';
import { UserQuota, QuotaStatsData } from '../components/quotas/types';

const { Title, Text } = Typography;
const { Option } = Select;

const AdminQuotas: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<UserQuota[]>([]);
  const [warnings, setWarnings] = useState<any[]>([]);
  const [stats, setStats] = useState<QuotaStatsData>({
    totalUsers: 0,
    activeQuotas: 0,
    overLimit: 0
  });

  // Search and Sort State
  const [searchText, setSearchText] = useState('');
  const [sortBy, setSortBy] = useState<keyof UserQuota | 'usagePercent'>('currentUsage');
  const [sortOrder, setSortOrder] = useState<'ascend' | 'descend'>('descend');

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

  const processedUsers = React.useMemo(() => {
    let result = users.filter(user => {
      const searchLower = searchText.toLowerCase();
      return (
        user.displayName?.toLowerCase().includes(searchLower) ||
        user.email?.toLowerCase().includes(searchLower) ||
        user.uid?.toLowerCase().includes(searchLower)
      );
    });

    if (sortBy) {
      result.sort((a, b) => {
        let aVal: any = (a as any)[sortBy];
        let bVal: any = (b as any)[sortBy];

        if (sortBy === 'usagePercent') {
          aVal = (a.currentUsage / a.monthlyQuota);
          bVal = (b.currentUsage / b.monthlyQuota);
        }

        if (typeof aVal === 'string' && typeof bVal === 'string') {
          return sortOrder === 'ascend' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        }
        
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortOrder === 'ascend' ? aVal - bVal : bVal - aVal;
        }

        return 0;
      });
    }

    return result;
  }, [users, searchText, sortBy, sortOrder]);

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
    <div style={{ padding: '24px', background: '#050505', minHeight: '100vh', color: '#fff' }}>
      {/* Header Section */}
      <div style={{ marginBottom: 32 }}>
        <Breadcrumb separator=">" style={{ marginBottom: 16, opacity: 0.7 }}>
          <Breadcrumb.Item href=""><DashboardOutlined /> ড্যাশবোর্ড</Breadcrumb.Item>
          <Breadcrumb.Item><SafetyCertificateOutlined /> রিসোর্স ম্যানেজমেন্ট</Breadcrumb.Item>
          <Breadcrumb.Item>কোটা কন্ট্রোল</Breadcrumb.Item>
        </Breadcrumb>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <Title level={2} style={{ margin: 0, color: '#fff', fontWeight: 800, fontSize: '32px', letterSpacing: '-0.5px' }}>
              কোটা ম্যানেজমেন্ট <span style={{ color: '#3b82f6', fontSize: '14px', fontWeight: 400, verticalAlign: 'middle', marginLeft: '8px', opacity: 0.8 }}>SYSTEM LIMITS</span>
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.45)', fontSize: '16px' }}>
              ইউজারদের রিসোর্স ব্যবহার এবং লিমিটেশন নিয়ন্ত্রণ করুন
            </Text>
          </div>
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={fetchData} 
            loading={loading}
            style={{ 
              height: '42px',
              padding: '0 24px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', 
              border: 'none',
              fontWeight: 600,
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
            }}
          >
            রিফ্রেশ ডাটা
          </Button>
        </div>
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

      <div style={{ margin: '24px 0' }}>
        <QuotaWarningsAlert warningsCount={warnings.length} />
      </div>

      <div style={{ marginBottom: 32 }}>
        <QuotaStats stats={stats} />
      </div>

      {/* Main Content Card */}
      <Card
        className="glass-card main-quota-card"
        style={{ 
          borderRadius: 24, 
          background: 'rgba(255,255,255,0.02)', 
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.3)',
          overflow: 'hidden'
        }}
        bodyStyle={{ padding: 0 }}
      >
        {/* Modern Toolbar */}
        <div className="glass-toolbar" style={{ 
          padding: '20px 24px', 
          background: 'rgba(255, 255, 255, 0.03)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          flexWrap: 'wrap', 
          gap: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ 
              background: 'rgba(59, 130, 246, 0.1)', 
              padding: '8px', 
              borderRadius: '10px',
              border: '1px solid rgba(59, 130, 246, 0.2)'
            }}>
              <SearchOutlined style={{ color: '#3b82f6', fontSize: '18px' }} />
            </div>
            <Input
              placeholder="নাম, ইমেইল বা আইডি দিয়ে খুঁজুন..."
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              variant="borderless"
              style={{ 
                width: 320, 
                height: '42px',
                fontSize: '15px',
                color: '#fff' 
              }}
              className="dark-input-minimal"
            />
          </div>
          
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <div className="toolbar-separator" />
            
            <Space size="middle">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Text style={{ 
                  color: 'rgba(255,255,255,0.35)', 
                  fontSize: '11px', 
                  textTransform: 'uppercase', 
                  letterSpacing: '1px', 
                  fontWeight: 700 
                }}>ফিল্টার</Text>
                <Select
                  value={sortBy}
                  onChange={val => setSortBy(val)}
                  style={{ width: 180 }}
                  className="premium-select"
                  dropdownClassName="premium-dropdown"
                >
                  <Option value="currentUsage">ব্যবহার (প্রকৃত)</Option>
                  <Option value="usagePercent">ব্যবহার (%)</Option>
                  <Option value="monthlyQuota">কোটা লিমিট</Option>
                  <Option value="displayName">ইউজার নাম</Option>
                  <Option value="tier">অ্যাকাউন্ট টিয়ার</Option>
                  <Option value="createdAt">রেজিস্ট্রেশন তারিখ</Option>
                </Select>
              </div>

              <Tooltip title={sortOrder === 'ascend' ? 'ক্রমানুসারে' : 'বিপরীত ক্রমানুসারে'}>
                <Button 
                  onClick={() => setSortOrder(sortOrder === 'ascend' ? 'descend' : 'ascend')}
                  icon={sortOrder === 'ascend' ? <SortAscendingOutlined /> : <SortDescendingOutlined />}
                  style={{ 
                    height: '42px',
                    width: '42px',
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  className="hover-bright"
                />
              </Tooltip>
            </Space>
          </div>
        </div>
        
        <div style={{ padding: '0 1px' }}>
          <QuotaTable 
            users={processedUsers}
            loading={loading}
            onReset={handleReset}
            onTierUpdate={handleTierUpdate}
            onDeactivate={handleDeactivate}
          />
        </div>
      </Card>

      <style>{`
        .glass-card {
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
        
        .main-quota-card .ant-card-body {
          background: linear-gradient(180deg, rgba(255,255,255,0.01) 0%, rgba(255,255,255,0) 100%);
        }

        .dark-input-minimal::placeholder {
          color: rgba(255,255,255,0.2) !important;
        }
        
        .toolbar-separator {
          height: 24px;
          width: 1px;
          background: rgba(255,255,255,0.08);
          margin: 0 8px;
        }

        .premium-select .ant-select-selector {
          background: rgba(255,255,255,0.05) !important;
          border: 1px solid rgba(255,255,255,0.1) !important;
          border-radius: 12px !important;
          height: 42px !important;
          display: flex !important;
          align-items: center !important;
          color: #fff !important;
          transition: all 0.3s ease !important;
        }

        .premium-select:hover .ant-select-selector {
          border-color: rgba(59, 130, 246, 0.5) !important;
          background: rgba(255,255,255,0.08) !important;
        }

        .premium-select .ant-select-selection-item {
          color: #fff !important;
          font-weight: 500 !important;
        }

        .premium-dropdown {
          background: #141414 !important;
          border: 1px solid rgba(255,255,255,0.1) !important;
          border-radius: 12px !important;
          padding: 8px !important;
          box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
        }

        .premium-dropdown .ant-select-item {
          color: rgba(255,255,255,0.65) !important;
          border-radius: 8px !important;
          margin-bottom: 4px !important;
          transition: all 0.2s ease !important;
        }

        .premium-dropdown .ant-select-item-option-selected {
          background: rgba(59, 130, 246, 0.15) !important;
          color: #3b82f6 !important;
        }

        .premium-dropdown .ant-select-item-option-active {
          background: rgba(255,255,255,0.05) !important;
          color: #fff !important;
        }

        .hover-bright:hover {
          background: rgba(255,255,255,0.1) !important;
          border-color: rgba(255,255,255,0.2) !important;
          transform: translateY(-1px);
        }

        /* Table Customizations */
        .admin-table-dark .ant-table {
          background: transparent !important;
        }

        .admin-table-dark .ant-table-thead > tr > th {
          background: rgba(255,255,255,0.02) !important;
          color: rgba(255,255,255,0.4) !important;
          border-bottom: 1px solid rgba(255,255,255,0.05) !important;
          font-size: 12px !important;
          text-transform: uppercase !important;
          letter-spacing: 1px !important;
          font-weight: 700 !important;
          padding: 16px 24px !important;
        }

        .admin-table-dark .ant-table-tbody > tr > td {
          border-bottom: 1px solid rgba(255,255,255,0.03) !important;
          padding: 16px 24px !important;
          color: rgba(255,255,255,0.85) !important;
        }

        .admin-table-dark .ant-table-tbody > tr:hover > td {
          background: rgba(255,255,255,0.02) !important;
        }

        .admin-table-dark .ant-pagination-item {
          background: rgba(255,255,255,0.05) !important;
          border: 1px solid rgba(255,255,255,0.1) !important;
          border-radius: 8px !important;
        }

        .admin-table-dark .ant-pagination-item-active {
          background: #3b82f6 !important;
          border-color: #3b82f6 !important;
        }

        .admin-table-dark .ant-pagination-item a {
          color: rgba(255,255,255,0.65) !important;
        }

        .admin-table-dark .ant-pagination-item-active a {
          color: #fff !important;
        }
      `}</style>
    </div>
  );
};

export default AdminQuotas;

