import React, { useEffect, useMemo, useState } from 'react';
import { Check, ChevronRight, Clipboard, ExternalLink, KeyRound, Link2, RefreshCw, ShieldCheck, Trash2, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { controlPlane, type CreatedExternalClient, type ExternalClient, type ExternalClientProtocol, type ExternalClientRole } from '../../services/controlPlane';

type Step = 1 | 2 | 3;

const roleCopy: Record<ExternalClientRole, { label: string; detail: string }> = {
  viewer: { label: 'Viewer', detail: 'Read-only tools and health details' },
  agent: { label: 'Agent', detail: 'Viewer access plus approved task execution' },
  admin: { label: 'Admin', detail: 'Full control, including permissions and destructive actions' },
};

const protocolLabels: Record<ExternalClientProtocol, string> = {
  'streamable-http': 'Remote MCP (recommended)',
  sse: 'MCP over SSE',
  stdio: 'Local desktop app',
  custom: 'Other MCP client',
};

function formatDate(value?: string) {
  if (!value) return 'Never';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

export const MCPConnector: React.FC = () => {
  const [clients, setClients] = useState<ExternalClient[]>([]);
  const [step, setStep] = useState<Step>(1);
  const [name, setName] = useState('');
  const [provider, setProvider] = useState('');
  const [protocol, setProtocol] = useState<ExternalClientProtocol>('streamable-http');
  const [role, setRole] = useState<ExternalClientRole>('viewer');
  const [newClient, setNewClient] = useState<CreatedExternalClient | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const loadClients = async () => {
    try {
      const result = await controlPlane.listExternalClients();
      setClients(result.clients ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load connections');
    }
  };

  useEffect(() => { void loadClients(); }, []);

  const connectionUrl = useMemo(() => `${import.meta.env.VITE_MCP_CONTROL_PLANE_URL ?? window.location.origin}/mcp`, []);

  const createConnection = async () => {
    setLoading(true);
    setError(null);
    try {
      const created = await controlPlane.createExternalClient({ name: name.trim(), provider: provider.trim() || 'generic', protocol, role });
      setNewClient(created);
      setStep(3);
      await loadClients();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create connection');
    } finally { setLoading(false); }
  };

  const copySetup = async () => {
    if (!newClient) return;
    await navigator.clipboard.writeText(JSON.stringify({ mcp_url: connectionUrl, authorization: `Bearer ${newClient.token}` }, null, 2));
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const rotate = async (id: string) => {
    setLoading(true);
    try {
      const rotated = await controlPlane.rotateExternalClient(id);
      setNewClient(rotated);
      setStep(3);
      await loadClients();
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not rotate token'); }
    finally { setLoading(false); }
  };

  const approve = async (id: string) => {
    setLoading(true);
    try { await controlPlane.approveExternalClient(id); await loadClients(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not approve connection'); }
    finally { setLoading(false); }
  };

  const changeRole = async (id: string, nextRole: ExternalClientRole) => {
    setLoading(true);
    try { await controlPlane.changeExternalClientRole(id, nextRole); await loadClients(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not change role'); }
    finally { setLoading(false); }
  };

  const revoke = async (id: string) => {
    if (!window.confirm('Remove this AI connection? It will lose access immediately.')) return;
    setLoading(true);
    try { await controlPlane.revokeExternalClient(id); await loadClients(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not revoke connection'); }
    finally { setLoading(false); }
  };

  return (
    <section className="mt-8 flex flex-col gap-5">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-[var(--supremeai-color-brand-primary)]"><Link2 size={16} /><span className="text-xs font-semibold uppercase tracking-[0.18em]">Connections</span></div>
        <h2 className="text-2xl font-semibold tracking-tight">Connect any MCP-compatible AI</h2>
        <p className="max-w-2xl text-sm text-muted-foreground">Give Claude, Cursor, ChatGPT-compatible clients, or your own agent a controlled connection without sharing your account credentials.</p>
      </div>

      <Card className="overflow-hidden" title="Add a connection" icon={<ShieldCheck size={20} />}>
        <div className="px-6 pb-6">
          <div className="mb-6 flex items-center gap-2 text-xs text-muted-foreground">
            {[['1', 'Identify'], ['2', 'Permission'], ['3', 'Connect']].map(([number, label], index) => <React.Fragment key={number}><div className={`flex items-center gap-2 ${step >= index + 1 ? 'text-foreground' : ''}`}><span className={`flex size-6 items-center justify-center rounded-full border text-[11px] ${step > index + 1 ? 'border-emerald-500 bg-emerald-500 text-white' : step === index + 1 ? 'border-primary bg-primary text-primary-foreground' : ''}`}>{step > index + 1 ? <Check size={13} /> : number}</span><span>{label}</span></div>{index < 2 && <ChevronRight size={14} />}</React.Fragment>)}
          </div>

          {step === 1 && <div className="grid gap-4 md:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm font-medium">Connection name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="My work AI" className="h-10 rounded-md border bg-background px-3 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring" /></label>
            <label className="flex flex-col gap-2 text-sm font-medium">AI/provider name <span className="font-normal text-muted-foreground">Optional</span><input value={provider} onChange={(event) => setProvider(event.target.value)} placeholder="Claude, Cursor, or Custom AI" className="h-10 rounded-md border bg-background px-3 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring" /></label>
            <label className="flex flex-col gap-2 text-sm font-medium">Connection method<select value={protocol} onChange={(event) => setProtocol(event.target.value as ExternalClientProtocol)} className="h-10 rounded-md border bg-background px-3 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring">{Object.entries(protocolLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            <div className="flex items-end justify-end"><Button disabled={!name.trim()} onClick={() => setStep(2)}>Continue <ChevronRight size={16} /></Button></div>
          </div>}

          {step === 2 && <div className="flex flex-col gap-4">
            <div className="grid gap-3 md:grid-cols-3">{(Object.keys(roleCopy) as ExternalClientRole[]).map((option) => <button type="button" key={option} onClick={() => setRole(option)} className={`rounded-lg border p-4 text-left transition ${role === option ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'hover:bg-muted/60'}`}><div className="mb-1 flex items-center justify-between font-medium">{roleCopy[option].label}{role === option && <Check size={16} />}</div><p className="text-xs leading-relaxed text-muted-foreground">{roleCopy[option].detail}</p></button>)}</div>
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-sm"><strong>Safe default:</strong> Viewer is recommended. You can change or remove this permission anytime from this dashboard.</div>
            <div className="flex justify-between"><Button variant="ghost" onClick={() => setStep(1)}>Back</Button><Button state={loading ? 'loading' : 'default'} onClick={() => void createConnection()}>Create secure connection</Button></div>
          </div>}

          {step === 3 && newClient && <div className="flex flex-col gap-4"><div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4"><div className="mb-1 flex items-center gap-2 font-medium"><Check size={17} /> Awaiting admin approval</div><p className="text-sm text-muted-foreground">The token is shown once. The AI client can connect only after an admin approves this request from the dashboard or Telegram bot.</p></div><pre className="overflow-auto rounded-lg border bg-muted/40 p-4 text-xs leading-relaxed">{JSON.stringify({ mcp_url: connectionUrl, authorization: `Bearer ${newClient.token}` }, null, 2)}</pre><div className="flex justify-between"><Button variant="ghost" onClick={() => { setStep(1); setNewClient(null); setName(''); }}>Done</Button><Button onClick={() => void copySetup()}>{copied ? <Check size={16} /> : <Clipboard size={16} />}{copied ? 'Copied' : 'Copy setup details'}</Button></div></div>}
        </div>
      </Card>

      {error && <div role="alert" className="flex items-center justify-between rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive"><span>{error}</span><button type="button" onClick={() => setError(null)} aria-label="Dismiss error"><X size={16} /></button></div>}

      <Card title="Connected AI clients" icon={<KeyRound size={20} />}>
        <div className="overflow-x-auto px-6 pb-6">{clients.length === 0 ? <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">No AI clients connected yet. New connections start with viewer access.</div> : <div className="flex flex-col gap-2">{clients.map((client) => <div key={client.id} className="grid gap-3 rounded-lg border p-4 md:grid-cols-[1.4fr_0.8fr_0.8fr_1.4fr_auto] md:items-center"><div><div className="font-medium">{client.name}</div><div className="text-xs text-muted-foreground">{client.provider} · {protocolLabels[client.protocol]}</div></div><div className="text-sm"><select aria-label={`Role for ${client.name}`} value={client.role} disabled={loading || client.status === 'revoked' || client.status === 'expired'} onChange={(event) => void changeRole(client.id, event.target.value as ExternalClientRole)} className="rounded-full border bg-background px-2 py-1 text-xs"><option value="viewer">Viewer</option><option value="agent">Agent</option><option value="admin">Admin</option></select></div><div className="text-xs text-muted-foreground">{client.status === 'pending' ? 'Pending approval' : client.status === 'active' ? 'Active' : client.status}</div><div className="text-xs text-muted-foreground">Connected {formatDate(client.createdAt)}<br />Last seen {formatDate(client.lastSeenAt)}</div><div className="flex justify-end gap-2">{client.status === 'pending' && <Button size="sm" disabled={loading} onClick={() => void approve(client.id)}><Check size={14} /> Approve</Button>}<Button variant="secondary" size="sm" disabled={loading || client.status !== 'active'} onClick={() => void rotate(client.id)}><RefreshCw size={14} /> Rotate</Button><Button variant="danger" size="sm" disabled={loading || client.status === 'revoked' || client.status === 'expired'} onClick={() => void revoke(client.id)}><Trash2 size={14} /> Remove</Button></div></div>)}</div>}</div>
      </Card>
    </section>
  );
};
