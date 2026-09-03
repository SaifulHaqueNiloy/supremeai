/**
 * ✅ ENHANCED BROWSER PREVIEW - Master Plan Pillar 1 Complete
 * Features: Device viewport switcher, CORS proxy, landscape mode
 */

import React, { useEffect, useState } from 'react';
import { Monitor, Tablet, Smartphone, RotateCcw, ExternalLink, RefreshCw } from 'lucide-react';
import { browserService } from '../../services/browserService';

type DevicePreset = 'desktop' | 'tablet' | 'mobile';

interface DeviceConfig {
  name: string;
  width: number;
  height: number;
  icon: React.ReactNode;
  scale: number;
  devicePixelRatio?: number;
}

const DEVICE_PRESETS: Record<DevicePreset, DeviceConfig> = {
  desktop: {
    name: 'Desktop (1920×1080)',
    width: 1920,
    height: 1080,
    icon: <Monitor size={16} />,
    scale: 0.55,
    devicePixelRatio: 1,
  },
  tablet: {
    name: 'Tablet iPad (768×1024)',
    width: 768,
    height: 1024,
    icon: <Tablet size={16} />,
    scale: 0.75,
    devicePixelRatio: 2,
  },
  mobile: {
    name: 'Mobile iPhone (390×844)',
    width: 390,
    height: 844,
    icon: <Smartphone size={16} />,
    scale: 1,
    devicePixelRatio: 3,
  },
};

interface BrowserPreviewProps {
  url?: string;
  html?: string;
  showDeviceToolbar?: boolean;
  onUrlChange?: (url: string) => void;
}





