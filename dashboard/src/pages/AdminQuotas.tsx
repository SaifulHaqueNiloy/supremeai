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
    <div className="admin-page">
      {/* Header Section */}
      <div className="admin-header">
        <Breadcrumb separator=">" style={{ marginBottom: 'var(--space-2)', opacity: 0.7 }}>
          <Breadcrumb.Item href=""><DashboardOutlined /> ড্যাশবোর্ড</Breadcrumb.Item>
          <Breadcrumb.Item><SafetyCertificateOutlined /> রিসোর্স ম্যানেজমেন্ট</Breadcrumb.Item>
          <Breadcrumb.Item>কোটা কন্ট্রোল</Breadcrumb.Item>
        </Breadcrumb>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
          <div>
            <Title level={2} className="admin-title">
              কোটা ম্যানেজমেন্ট <span className="admin-badge">SYSTEM LIMITS</span>
            </Title>
            <Text className="admin-subtitle">
              ইউজারদের রিসোর্স ব্যবহার এবং লিমিটেশন নিয়ন্ত্রণ করুন
            </Text>
          </div>
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={fetchData}
            loading={loading}
            className="admin-btn-primary"
            style={{ 
              background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              border: 'none',
              fontWeight: 600,
              boxShadow: '0 4px clamp(12px, 2vw, 20px) rgba(59, 130, 246, 0.3)'
            }}
          >
            রিফ্রেশ ডাটা
          </Button>
        </div>
      </div>

      <QuotaWarningsAlert warnings={warnings} />

      <div className="admin-toolbar">
        <div className="toolbar-section">
          <div style={{ 
            background: 'rgba(59, 130, 246, 0.1)', 
            padding: 'var(--space-2)', 
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            display: 'flex',
            alignItems: 'center'
          }}>
            <SearchOutlined style={{ color: '#3b82f6', fontSize: 'var(--text-base)' }} />
          </div>
          <Input
            placeholder="ইউজার ইমেইল বা নাম দিয়ে খুঁজুন..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            variant="borderless"
            className="admin-search dark-input-minimal"
          />
        </div>
        
        <div className="toolbar-section">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Text style={{ 
              color: 'rgba(255,255,255,0.35)', 
              fontSize: 'var(--text-xs)', 
              textTransform: 'uppercase', 
              letterSpacing: '1px', 
              fontWeight: 700 
            }}>সর্ট</Text>
            <Select
              value={sortBy}
              onChange={(val) => setSortBy(val)}
              style={{ width: clamp(140px, 14vw, 180px) }}
              className="premium-select"
              dropdownClassName="premium-dropdown"
            >
              <Option value="currentUsage">ব্যবহার</Option>
              <Option value="monthlyQuota">কোটা</Option>
              <Option value="displayName">নাম</Option>
              <Option value="tier">টিয়ার</Option>
            </Select>
          </div>

          <Tooltip title={sortOrder === 'ascend' ? 'ক্রমানুসারে' : 'বিপরীত ক্রমানুসারে'}>
            <Button 
              onClick={() => setSortOrder(sortOrder === 'ascend' ? 'descend' : 'ascend')}
              icon={sortOrder === 'ascend' ? <SortAscendingOutlined /> : <SortDescendingOutlined />}
              className="admin-btn-icon"
              style={{ 
                borderRadius: 'var(--radius-md)',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#fff'
              }}
            />
          </Tooltip>
        </div>
      </div>

      <QuotaStats stats={stats} loading={loading} />

      <Card
        className="glass-card"
        style={{ 
          borderRadius: 'var(--radius-xl)', 
          background: 'rgba(255,255,255,0.02)', 
          border: '1px solid rgba(255,255,255,0.08)',
          marginBottom: 'var(--space-4)',
          overflow: 'hidden'
        }}
        bodyStyle={{ padding: 0 }}
      >
        <div style={{ overflowX: 'auto' }}>
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

