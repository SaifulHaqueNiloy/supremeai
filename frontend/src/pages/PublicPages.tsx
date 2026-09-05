import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowUp, Check, FileText, History, Menu, Paperclip, Plus, Sparkles, Wrench, X } from 'lucide-react';

const publicLinks = [
  { to: '/features', label: 'Features' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/docs', label: 'Docs' },
];

export function PublicHeader() {
  const [menuOpen, setMenuOpen] = React.useState(false);
  return (
    <header className="absolute inset-x-0 top-0 z-20 px-4 py-4 sm:px-8 sm:py-5">
      <div className="mx-auto flex max-w-6xl items-center justify-between">
        <Link to="/" aria-label="SupremeAI home" className="flex items-center gap-3 text-sm font-semibold tracking-[0.18em] text-slate-100">
          <span className="flex size-8 items-center justify-center rounded-xl bg-cyan-300 font-mono text-sm font-bold text-slate-950">S</span>
          <span className="hidden sm:inline">SUPREMEAI</span>
        </Link>
        <nav className="hidden items-center gap-7 md:flex" aria-label="Public navigation">
          {publicLinks.map((link) => <Link key={link.to} to={link.to} className="text-sm text-slate-500 transition hover:text-slate-200">{link.label}</Link>)}
        </nav>
        <div className="flex items-center gap-3">
          <Link to="/login" className="hidden text-sm text-slate-400 transition hover:text-slate-100 sm:block">Sign in</Link>
          <Link to="/register" className="rounded-full bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200">Get started</Link>
          <button type="button" onClick={() => setMenuOpen((open) => !open)} className="rounded-lg p-2 text-slate-400 md:hidden" aria-label={menuOpen ? 'Close menu' : 'Open menu'} aria-expanded={menuOpen}>{menuOpen ? <X size={18} /> : <Menu size={18} />}</button>
        </div>
      </div>
      {menuOpen && <nav className="mx-auto mt-3 flex max-w-6xl flex-col gap-1 rounded-2xl border border-white/10 bg-slate-900/95 p-3 md:hidden" aria-label="Mobile navigation">{publicLinks.map((link) => <Link key={link.to} to={link.to} onClick={() => setMenuOpen(false)} className="rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/5">{link.label}</Link>)}<Link to="/login" className="rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/5">Sign in</Link></nav>}
    </header>
  );
}

export function PublicLayout({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-[#0d0f12] text-slate-100">{children}</div>;
}

const capabilityItems = [
  { title: 'History', text: 'Save and revisit conversations', icon: History },
  { title: 'Files', text: 'Work with your own context', icon: FileText },
  { title: 'Tools', text: 'Connect actions and workflows', icon: Wrench },
];

function responseFor(input: string) {
  const text = input.toLowerCase();
  if (text.includes('plan') || text.includes('build')) return 'I can help you turn that idea into a practical plan. Start with the outcome, then add the context and constraints that matter.';
  if (text.includes('file') || text.includes('document')) return 'That is a great use for SupremeAI. With an account, you can bring files into the conversation and keep the source context attached.';
  if (text.includes('automat') || text.includes('workflow')) return 'We can shape that into a repeatable workflow. Sign in when you want to save it, connect tools, and run it with approval.';
  return 'I can help you think that through. Ask me to plan, explain, summarize, or turn an idea into your next action.';
}

type Message = { role: 'user' | 'assistant'; text: string };

export function GuestChatPage() {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState('');
  const [showCapabilities, setShowCapabilities] = React.useState(false);
  const inputRef = React.useRef<HTMLTextAreaElement>(null);

  const submit = (event?: React.FormEvent) => {
    event?.preventDefault();
    const value = input.trim();
    if (!value) return;
    setMessages((current) => [...current, { role: 'user', text: value }, { role: 'assistant', text: responseFor(value) }]);
    setInput('');
    setShowCapabilities(true);
  };

  const reset = () => {
    setMessages([]);
    setInput('');
    inputRef.current?.focus();
  };

  return <PublicLayout><main className="relative flex min-h-screen flex-col overflow-hidden px-4 pb-8 pt-24 sm:px-8">
    <div className="pointer-events-none absolute left-1/2 top-[31%] size-[32rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-950/35 blur-3xl" aria-hidden="true" />
    <section className="relative mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center">
      <div className="mb-7 text-center transition-all duration-500" data-chat-start={messages.length === 0}>
        {messages.length === 0 ? <><div className="mx-auto mb-5 flex size-12 items-center justify-center rounded-2xl bg-cyan-300/10 text-cyan-300"><Sparkles size={23} aria-hidden="true" /></div><h1 className="text-balance text-3xl font-medium tracking-tight text-slate-200 sm:text-5xl">What can I help you with?</h1><p className="mx-auto mt-4 max-w-md text-sm leading-6 text-slate-500">Chat with SupremeAI for free. No account needed to get started.</p></> : <div className="max-h-[38vh] space-y-4 overflow-y-auto px-1 text-left" aria-live="polite">{messages.map((message, index) => <div key={`${message.role}-${index}`} className={message.role === 'user' ? 'ml-auto max-w-[85%] rounded-3xl bg-slate-800 px-5 py-3 text-sm leading-6 text-slate-100' : 'max-w-[85%] px-5 py-3 text-sm leading-6 text-slate-400'}>{message.text}</div>)}</div>}
      </div>

      <form onSubmit={submit} className="relative rounded-[1.65rem] border border-white/10 bg-[#202124] p-3 shadow-[0_18px_80px_rgba(0,0,0,0.3)] focus-within:border-cyan-300/35" aria-label="Guest chat">
        <textarea ref={inputRef} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing && event.keyCode !== 229) { event.preventDefault(); submit(); } }} rows={2} placeholder="Ask SupremeAI anything..." className="min-h-14 w-full resize-none bg-transparent px-2 py-1 text-base leading-7 text-slate-100 outline-none placeholder:text-slate-600" aria-label="Message SupremeAI" />
        <div className="flex items-center justify-between gap-3 pt-2"><div className="flex items-center gap-1"><button type="button" className="rounded-full p-2 text-slate-500 transition hover:bg-white/10 hover:text-slate-300" aria-label="Attach a file"><Paperclip size={18} /></button><button type="button" onClick={reset} className="rounded-full p-2 text-slate-500 transition hover:bg-white/10 hover:text-slate-300" aria-label="Start a new chat"><Plus size={19} /></button><span className="hidden text-xs text-slate-600 sm:inline">Guest chat · temporary session</span></div><button type="submit" disabled={!input.trim()} className="flex size-9 items-center justify-center rounded-full bg-slate-100 text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-30" aria-label="Send message"><ArrowUp size={18} /></button></div>
      </form>

      {showCapabilities && <div className="mt-7 rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-center"><p className="text-sm text-slate-400">Enjoying the conversation? Sign in to keep going with more context.</p><div className="mt-4 flex flex-wrap justify-center gap-2">{capabilityItems.map(({ title, icon: Icon, text }) => <Link key={title} to="/register" className="flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs text-slate-400 transition hover:border-cyan-300/40 hover:text-cyan-200" title={text}><Icon size={14} />{title}</Link>)}<Link to="/register" className="flex items-center gap-2 rounded-full bg-cyan-300 px-4 py-2 text-xs font-semibold text-slate-950 transition hover:bg-cyan-200"><Check size={14} />Continue with an account</Link></div></div>}
    </section>
    <p className="relative mx-auto mt-6 max-w-2xl text-center text-xs leading-5 text-slate-600">SupremeAI may make mistakes. For saved history, file context, tools, and extended conversations, <Link to="/login" className="text-slate-400 underline underline-offset-4 hover:text-cyan-200">sign in</Link>.</p>
  </main></PublicLayout>;
}