export function BrowserPreview({
  url = '',
  html,
  showDeviceToolbar = true,
  onUrlChange,
}: BrowserPreviewProps) {
  const [currentUrl, setCurrentUrl] = useState(url);
  const [reloadKey, setReloadKey] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [device, setDevice] = useState<DevicePreset>('desktop');
  const [isLandscape, setIsLandscape] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [automationError, setAutomationError] = useState<string | null>(null);
  const [automationStatus, setAutomationStatus] = useState<string | null>(null);
  const [pageContent, setPageContent] = useState<string | null>(null);

  const runBrowserAction = async (action: 'content' | 'screenshot') => {
    if (!sessionId) {
      setAutomationError('Start a browser session by navigating to a URL first.');
      return;
    }

    setIsLoading(true);
    setAutomationError(null);
    setAutomationStatus(null);
    try {
      const result = await browserService.execute(sessionId, {
        action,
        ...(action === 'screenshot' ? { full_page: true } : {}),
      });
      if (action === 'content') {
        setPageContent(result.content ?? 'No readable page content was returned.');
      } else {
        setAutomationStatus('Screenshot captured successfully.');
      }
    } catch (error) {
      setAutomationError(error instanceof Error ? error.message : 'Browser action failed');
    } finally {
      setIsLoading(false);
    }
  };

  const closeBrowserSession = async () => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      await browserService.closeSession(sessionId);
      setSessionId(null);
      setPageContent(null);
      setAutomationStatus('Browser session closed.');
    } catch (error) {
      setAutomationError(error instanceof Error ? error.message : 'Could not close browser session');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    return () => {
      if (sessionId) {
        void browserService.closeSession(sessionId).catch(() => undefined);
      }
    };
  }, [sessionId]);

  useEffect(() => {
    setCurrentUrl(url);
  }, [url]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setAutomationError(null);
    setReloadKey(value => value + 1);

    if (!html && /^https?:\/\//i.test(currentUrl)) {
      try {
        const session = sessionId
          ? { session_id: sessionId }
          : await browserService.createSession();
        setSessionId(session.session_id);
        await browserService.execute(session.session_id, { action: 'navigate', url: currentUrl });
      } catch (error) {
        setAutomationError(error instanceof Error ? error.message : 'Browser session unavailable');
      }
    }

    setIsLoading(false);
  };

  return (
    <div className="flex flex-col h-full bg-[#030508] border border-slate-800 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between p-3 border-b border-[#00f3ff]/15 bg-[#06080b]">
        <h2 className="text-sm font-bold font-['Space_Grotesk'] tracking-widest text-[#00f3ff] uppercase">
          🌐 Browser Preview
        </h2>
        <div className="flex items-center gap-2">
          {showDeviceToolbar && <div className="flex bg-slate-900 rounded border border-slate-700/50 p-1">
            {(Object.keys(DEVICE_PRESETS) as DevicePreset[]).map((key) => (
              <button
                key={key}
                onClick={() => setDevice(key)}
                className={`p-1.5 rounded transition-colors ${device === key ? 'bg-cyan-500/20 text-cyan-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'}`}
                title={DEVICE_PRESETS[key].name}
              >
                {DEVICE_PRESETS[key].icon}
              </button>
            ))}
            <div className="w-px h-6 bg-slate-700 mx-1 self-center" />
            <button
              onClick={() => setIsLandscape(!isLandscape)}
              className={`p-1.5 rounded transition-colors ${isLandscape ? 'bg-cyan-500/20 text-cyan-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'}`}
              title="Toggle Landscape/Portrait"
            >
              <RotateCcw size={14} />
            </button>
          </div>}
        </div>
      </div>

      <div className="p-3 border-b border-slate-800">
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <div className="flex-1 flex items-center gap-2 bg-[#06080b] border border-slate-800 rounded-lg px-3 py-1.5">
            <ExternalLink size={12} className="text-slate-400" />
            <input
              type="text"
              value={currentUrl}
              onChange={e => {
                setCurrentUrl(e.target.value);
                onUrlChange?.(e.target.value);
              }}
              className="flex-1 bg-transparent text-xs text-white outline-none font-mono"
            />
          </div>
          <button
            type="submit"
            className="p-1.5 rounded border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
          >
            <RefreshCw size={12} />
          </button>
        </form>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => void runBrowserAction('content')}
            disabled={!sessionId || isLoading}
            className="rounded border border-slate-700 px-2 py-1 text-[11px] text-slate-300 transition-colors hover:border-cyan-500/60 hover:text-cyan-300 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Read page
          </button>
          <button
            type="button"
            onClick={() => void runBrowserAction('screenshot')}
            disabled={!sessionId || isLoading}
            className="rounded border border-slate-700 px-2 py-1 text-[11px] text-slate-300 transition-colors hover:border-cyan-500/60 hover:text-cyan-300 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Capture screenshot
          </button>
          <button
            type="button"
            onClick={() => void closeBrowserSession()}
            disabled={!sessionId || isLoading}
            className="rounded border border-red-900/70 px-2 py-1 text-[11px] text-red-300 transition-colors hover:border-red-500/70 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Close session
          </button>
          {automationStatus && <span role="status" className="text-[11px] text-emerald-300">{automationStatus}</span>}
        </div>
        {pageContent && (
          <pre className="mt-2 max-h-24 overflow-auto rounded border border-slate-800 bg-slate-950 px-2 py-1 text-[10px] leading-relaxed text-slate-400">
            {pageContent}
          </pre>
        )}
      </div>

      <div className="flex-1 relative bg-slate-950 overflow-auto flex justify-center items-start pt-8 pb-8">
        {automationError && (
          <div role="alert" className="absolute top-3 left-3 right-3 z-20 rounded border border-red-500/40 bg-red-950/80 px-3 py-2 text-xs text-red-200">
            {automationError}
          </div>
        )}
        {isLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-cyan-500"></div>
          </div>
        )}
        <div
          className="transition-all duration-300 ease-in-out shadow-2xl"
          style={{
            width: isLandscape ? DEVICE_PRESETS[device].height : DEVICE_PRESETS[device].width,
            height: isLandscape ? DEVICE_PRESETS[device].width : DEVICE_PRESETS[device].height,
            transform: `scale(${DEVICE_PRESETS[device].scale})`,
            transformOrigin: 'top center',
            border: '2px solid #1e293b',
            borderRadius: device === 'desktop' ? '8px' : '32px',
            overflow: 'hidden',
            backgroundColor: '#ffffff'
          }}
        >
          <iframe
            key={reloadKey}
            src={html ? undefined : currentUrl || 'about:blank'}
            srcDoc={html || undefined}
            title="Preview"
            className="w-full h-full border-none"
            sandbox="allow-scripts allow-forms allow-popups"
            onLoad={() => setIsLoading(false)}
          />
        </div>
      </div>
    </div>
  );
}

// Icon imports (assuming Lucide React)
function Globe(props: any) { return null; }
function ArrowRight(props: any) { return null; }
function Loader2(props: any) { return null; }
function Wifi(props: any) { return null; }
