import React, { useState } from 'react';
import { Check, Link2, ShieldCheck, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

type ConnectionState = 'idle' | 'connecting' | 'connected' | 'error';

function normalizeUrl(value: string) {
  return value.trim().replace(/\/$/, '');
}

export const MCPConnector: React.FC = () => {
  const [url, setUrl] = useState('');
  const [token, setToken] = useState('');
  const [state, setState] = useState<ConnectionState>('idle');
  const [message, setMessage] = useState('');

  const connect = async () => {
    const endpointUrl = normalizeUrl(url);
    const serverUrl = endpointUrl.replace(/\/mcp$/, '');
    if (!serverUrl || !token.trim()) {
      setState('error');
      setMessage('Server URL এবং token দুটোই দিন।');
      return;
    }

    setState('connecting');
    setMessage('');
    try {
      const response = await fetch(`${serverUrl}/health/summary`, {
        headers: { Accept: 'application/json', Authorization: `Bearer ${token.trim()}` },
        signal: AbortSignal.timeout(10000),
      });
      if (!response.ok) throw new Error(`Connection failed (${response.status})`);
      setUrl(serverUrl);
      setState('connected');
      setMessage('MCP server connected successfully.');
    } catch (error) {
      setState('error');
      setMessage(error instanceof Error ? error.message : 'MCP server connect করা যায়নি।');
    }
  };

  return (
    <section className="mt-8 flex flex-col gap-5">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-[var(--supremeai-color-brand-primary)]"><Link2 size={16} /><span className="text-xs font-semibold uppercase tracking-[0.18em]">MCP Server</span></div>
        <h2 className="text-2xl font-semibold tracking-tight">Connect your MCP server</h2>
        <p className="max-w-2xl text-sm text-muted-foreground">শুধু server URL এবং token দিন। বাকি authentication নিজে থেকেই হবে।</p>
      </div>

      <Card className="overflow-hidden" title="Add MCP server" icon={<ShieldCheck size={20} />}>
        <div className="flex max-w-2xl flex-col gap-4 px-6 pb-6">
          <label className="flex flex-col gap-2 text-sm font-medium">
            Server URL
            <input value={url} onChange={(event) => { setUrl(event.target.value); setState('idle'); setMessage(''); }} placeholder="https://your-server.example.com/mcp" inputMode="url" className="h-10 rounded-md border bg-background px-3 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-medium">
            Token
            <input type="password" value={token} onChange={(event) => { setToken(event.target.value); setState('idle'); setMessage(''); }} placeholder="Paste your MCP token" autoComplete="off" className="h-10 rounded-md border bg-background px-3 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring" />
          </label>
          <div className="flex items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">Token এই browser session-এর বাইরে সংরক্ষণ করা হয় না।</p>
            <Button state={state === 'connecting' ? 'loading' : 'default'} disabled={!url.trim() || !token.trim() || state === 'connecting'} onClick={() => void connect()}>{state === 'connected' ? <Check size={16} /> : <Link2 size={16} />}{state === 'connected' ? 'Connected' : 'Connect'}</Button>
          </div>
        </div>
      </Card>

      {message && <div role="status" className={`flex items-center justify-between rounded-lg border p-3 text-sm ${state === 'connected' ? 'border-emerald-500/30 bg-emerald-500/5 text-emerald-700' : 'border-destructive/30 bg-destructive/5 text-destructive'}`}><span>{message}</span>{state === 'error' && <button type="button" onClick={() => setMessage('')} aria-label="Dismiss error"><X size={16} /></button>}</div>}
    </section>
  );
};
