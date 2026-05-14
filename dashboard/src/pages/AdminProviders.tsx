import React, { useState, useEffect } from 'react';
import { Card, message, Spin, Alert } from 'antd';
import AdminLayout from '../components/AdminLayout';
import { authUtils } from '../lib/authUtils';
import AISuggestionInformer from '../components/AISuggestionInformer';
import { useRole } from '../contexts/RoleContext';

// Modular Components
import { Provider, ProviderHealthStats as StatsType } from '../components/providers/types';
import ProviderHealthStats from '../components/providers/ProviderHealthStats';
import ProvidersTable from '../components/providers/ProvidersTable';
import ProviderModal from '../components/providers/ProviderModal';
import ProviderActionToolbar from '../components/providers/ProviderActionToolbar';

const AdminProviders: React.FC = () => {
  const { isGuest } = useRole();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null);
  const [healthStats, setHealthStats] = useState<StatsType | null>(null);
  const [testingAll, setTestingAll] = useState(false);

  const fetchProviders = async () => {
    setLoading(true);
    setError(null);
    try {
      const [provRes, statsRes] = await Promise.all([
        authUtils.fetchWithAuth('/api/admin/providers/configured'),
        authUtils.fetchWithAuth('/api/admin/providers/health-stats')
      ]);

      if (!provRes.ok) throw new Error('Failed to fetch providers');
      const result = await provRes.json();
      const rawData = result.data?.providers || (Array.isArray(result.data) ? result.data : []);
      
      const provList: Provider[] = rawData.map((p: any) => ({
        ...p,
        models: Array.isArray(p.models) ? p.models : [],
        status: p.status || 'inactive',
        type: p.type || 'unknown'
      }));
      
      setProviders(provList);

      if (statsRes.ok) {
        const stats = await statsRes.json();
        setHealthStats(stats.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  const handleTestAll = async () => {
    if (isGuest) return;
    setTestingAll(true);
    try {
      const response = await authUtils.fetchWithAuth('/api/admin/providers/test-all', { method: 'POST' });
      if (response.ok) {
        const result = await response.json();
        message.success(result.data.message);
        setTimeout(fetchProviders, 5000); // Refresh after some time
      }
    } catch (err) {
      message.error('Validation test failed');
    } finally {
      setTestingAll(false);
    }
  };

  const handleRemoveDead = async () => {
    if (isGuest) return;
    try {
      const response = await authUtils.fetchWithAuth('/api/admin/providers/bulk-remove-dead', { method: 'DELETE' });
      if (response.ok) {
        message.success('সব ডেড কী রিমুভ করা হয়েছে');
        fetchProviders();
      }
    } catch (err) {
      message.error('Failed to remove dead keys');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const payload: Provider = {
        ...values,
        status: values.status || 'active',
        models: values.models ? values.models.split(',').map((m: string) => m.trim()) : [],
      };
      let response;
      if (editingProvider && editingProvider.id) {
        response = await authUtils.fetchWithAuth(`/api/admin/providers/${editingProvider.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      } else {
        response = await authUtils.fetchWithAuth('/api/admin/providers/add', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || err.message || 'Failed to save provider');
      }
      message.success('Provider saved successfully');
      setModalVisible(false);
      fetchProviders();
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Operation failed');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const response = await authUtils.fetchWithAuth(`/api/admin/providers/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete provider');
      message.success('Provider deleted');
      fetchProviders();
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

  return (
    <AdminLayout title="AI Provider Management">
      <AISuggestionInformer 
        title="AI Architecture Optimizations"
        context="Provider Orchestration"
        suggestions={[
          {
            id: 'add-deepseek',
            title: 'Enable DeepSeek V4-Pro',
            description: 'Detected complex coding tasks taking longer with current models. Suggesting integration of DeepSeek V4-Pro for 35% better code generation performance.',
            impact: 'capability',
            confidence: 0.95,
            autoExecutable: false
          },
          {
            id: 'failover-config',
            title: 'Dynamic Failover detected',
            description: 'Anthropic API is experiencing high latency (2500ms+). Suggesting automatic rerouting to GPT-4o-mini for non-critical chat tasks to maintain responsiveness.',
            impact: 'performance',
            confidence: 0.91,
            autoExecutable: true
          }
        ]}
        onApprove={(id) => message.success(`Executing provider optimization: ${id}`)}
        onDecline={(id) => message.info(`Optimization ${id} skipped.`)}
      />

      <ProviderHealthStats stats={healthStats} />

      <Card>
        <ProviderActionToolbar 
          loading={loading}
          testingAll={testingAll}
          deadCount={healthStats?.dead || 0}
          onAdd={() => {
            setEditingProvider(null);
            setModalVisible(true);
          }}
          onRefresh={fetchProviders}
          onTestAll={handleTestAll}
          onRemoveDead={handleRemoveDead}
        />

        {loading && <Spin style={{ display: 'block', margin: '20px auto' }} />}
        {error && <Alert type="error" message={error} action={<Button onClick={fetchProviders}>Retry</Button>} />}

        {!loading && !error && (
          <ProvidersTable 
            providers={providers}
            loading={loading}
            onEdit={(record) => {
              setEditingProvider(record);
              setModalVisible(true);
            }}
            onDelete={handleDelete}
          />
        )}
      </Card>

      <ProviderModal 
        visible={modalVisible}
        editingProvider={editingProvider}
        onCancel={() => setModalVisible(false)}
        onSubmit={handleSubmit}
      />
    </AdminLayout>
  );
};

export default AdminProviders;
