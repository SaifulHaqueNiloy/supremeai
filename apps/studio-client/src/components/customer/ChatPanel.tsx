import React, { useState } from 'react';
import type { ChatMessage } from '../../types';
import { UnifiedChatBubble } from '../chat';

// বাংলা মন্তব্য: Markdown রেন্ডার করার জন্য হালকা ফাংশন
function sanitizeHtml(html: string): string {
  const allowedTags = /^(strong|code|br)$/;
  return html.replace(/<\/?([a-zA-Z][a-zA-Z0-9]*)[^>]*>/g, (match, tag) => {
    const lowerTag = tag.toLowerCase();
    if (allowedTags.test(lowerTag)) {
      const isClosing = match.startsWith('</');
      return isClosing ? `</${lowerTag}>` : `<${lowerTag}>`;
    }
    return '';
  });
}

function renderMarkdown(text: string): React.ReactNode[] {
  const elements: React.ReactNode[] = [];
  const lines = text.split('\n');
  let inCodeBlock = false;
  let codeBuffer: string[] = [];
  let codeLang = '';

  lines.forEach((line, idx) => {
    // Code block handling
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        // Close code block
        const code = codeBuffer.join('\n');
        elements.push(
          <pre key={`cb-${idx}`} className="bg-[#0c0d13] border border-slate-700 rounded-lg p-3 my-2 overflow-x-auto text-[11px] font-mono">
            <code>{code}</code>
          </pre>
        );
        codeBuffer = [];
        inCodeBlock = false;
        codeLang = '';
      } else {
        inCodeBlock = true;
        codeLang = line.slice(3).trim();
      }
      return;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      return;
    }

    // Bold: **text**
    const escapedLine = line
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');

    const processed = escapedLine
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.+?)`/g, '<code class="bg-[#1a1d2e] text-[#bc13fe] px-1 rounded text-[11px] font-mono">$1</code>');

    if (line.trim() === '') {
      elements.push(<br key={`br-${idx}`} />);
    } else if (line.startsWith('- ')) {
      elements.push(
        <div key={`li-${idx}`} className="flex gap-2 text-xs text-slate-300 ml-2">
          <span className="text-[#bc13fe]">•</span>
          <span dangerouslySetInnerHTML={{ __html: sanitizeHtml(processed.slice(2)) }} />
        </div>
      );
    } else {
      elements.push(
        <div key={`p-${idx}`} className="text-xs text-slate-300 leading-relaxed" dangerouslySetInnerHTML={{ __html: sanitizeHtml(processed) }} />
      );
    }
  });

  // Unclosed code block
  if (inCodeBlock && codeBuffer.length > 0) {
    elements.push(
      <pre key="cb-unclosed" className="bg-[#0c0d13] border border-slate-700 rounded-lg p-3 my-2 overflow-x-auto text-[11px] font-mono">
        <code>{codeBuffer.join('\n')}</code>
      </pre>
    );
  }

  return elements;
}

interface ChatPanelProps {
  messages: ChatMessage[];
  input: string;
  onInputChange: (val: string) => void;
  onSend: () => void;
  loading: boolean;
  onSaveToProject?: (code: string) => void;
}

export function ChatPanel({ messages, input, onInputChange, onSend, loading, onSaveToProject }: ChatPanelProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      // clipboard not available
    }
  };

  return (
    <div className="w-96 flex-shrink-0 bg-[#050608]/90 border-l border-slate-800 flex flex-col">
      <div className="h-10 border-b border-slate-800 flex items-center px-4 justify-between bg-[#0a0c12]">
        {/* বাংলা মন্তব্য: চ্যাট প্যানেল লোড হয়েছে কিনা তা টেস্টে যাচাই করার জন্য chat-header data-testid দেওয়া হলো */}
        <span data-testid="chat-header" className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Unified Command Portal</span>
        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/30 text-emerald-400 border border-emerald-900/30 font-mono">ONLINE</span>
      </div>
      <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4">
        {messages.map(msg => {
          const isUser = msg.sender === 'User' || msg.sender === 'user';
          return (
            <div key={msg.id} className="group relative">
              <UnifiedChatBubble
                text={msg.text}
                sender={isUser ? 'user' : 'system'}
                timestamp={msg.timestamp}
                action={msg.action}
                onSaveToProject={onSaveToProject}
              />
              {/* Copy button on hover */}
              {!isUser && (
                <button
                  onClick={() => handleCopy(msg.text, String(msg.id))}
                  className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700"
                  title="Copy message"
                >
                  {copiedId === String(msg.id) ? 'Copied!' : 'Copy'}
                </button>
              )}
            </div>
          );
        })}

        {loading && (
          <div className="text-xs text-slate-400 animate-pulse font-mono flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-[#bc13fe] rounded-full animate-bounce"></span>
            SupremeAI is thinking...
          </div>
        )}
      </div>
      <div className="p-4 border-t border-slate-800 bg-[#050608]">
        <div className="flex gap-2">
          {/* বাংলা মন্তব্য: টেস্টে চ্যাট ইনপুট দেওয়ার জন্য chat-input data-testid ব্যবহার করা হলো */}
          <input
            data-testid="chat-input"
            type="text"
            placeholder="Ask anything or execute a command…"
            value={input}
            onChange={e => onInputChange(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && onSend()}
            className="flex-grow bg-[#0c0d13] border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#bc13fe] transition-colors"
          />
          {/* বাংলা মন্তব্য: চ্যাট মেসেজ পাঠানোর বাটনে ক্লিক করতে chat-submit data-testid দেওয়া হলো */}
          <button
            data-testid="chat-submit"
            onClick={onSend}
            className="bg-[#bc13fe] hover:bg-[#8b5cf6] text-white px-4 rounded-xl font-bold transition-all shadow-[0_4px_12px_rgba(188,19,254,0.2)] text-xs uppercase"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
