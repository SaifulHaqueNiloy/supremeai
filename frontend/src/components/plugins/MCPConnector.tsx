import React, { useState } from 'react';
import { Check, Link2, ShieldCheck, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { formatViewerValue, loadMcpViewerData, normalizeMcpUrl, type McpViewerData } from '../../services/mcpViewer';

type ConnectionState = 'idle' | 'connecting' | 'connected' | 'error';

function DataBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border/60 bg-background/40 p-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-muted-foreground">{formatViewerValue(value)}</pre>
    </div>
  );
}

function ViewerResults({ data }: { data: McpViewerData }) {
  const sections = [
    ['Server', data.server],
    ['Health', data.health],
    ['Dashboard', data.dashboard],
    ['Capabilities', data.capabilities],
    ['Resources', data.resources],
    ['Tools', data.tools],
  ] as const;
  const visibleSections = sections.filter(([, value]) => value !== null && (Array.isArray(value) ? value.length > 0 : Object.keys(value as object).length > 0));

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 text-sm font-medium text-emerald-600"><Check size={16} /> Viewer access connected</div>
      {visibleSections.length ? visibleSections.map(([title, value]) => <DataBlock key={title} title={title} value={value} />) : <p className="text-sm text-muted-foreground">The server connected but returned no viewer data.</p>}
    </div>
  );
}

export const MCPConnector: React.FC = () => {
  const [url, setUrl] = useState('');
  const [token, setToken] = useState('');
  const [state, setState] = useState<ConnectionState>('idle');
  const [message, setMessage] = useState('');
  const [data, setData] = useState<McpViewerData | null>(null);

  const connect = async () => {
    setState('connecting');
    setMessage('');
    setData(null);
    try {
      const normalizedUrl = normalizeMcpUrl(url);
      const viewerData = await loadMcpViewerData(normalizedUrl, token);
      setUrl(normalizedUrl);
      setData(viewerData);
      setState('connected');
    } catch (error) {
      setState('error');
      setMessage(error instanceof Error ? error.message : 'Could not read this MCP server.');
    }
  };

  return (
    <section className="mx-auto mt-8 flex max-w-4xl flex-col gap-5">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-[var(--supremeai-color-brand-primary)]"><Link2 size={16} /><span className="text-xs font-semibold uppercase tracking-[0.18em]">MCP Viewer</span></div>
        <h2 className="text-2xl font-semibold tracking-tight">View an MCP server</h2>
        <p className="max-w-2xl text-sm text-muted-foreground">Share the server URL. The viewer reads only the data exposed by its read-only endpoints.</p>
      </div>

      <Card className="overflow-hidden" title="Connect server" icon={<ShieldCheck size={20} />}>
        <div className="flex flex-col gap-4 px-6 pb-6">
          <label className="flex flex-col gap-2 text-sm font-medium">
            Server URL
            <input value={url} onChange={(event) => { setUrl(event.target.value); setState('idle'); setMessage(''); }} placeholder="https://your-server.example.com/mcp" inputMode="url" className="h-10 rounded-md border bg-background px-3 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring" />
          </label>
          <label className="flex flex-col gap-2 text-sm font-medium">
            Viewer token <span className="font-normal text-muted-foreground">(optional)</span>
            <input type="password" value={token} onChange={(event) => { setToken(event.target.value); setState('idle'); setMessage(''); }} placeholder="Only if the server requires it" autoComplete="off" className="h-10 rounded-md border bg-background px-3 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring" />
          </label>
          <div className="flex items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">The token stays in this browser session and is not saved.</p>
            <Button state={state === 'connecting' ? 'loading' : 'default'} disabled={!url.trim() || state === 'connecting'} onClick={() => void connect()}>{state === 'connected' ? <Check size={16} /> : <Link2 size={16} />}{state === 'connected' ? 'Refresh' : 'Connect'}</Button>
          </div>
        </div>
      </Card>

      {message && <div role="alert" className="flex items-center justify-between rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive"><span>{message}</span><button type="button" onClick={() => setMessage('')} aria-label="Dismiss error"><X size={16} /></button></div>}
      {data && <ViewerResults data={data} />}
    </section>
  );
};