const pageCopy: Record<string, { eyebrow: string; title: string; description: string }> = {
  '/pricing': { eyebrow: 'Plans', title: 'Start free, then scale with context.', description: 'Try the core conversation experience first. Create an account when you need history, files, tools, and longer-running work.' },
  '/features': { eyebrow: 'Features', title: 'A simple conversation can become useful work.', description: 'Start with a question. Add context, tools, and repeatable workflows as your needs grow.' },
  '/docs': { eyebrow: 'Docs', title: 'From first question to governed execution.', description: 'Learn how guest chat, saved conversations, context, tools, and workspaces fit together.' },
  '/about': { eyebrow: 'About', title: 'AI that starts simple and grows with you.', description: 'SupremeAI makes intelligent work approachable at the first message and dependable at scale.' },
  '/contact': { eyebrow: 'Contact', title: 'Bring your hardest workflow.', description: 'Tell us what you want to make simpler and we will help you find the right starting point.' },
};

export function PublicInfoPage({ kind }: { kind: '/features' | '/pricing' | '/docs' | '/about' | '/contact' }) {
  const copy = pageCopy[kind];
  return <PublicLayout><PublicHeader /><main className="mx-auto max-w-5xl px-5 pb-24 pt-36 sm:px-8"><p className="font-mono text-xs uppercase tracking-[0.2em] text-cyan-300">{copy.eyebrow}</p><h1 className="mt-5 max-w-3xl text-balance text-4xl font-medium tracking-tight text-slate-100 sm:text-6xl">{copy.title}</h1><p className="mt-6 max-w-2xl text-pretty text-lg leading-8 text-slate-500">{copy.description}</p><div className="mt-14 grid gap-3 sm:grid-cols-3">{capabilityItems.map(({ title, text, icon: Icon }) => <article key={title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"><Icon size={19} className="text-cyan-300" /><h2 className="mt-8 font-medium text-slate-200">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-500">{text}</p></article>)}</div><Link to="/" className="mt-12 inline-flex items-center gap-2 rounded-full bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-200">Try SupremeAI <ArrowUp size={16} className="rotate-45" /></Link></main></PublicLayout>;
}

export function PricingPage() { return <PublicInfoPage kind="/pricing" />; }
export default GuestChatPage;
