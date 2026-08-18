import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Search, X, Send } from 'lucide-react';
import { ChatBubble } from '@supremeai/ui-components';
import { BACKEND_URL } from '../config';

// ═══════════════════════════════════════════════════════════════
// AETHEL Desktop Studio — Global Floating AI Assistant (Alt + Space Widget)
// বাংলা মন্তব্য: থিন ক্লায়েন্ট — সরাসরি ব্যাকএন্ড /api/chat/stream দিয়ে রাউট করে
// (কোনো লোকাল/থার্ড-পার্টি AI সিমুলেশন নেই; অফলাইন fallback শুধু local Ollama)
// ═══════════════════════════════════════════════════════════════

interface Msg {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface FloatingAssistantBarProps {
  onClose?: () => void;
}

export const FloatingAssistantBar: React.FC<FloatingAssistantBarProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = prompt.trim();
    if (!text || loading) return;
    setPrompt('');
    setMessages((m) => [...m, { role: 'user', content: text, timestamp: new Date() }]);
    setLoading(true);

    const assistant: Msg = { role: 'assistant', content: '', timestamp: new Date() };
    setMessages((m) => [...m, assistant]);

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok || !res.body) throw new Error(`Stream failed: ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      // Thin-client SSE parse: lines of `data: {token}` ending with `data: [DONE]`
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const data = trimmed.slice(5).trim();
          if (data === '[DONE]') continue;
          try {
            const json = JSON.parse(data);
            const token: string = json.token ?? '';
            if (token) {
              setMessages((m) => {
                const copy = [...m];
                const last = copy[copy.length - 1];
                if (last?.role === 'assistant') {
                  copy[copy.length - 1] = { ...last, content: last.content + token };
                }
                return copy;
              });
            }
          } catch {
            /* ignore non-JSON keepalive frames */
          }
        }
      }
    } catch {
      setMessages((m) => {
        const copy = [...m];
        const last = copy[copy.length - 1];
        if (last?.role === 'assistant') {
          copy[copy.length - 1] = { ...last, content: last.content || '⚠️ Backend connection failed.' };
        }
        return copy;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed top-12 left-1/2 -translate-x-1/2 w-[680px] h-[520px] bg-[#080b14]/90 backdrop-blur-xl border border-[#00f3ff]/30 rounded-2xl shadow-[0_0_40px_rgba(0,243,255,0.25)] p-4 text-white z-50 flex flex-col font-sans">
      <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#00f3ff] to-[#bc13fe] flex items-center justify-center shadow-[0_0_10px_#00f3ff]">
            <Sparkles size={16} className="text-black" />
          </div>
          <span className="text-xs font-mono font-bold uppercase tracking-widest text-[#00f3ff]">
            SupremeAI Floating Assistant
          </span>
          <span className="text-[10px] bg-[#00f3ff]/10 text-[#00f3ff] px-2 py-0.5 rounded-full border border-[#00f3ff]/30 font-mono">
            Alt + Space
          </span>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={16} />
          </button>
        )}
      </div>

      {/* Conversation */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto pr-1 space-y-3">
        {messages.length === 0 && (
          <p className="text-xs text-gray-500 font-mono">
            Ask AI anything, generate code, or execute a command — routed through the SupremeAI backend.
          </p>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} content={m.content} timestamp={m.timestamp} />
        ))}
        {loading && (
          <span className="text-[10px] font-mono text-[#00f3ff] animate-pulse">● streaming…</span>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="relative flex items-center mt-3">
        <Search size={18} className="absolute left-3 text-[#00f3ff]" />
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ask AI anything, generate code, or execute command..."
          className="w-full bg-black/40 border border-white/10 rounded-xl pl-10 pr-24 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#00f3ff] transition-all font-mono"
          autoFocus
        />
        <button
          type="submit"
          disabled={loading}
          className="absolute right-2 bg-gradient-to-r from-[#00f3ff] to-[#bc13fe] text-black font-bold text-xs px-4 py-2 rounded-lg hover:opacity-90 transition-opacity flex items-center gap-1 disabled:opacity-50"
        >
          <Send size={14} />
          <span>Run</span>
        </button>
      </form>
    </div>
  );
};
