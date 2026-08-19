import React, { useState, useEffect, useRef } from 'react';
import {
  Globe,
  Play,
  Square,
  Pause,
  RefreshCw,
  ExternalLink,
  Shield,
  Hand,
  MousePointer,
  FileCode,
  Terminal,
  Laptop,
  Smartphone,
  Monitor,
  CheckCircle2,
  AlertTriangle,
  Zap,
  ArrowRight,
  Layers,
  Camera
} from 'lucide-react';
import { getApiBaseUrl } from '../../utils/api';
import { getRawToken } from '../../services/apiClient';

interface BrowserActionLog {
  id: string;
  timestamp: string;
  action: 'navigate' | 'click' | 'fill' | 'extract' | 'takeover' | 'thought';
  target?: string;
  details: string;
  status: 'pending' | 'success' | 'failed';
}

function getProxiedUrl(targetUrl: string): string {
  if (/^https?:\/\//i.test(targetUrl)) {
    const baseUrl = getApiBaseUrl();
    const token = getRawToken() || '';
    return `${baseUrl}/api/browser/render?url=${encodeURIComponent(targetUrl)}&token=${encodeURIComponent(token)}`;
  }
  return targetUrl;
}

export const LiveBrowserStudio: React.FC = () => {
  const [currentUrl, setCurrentUrl] = useState<string>('https://news.ycombinator.com');
  const [inputUrl, setInputUrl] = useState<string>('https://news.ycombinator.com');
  const [agentGoal, setAgentGoal] = useState<string>('Scrape top 5 trending tech articles and extract their title & link');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isTakeoverActive, setIsTakeoverActive] = useState<boolean>(false);
  const [viewportMode, setViewportMode] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [reloadCounter, setReloadCounter] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<'stream' | 'findings' | 'logs'>('stream');

  const [logs, setLogs] = useState<BrowserActionLog[]>([
    {
      id: '1',
      timestamp: new Date().toLocaleTimeString(),
      action: 'thought',
      details: 'Agent initialized. Ready to execute browser automation goals.',
      status: 'success'
    }
  ]);

  const [findings, setFindings] = useState<Array<{ title: string; url: string; score?: string }>>([
    { title: 'Show HN: SupremeAI Self-Evolving Engine', url: 'https://news.ycombinator.com/item?id=1', score: '342 points' },
    { title: 'Why Decentralized Compute Beats Closed SaaS', url: 'https://news.ycombinator.com/item?id=2', score: '219 points' }
  ]);

  const iframeRef = useRef<HTMLIFrameElement>(null);

  const handleNavigate = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    let formatted = inputUrl.trim();
    if (!/^https?:\/\//i.test(formatted)) {
      formatted = `https://${formatted}`;
    }
    setCurrentUrl(formatted);
    setInputUrl(formatted);
    setReloadCounter(prev => prev + 1);

    addLog('navigate', formatted, `Navigated to ${formatted}`);
  };

  const addLog = (action: BrowserActionLog['action'], target: string | undefined, details: string) => {
    const newLog: BrowserActionLog = {
      id: Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toLocaleTimeString(),
      action,
      target,
      details,
      status: 'success'
    };
    setLogs(prev => [newLog, ...prev]);
  };

  const handleStartGoal = async () => {
    if (!agentGoal.trim()) return;
    setIsRunning(true);
    addLog('thought', undefined, `Goal initiated: "${agentGoal}"`);

    // Simulated autonomous agent step progression
    setTimeout(() => {
      addLog('navigate', currentUrl, `Analyzing DOM structure of ${currentUrl}`);
    }, 800);

    setTimeout(() => {
      addLog('click', 'a.storylink', 'Clicked first top trending item');
    }, 1800);

    setTimeout(() => {
      addLog('extract', 'data-table', 'Extracted 5 top articles into findings registry');
      setIsRunning(false);
    }, 3200);
  };

  const handleToggleTakeover = () => {
    const nextState = !isTakeoverActive;
    setIsTakeoverActive(nextState);
    if (nextState) {
      addLog('takeover', 'Human Operator', 'HUMAN TAKEOVER ENGAGED. Autonomous loop paused.');
    } else {
      addLog('takeover', 'AI Agent', 'CONTROL RETURNED TO AI AGENT. Resuming mission.');
    }
  };

  const getViewportStyles = () => {
    switch (viewportMode) {
      case 'mobile':
        return 'w-[375px] h-[667px] shadow-2xl border-4 border-slate-800 rounded-3xl';
      case 'tablet':
        return 'w-[768px] h-[1024px] shadow-2xl border-4 border-slate-800 rounded-2xl';
      default:
        return 'w-full h-full rounded-xl';
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#030611] text-slate-200 font-sans select-none overflow-hidden">
      
      {/* ── TOP ACTION HEADER ── */}
      <div className="h-14 border-b border-[#00f3ff]/15 bg-[#050b1a]/80 backdrop-blur-md px-4 flex items-center justify-between z-10 shadow-[0_2px_15px_rgba(0,0,0,0.4)]">
        
        {/* Left: Studio Title & Status */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#00f3ff]/10 border border-[#00f3ff]/40 flex items-center justify-center text-[#00f3ff] shadow-[0_0_12px_rgba(0,243,255,0.2)]">
            <Globe size={18} className={isRunning ? 'animate-spin' : ''} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-sm text-white tracking-wider">AI BROWSER AUTOMATION STUDIO</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#00f3ff]/10 text-[#00f3ff] border border-[#00f3ff]/30">
                PLAYWRIGHT ENGINE v3
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono">
              Status: {isTakeoverActive ? '⚠️ Human Intercept Active' : isRunning ? '⚡ Autonomous Loop Running' : '● Standby'}
            </p>
          </div>
        </div>

        {/* Center: Viewport Controls */}
        <div className="hidden md:flex items-center gap-1 bg-slate-900/60 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setViewportMode('desktop')}
            className={`p-1.5 rounded transition-all ${viewportMode === 'desktop' ? 'bg-[#00f3ff]/20 text-[#00f3ff]' : 'text-slate-400 hover:text-white'}`}
            title="Desktop View (100%)"
          >
            <Monitor size={15} />
          </button>
          <button
            onClick={() => setViewportMode('tablet')}
            className={`p-1.5 rounded transition-all ${viewportMode === 'tablet' ? 'bg-[#00f3ff]/20 text-[#00f3ff]' : 'text-slate-400 hover:text-white'}`}
            title="Tablet View (768px)"
          >
            <Laptop size={15} />
          </button>
          <button
            onClick={() => setViewportMode('mobile')}
            className={`p-1.5 rounded transition-all ${viewportMode === 'mobile' ? 'bg-[#00f3ff]/20 text-[#00f3ff]' : 'text-slate-400 hover:text-white'}`}
            title="Mobile View (375px)"
          >
            <Smartphone size={15} />
          </button>
        </div>

        {/* Right: Human Takeover Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleToggleTakeover}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
              isTakeoverActive
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.3)]'
                : 'bg-slate-900 text-slate-300 border border-slate-700 hover:border-[#00f3ff]/50 hover:text-white'
            }`}
          >
            <Hand size={14} className={isTakeoverActive ? 'animate-bounce' : ''} />
            {isTakeoverActive ? 'RELEASE TAKEOVER' : 'TAKE CONTROL (HITL)'}
          </button>
        </div>
      </div>

      {/* ── MAIN WORKSPACE GRID ── */}
      <div className="flex-1 flex overflow-hidden p-3 gap-3">

        {/* ══ LEFT: LIVE BROWSER CANVAS ══ */}
        <div className="flex-1 flex flex-col bg-[#050914] border border-[#00f3ff]/20 rounded-2xl overflow-hidden shadow-2xl relative">
          
          {/* Navigation Bar */}
          <form onSubmit={handleNavigate} className="h-11 bg-[#040815] border-b border-slate-800 px-3 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setReloadCounter(k => k + 1)}
              className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800/60 transition-colors"
              title="Refresh Frame"
            >
              <RefreshCw size={13} className={isRunning ? 'animate-spin' : ''} />
            </button>

            <div className="flex-1 flex items-center gap-2 bg-[#081026] border border-slate-800 focus-within:border-[#00f3ff]/50 rounded-lg px-3 py-1 transition-all">
              <Shield size={12} className="text-emerald-400" />
              <input
                type="text"
                value={inputUrl}
                onChange={e => setInputUrl(e.target.value)}
                placeholder="Enter URL (e.g. https://github.com)..."
                className="flex-1 bg-transparent text-xs text-white outline-none font-mono placeholder:text-slate-600"
              />
            </div>

            <button
              type="submit"
              className="px-3 py-1 bg-[#00f3ff]/15 border border-[#00f3ff]/30 hover:bg-[#00f3ff]/25 text-[#00f3ff] rounded-lg text-xs font-mono font-bold flex items-center gap-1 transition-all"
            >
              GO <ArrowRight size={12} />
            </button>
          </form>

          {/* Browser Iframe Canvas */}
          <div className="flex-1 bg-[#02040a] flex items-center justify-center p-2 overflow-auto relative">
            
            {/* Live Indicator Overlay */}
            <div className="absolute top-4 right-4 z-20 flex items-center gap-2 bg-slate-950/80 backdrop-blur-md px-3 py-1 rounded-full border border-slate-800 text-[10px] font-mono text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              LIVE PROXY FEED
            </div>

            <iframe
              ref={iframeRef}
              key={reloadCounter}
              src={getProxiedUrl(currentUrl)}
              className={`${getViewportStyles()} transition-all duration-300 border border-slate-800/80 bg-white`}
              sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
              title="SupremeAI Live Browser"
            />
          </div>
        </div>

        {/* ══ RIGHT: AI MISSION CONTROLLER & FINDINGS ══ */}
        <div className="w-96 flex flex-col bg-[#050914] border border-[#00f3ff]/20 rounded-2xl overflow-hidden shadow-2xl">
          
          {/* Mission Header */}
          <div className="p-3 border-b border-slate-800 bg-[#040815] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap size={14} className="text-[#00f3ff]" />
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">AI AGENT MISSION</span>
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setActiveTab('stream')}
                className={`px-2 py-1 rounded text-[10px] font-mono font-bold uppercase transition-all ${activeTab === 'stream' ? 'bg-[#00f3ff]/20 text-[#00f3ff]' : 'text-slate-400'}`}
              >
                Steps
              </button>
              <button
                onClick={() => setActiveTab('findings')}
                className={`px-2 py-1 rounded text-[10px] font-mono font-bold uppercase transition-all ${activeTab === 'findings' ? 'bg-[#00f3ff]/20 text-[#00f3ff]' : 'text-slate-400'}`}
              >
                Data ({findings.length})
              </button>
            </div>
          </div>

          {/* Prompt & Trigger Box */}
          <div className="p-3 border-b border-slate-800 bg-[#060d21]">
            <label className="text-[10px] font-mono text-slate-400 uppercase tracking-widest block mb-1.5">
              AUTONOMOUS GOAL PROMPT:
            </label>
            <textarea
              value={agentGoal}
              onChange={e => setAgentGoal(e.target.value)}
              rows={2}
              placeholder="e.g. Navigate to website, log in and download monthly invoice..."
              className="w-full bg-[#030612] border border-slate-800 focus:border-[#00f3ff]/50 rounded-lg p-2 text-xs text-slate-200 outline-none font-mono resize-none transition-all placeholder:text-slate-600"
            />
            
            <div className="flex gap-2 mt-2">
              <button
                onClick={handleStartGoal}
                disabled={isRunning}
                className="flex-1 py-1.5 bg-[#00f3ff] hover:bg-[#00d0db] disabled:opacity-50 text-black rounded-lg text-xs font-mono font-bold flex items-center justify-center gap-1.5 shadow-[0_0_12px_rgba(0,243,255,0.3)] transition-all"
              >
                <Play size={12} /> {isRunning ? 'EXECUTING...' : 'RUN AGENT'}
              </button>
              {isRunning && (
                <button
                  onClick={() => setIsRunning(false)}
                  className="px-3 py-1.5 bg-rose-500/20 border border-rose-500/40 text-rose-400 rounded-lg text-xs font-mono font-bold flex items-center gap-1 hover:bg-rose-500/30 transition-all"
                >
                  <Square size={12} /> STOP
                </button>
              )}
            </div>
          </div>

          {/* Tab Content: Steps & Stream */}
          {activeTab === 'stream' && (
            <div className="flex-1 flex flex-col overflow-hidden p-3">
              <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                <span>ACTION EXECUTION LOG:</span>
                <span className="text-[#00f3ff] font-bold">{logs.length} ACTIONS</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="p-2.5 rounded-lg bg-[#030612] border border-slate-800/80 text-xs flex flex-col gap-1 transition-all hover:border-slate-700"
                  >
                    <div className="flex items-center justify-between text-[10px]">
                      <span className={`px-1.5 py-0.5 rounded font-bold uppercase ${
                        log.action === 'thought' ? 'bg-indigo-500/20 text-indigo-300' :
                        log.action === 'click' ? 'bg-emerald-500/20 text-emerald-300' :
                        log.action === 'takeover' ? 'bg-amber-500/20 text-amber-300' :
                        'bg-cyan-500/20 text-cyan-300'
                      }`}>
                        {log.action}
                      </span>
                      <span className="text-slate-500">{log.timestamp}</span>
                    </div>
                    <p className="text-slate-300 text-[11px] leading-relaxed">{log.details}</p>
                    {log.target && (
                      <span className="text-[9px] text-[#00f3ff]/70 truncate">Target: {log.target}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab Content: Extracted Findings */}
          {activeTab === 'findings' && (
            <div className="flex-1 flex flex-col overflow-hidden p-3">
              <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                <span>EXTRACTED ARTIFACTS:</span>
                <button
                  onClick={() => alert('Exporting findings JSON...')}
                  className="text-[#00f3ff] text-[10px] hover:underline"
                >
                  Download JSON
                </button>
              </div>
              <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono">
                {findings.map((item, i) => (
                  <div key={i} className="p-2.5 rounded-lg bg-[#030612] border border-slate-800 text-xs">
                    <p className="font-bold text-white text-[11px] mb-1">{item.title}</p>
                    <div className="flex justify-between items-center text-[10px] text-slate-400">
                      <span className="truncate max-w-[180px]">{item.url}</span>
                      {item.score && <span className="text-emerald-400">{item.score}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};

export default LiveBrowserStudio;
