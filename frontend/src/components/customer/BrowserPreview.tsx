import { useState } from 'react';
import { Card } from '../ui';
import { RefreshCw, ExternalLink } from 'lucide-react';
import { getApiBaseUrl } from '../../utils/api';
import { getRawToken } from '../../services/apiClient';

interface BrowserPreviewProps {
  url?: string;
  html?: string;
}

function proxied(src: string): string {
  // Route external URLs through the backend proxy so sites that block iframes (X-Frame-Options)
  // still render inside the preview. Token is appended so AuthMiddleware accepts the iframe request.
  if (/^https?:\/\//i.test(src)) {
    return `${getApiBaseUrl()}/api/browser/render?url=${encodeURIComponent(src)}&token=${encodeURIComponent(getRawToken() || '')}`;
  }
  return src;
}

export function BrowserPreview({ url = 'https://supremeai.web.app', html }: BrowserPreviewProps) {
  const [currentUrl, setCurrentUrl] = useState(url);
  const [reloadKey, setReloadKey] = useState(0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setReloadKey(k => k + 1);
  };

  const iframeSrc = html ? undefined : proxied(currentUrl);
  const sandbox = html ? 'allow-scripts allow-forms allow-same-origin' : 'allow-scripts allow-forms allow-popups';

  return (
    <div className="flex-grow p-6 overflow-y-auto bg-[#030508]">
      <div className="flex items-center justify-between mb-6 pb-2 border-b border-[#00f3ff]/15">
        <h2 className="text-lg font-bold font-['Space_Grotesk'] tracking-widest text-[#00f3ff] uppercase">
          🌐 Browser Preview
        </h2>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="flex items-center gap-2 mb-4">
          <div className="flex-1 flex items-center gap-2 bg-[#06080b] border border-slate-800 rounded-lg px-3 py-1.5">
            <ExternalLink size={12} className="text-slate-400" />
            <input
              type="text"
              value={currentUrl}
              onChange={e => setCurrentUrl(e.target.value)}
              placeholder="https://example.com"
              className="flex-1 bg-transparent text-xs text-white outline-none font-mono"
            />
          </div>
          <button
            type="submit"
            className="p-1.5 rounded border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
            aria-label="Reload preview"
          >
            <RefreshCw size={12} className={reloadKey ? 'animate-spin' : ''} />
          </button>
        </form>

        <div className="border border-slate-800 rounded-lg overflow-hidden bg-white">
          <iframe
            key={reloadKey}
            src={iframeSrc}
            srcDoc={html}
            title="Preview"
            className="w-full h-[60vh]"
            sandbox={sandbox}
          />
        </div>
      </Card>
    </div>
  );
}
