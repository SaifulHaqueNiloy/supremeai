// বাংলা মন্তব্য: Devin-স্টাইল সেটিংস পেজ — ব্যাকএন্ড /preferences/ এপিআই দিয়ে ইউজার প্রেফারেন্স লোড/সেভ করা হয়
import { useState, useEffect } from 'react';
import { Save, Loader2, Shield, Trash2 } from 'lucide-react';
import { apiClient } from '../../services/apiClient';
// বাংলা মন্তব্য: বাহিরের মডেল নামের বদলে SupremeAI ব্র্যান্ডেড নাম + ক্যানোনিক্যাল মডেল লিস্ট
import { getSupremeModelLabel, SUPREME_AVAILABLE_MODELS } from '../../lib/modelBranding';

interface Preferences {
  theme: string;
  default_model: string;
  max_tokens: number;
  auto_save: boolean;
  verbosity: string;
}

const DEFAULT_PREFS: Preferences = {
  theme: 'dark',
  default_model: 'gpt-4o',
  max_tokens: 4096,
  auto_save: true,
  verbosity: 'normal',
};

const MODELS = SUPREME_AVAILABLE_MODELS;

interface SettingsPageProps {
  theme: 'dark' | 'light';
  toggleTheme: () => void;
}

export function SettingsPage({ theme, toggleTheme }: SettingsPageProps) {
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [trustedBrowsers, setTrustedBrowsers] = useState<Array<{ id: string; created_at: number }>>([]);
  const [trustedBrowserStatus, setTrustedBrowserStatus] = useState('');

  useEffect(() => {
    apiClient
      .get<Partial<Preferences>>('/api/preferences/?user_id=default')
      .then((data) => setPrefs({ ...DEFAULT_PREFS, ...data }))
      .catch(() => setStatus('Failed to load preferences — using defaults.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    apiClient.get<{ browsers: Array<{ id: string; created_at: number }> }>('/api/admin/trusted-browsers')
      .then((data) => setTrustedBrowsers(data.browsers || []))
      .catch(() => setTrustedBrowsers([]));
  }, []);

  const revokeBrowser = async (id: string) => {
    setTrustedBrowserStatus('Revoking...');
    try {
      await apiClient.delete(`/api/admin/trusted-browsers/${encodeURIComponent(id)}`);
      setTrustedBrowsers((items) => items.filter((item) => item.id !== id));
      setTrustedBrowserStatus('Browser revoked.');
    } catch (error) {
      setTrustedBrowserStatus(error instanceof Error ? error.message : 'Unable to revoke browser.');
    }
  };

  const revokeAllBrowsers = async () => {
    setTrustedBrowserStatus('Revoking all...');
    try {
      await apiClient.delete('/api/admin/trusted-browsers');
      setTrustedBrowsers([]);
      setTrustedBrowserStatus('All trusted browsers revoked.');
    } catch (error) {
      setTrustedBrowserStatus(error instanceof Error ? error.message : 'Unable to revoke browsers.');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setStatus('');
    try {
      await apiClient.post('/api/preferences/?user_id=default', {
        theme: prefs.theme,
        default_model: prefs.default_model,
        max_tokens: prefs.max_tokens,
        auto_save: prefs.auto_save,
        verbosity: prefs.verbosity,
      });
      setStatus('Preferences saved.');
    } catch (error) {
      setStatus(`Save failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
      setTimeout(() => setStatus(''), 3000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        <Loader2 size={20} className="animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <h1 className="text-lg font-semibold text-white mb-1">Settings</h1>
      <p className="text-xs text-slate-400 mb-6">Manage your workspace preferences.</p>

      <div className="flex flex-col gap-5">
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
          <h2 className="text-sm font-medium text-white mb-3">Appearance</h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-300">Theme</p>
              <p className="text-[11px] text-slate-400">Switch between light and dark mode.</p>
            </div>
            <button
              data-testid="settings-theme-toggle"
              onClick={() => {
                toggleTheme();
                setPrefs((p) => ({ ...p, theme: theme === 'dark' ? 'light' : 'dark' }));
              }}
              className="px-3 py-1.5 rounded-lg border border-white/10 text-xs text-slate-200 hover:bg-white/[0.05] transition-colors"
            >
              {theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5 flex flex-col gap-4">
          <h2 className="text-sm font-medium text-white">AI Model</h2>
          <div>
            <label className="block text-xs text-slate-300 mb-1" htmlFor="default-model">
              Default model
            </label>
            <select
              id="default-model"
              value={prefs.default_model}
              onChange={(e) => setPrefs((p) => ({ ...p, default_model: e.target.value }))}
              className="w-full rounded-lg bg-black/30 border border-white/10 px-3 py-2 text-xs text-white outline-none focus:border-blue-500/50"
            >
              {MODELS.map((m) => (
                <option key={m} value={m}>
                  {getSupremeModelLabel(m)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-300 mb-1" htmlFor="max-tokens">
              Max tokens per response
            </label>
            <input
              id="max-tokens"
              type="number"
              min={256}
              max={128000}
              value={prefs.max_tokens}
              onChange={(e) => setPrefs((p) => ({ ...p, max_tokens: Number(e.target.value) }))}
              className="w-full rounded-lg bg-black/30 border border-white/10 px-3 py-2 text-xs text-white outline-none focus:border-blue-500/50"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-300 mb-1" htmlFor="verbosity">
              Response verbosity
            </label>
            <select
              id="verbosity"
              value={prefs.verbosity}
              onChange={(e) => setPrefs((p) => ({ ...p, verbosity: e.target.value }))}
              className="w-full rounded-lg bg-black/30 border border-white/10 px-3 py-2 text-xs text-white outline-none focus:border-blue-500/50"
            >
              <option value="concise">Concise</option>
              <option value="normal">Normal</option>
              <option value="detailed">Detailed</option>
            </select>
          </div>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
          <h2 className="text-sm font-medium text-white mb-3">Workspace</h2>
          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <p className="text-xs text-slate-300">Auto-save</p>
              <p className="text-[11px] text-slate-400">Automatically save workspace changes.</p>
            </div>
            <input
              type="checkbox"
              checked={prefs.auto_save}
              onChange={(e) => setPrefs((p) => ({ ...p, auto_save: e.target.checked }))}
              className="w-4 h-4 accent-blue-600"
            />
          </label>
        </div>

        <div className="rounded-xl border border-amber-400/20 bg-amber-400/[0.04] p-5">
          <div className="flex items-start justify-between gap-4 mb-3">
            <div className="flex items-start gap-2">
              <Shield size={16} className="text-amber-300 mt-0.5" />
              <div>
                <h2 className="text-sm font-medium text-white">Authorized browsers</h2>
                <p className="text-[11px] text-slate-400">Admin browsers trusted for seven days without another TOTP prompt.</p>
              </div>
            </div>
            {trustedBrowsers.length > 0 && <button onClick={revokeAllBrowsers} className="text-[11px] text-red-300 hover:text-red-200">Revoke all</button>}
          </div>
          {trustedBrowsers.length === 0 ? (
            <p className="text-xs text-slate-500">No trusted browsers found, or this account is not an admin.</p>
          ) : (
            <div className="space-y-2">
              {trustedBrowsers.map((browser) => (
                <div key={browser.id} className="flex items-center justify-between rounded-lg border border-white/10 px-3 py-2">
                  <span className="text-xs text-slate-300">Browser authorized {new Date(browser.created_at * 1000).toLocaleDateString()}</span>
                  <button aria-label="Revoke browser" onClick={() => revokeBrowser(browser.id)} className="text-slate-400 hover:text-red-300"><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          )}
          {trustedBrowserStatus && <p className="text-[11px] text-slate-400 mt-3">{trustedBrowserStatus}</p>}
        </div>

        <div className="flex items-center gap-3">
          <button
            data-testid="settings-save-btn"
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white text-xs font-medium transition-colors"
          >
            {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
            Save preferences
          </button>
          {status && <span className="text-xs text-slate-400">{status}</span>}
        </div>
      </div>
    </div>
  );
}
