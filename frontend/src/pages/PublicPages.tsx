import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, BookOpen, Check, Mail, ShieldCheck, Sparkles, Workflow } from 'lucide-react';

const publicLinks = [
  { to: '/features', label: 'Features' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/docs', label: 'Docs' },
  { to: '/about', label: 'About' },
  { to: '/contact', label: 'Contact' },
];

export function PublicHeader() {
  return (
    <header className="sticky top-0 z-20 border-b border-cyan-400/15 bg-[#07111f]/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-5 py-4 sm:px-8">
        <Link to="/" className="flex items-center gap-3" aria-label="SupremeAI home">
          <span className="flex size-9 items-center justify-center rounded-lg bg-cyan-300 font-mono text-sm font-bold text-[#07111f]">S</span>
          <span className="font-mono text-sm font-semibold tracking-[0.16em] text-slate-100">SUPREMEAI</span>
        </Link>
        <nav className="hidden items-center gap-6 md:flex" aria-label="Public navigation">
          {publicLinks.map((link) => <Link key={link.to} to={link.to} className="text-sm text-slate-400 transition hover:text-cyan-200">{link.label}</Link>)}
        </nav>
        <div className="flex items-center gap-3">
          <Link to="/login" className="hidden text-sm font-medium text-slate-300 transition hover:text-cyan-200 sm:block">Sign in</Link>
          <Link to="/register" className="rounded-lg bg-cyan-300 px-4 py-2 text-sm font-semibold text-[#07111f] transition hover:bg-cyan-200">Create account</Link>
        </div>
      </div>
    </header>
  );
}

export function PublicLayout({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-[#07111f] text-slate-100"><PublicHeader />{children}<footer className="border-t border-cyan-400/15 px-5 py-8 text-sm text-slate-500 sm:px-8"><div className="mx-auto flex max-w-7xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><span>SupremeAI — reliable action from intent.</span><span className="font-mono text-xs">Private by design.</span></div></footer></div>;
}

const pageCopy: Record<string, { eyebrow: string; title: string; description: string }> = {
  '/pricing': { eyebrow: 'Plans', title: 'Start small. Govern deeply.', description: 'Explore the operating model first, then bring governed automation to the workflows that matter.' },
  '/features': { eyebrow: 'Capability map', title: 'One command center for intelligent work.', description: 'SupremeAI connects agents, automation, oversight, and execution in one operational surface.' },
  '/docs': { eyebrow: 'Documentation', title: 'Understand the system before you extend it.', description: 'Start with the core concepts, then move into agents, tools, approvals, and deployment.' },
  '/about': { eyebrow: 'The company', title: 'Built for useful autonomy, not opaque magic.', description: 'SupremeAI helps teams turn high-level intent into observable, governable action.' },
  '/contact': { eyebrow: 'Contact', title: 'Bring a real workflow to the command center.', description: 'Tell us what you want to coordinate and we will help map the safest path forward.' },
};

export function PublicInfoPage({ kind }: { kind: '/features' | '/pricing' | '/docs' | '/about' | '/contact' }) {
  const copy = pageCopy[kind];
  return <PublicLayout><main className="mx-auto max-w-7xl px-5 py-16 sm:px-8 sm:py-24"><div className="max-w-3xl"><p className="font-mono text-xs uppercase tracking-[0.24em] text-cyan-300">{copy.eyebrow}</p><h1 className="mt-5 text-balance text-4xl font-semibold tracking-tight text-slate-50 sm:text-6xl">{copy.title}</h1><p className="mt-6 max-w-2xl text-pretty text-lg leading-8 text-slate-400">{copy.description}</p></div>{kind === '/features' && <div className="mt-14 grid gap-4 md:grid-cols-3">{[{ icon: Workflow, title: 'Build', text: 'Compose agents, models, skills, and integrations without losing the thread.' }, { icon: ShieldCheck, title: 'Govern', text: 'Keep approvals, policies, audit trails, and human oversight close to execution.' }, { icon: Sparkles, title: 'Observe', text: 'See what is running, what changed, and where the next decision belongs.' }].map(({ icon: Icon, title, text }) => <article key={title} className="border border-cyan-400/15 bg-[#0b1a2d] p-6"><Icon className="text-cyan-300" aria-hidden="true" /><h2 className="mt-8 text-xl font-semibold">{title}</h2><p className="mt-3 leading-7 text-slate-400">{text}</p></article>)}</div>}{kind === '/pricing' && <div className="mt-14 grid max-w-4xl gap-4 md:grid-cols-2">{[{ name: 'Explore', price: 'Free', text: 'Try the guest experience and understand the operating model.' }, { name: 'Scale', price: 'Custom', text: 'Bring governed automation, integrations, and team workflows to production.' }].map((plan) => <article key={plan.name} className="border border-cyan-400/15 bg-[#0b1a2d] p-7"><p className="font-mono text-xs uppercase tracking-[0.18em] text-cyan-300">{plan.name}</p><p className="mt-5 text-4xl font-semibold">{plan.price}</p><p className="mt-4 leading-7 text-slate-400">{plan.text}</p><Link to={plan.name === 'Explore' ? '/' : '/contact'} className="mt-8 inline-flex items-center gap-2 font-semibold text-cyan-200">{plan.name === 'Explore' ? 'Try guest chat' : 'Talk to us'} <ArrowRight size={16} /></Link></article>)}</div>}{kind === '/docs' && <div className="mt-14 grid max-w-4xl gap-3">{['Start with the guest chat', 'Create an authenticated workspace', 'Connect tools with explicit permissions', 'Review activity and approvals'].map((item, index) => <div key={item} className="flex items-center gap-4 border-b border-cyan-400/15 py-5"><span className="font-mono text-sm text-cyan-300">0{index + 1}</span><BookOpen size={18} className="text-slate-500" /><span className="font-medium">{item}</span></div>)}</div>}{kind === '/about' && <div className="mt-14 max-w-2xl border-l-2 border-cyan-300 pl-6 text-lg leading-8 text-slate-300">The product is designed around a simple promise: every powerful action should be understandable, observable, and interruptible when a person needs to be in control.</div>}{kind === '/contact' && <div className="mt-14 max-w-xl border border-cyan-400/15 bg-[#0b1a2d] p-7"><p className="text-slate-300">For product, partnership, or implementation questions, start a conversation with our team.</p><a href="mailto:hello@supremeai.dev" className="mt-7 inline-flex items-center gap-2 font-semibold text-cyan-200"><Mail size={17} /> hello@supremeai.dev</a></div>}</main></PublicLayout>;
}

export function PricingPage() { return <PublicInfoPage kind="/pricing" />; }

export function GuestChatPage() {
  const [messages, setMessages] = React.useState<Array<{ role: 'user' | 'assistant'; text: string }>>([{ role: 'assistant', text: 'Tell me what you want to accomplish. I can help you shape the workflow before you create an account.' }]);
  const [input, setInput] = React.useState('');
  const [isSubmitted, setIsSubmitted] = React.useState(false);
  const submit = (event: React.FormEvent) => { event.preventDefault(); const text = input.trim(); if (!text) return; setMessages((current) => [...current, { role: 'user', text }, { role: 'assistant', text: 'I have the shape of that workflow. Create a free account to continue with tools, files, and execution.' }]); setInput(''); setIsSubmitted(true); };
  return <PublicLayout><main className="mx-auto grid min-h-[calc(100vh-145px)] max-w-7xl items-center gap-12 px-5 py-12 sm:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:gap-20"><section><p className="font-mono text-xs uppercase tracking-[0.24em] text-cyan-300">Guest command center</p><h1 className="mt-5 text-balance text-5xl font-semibold tracking-tight sm:text-7xl">Start with the work. Not the setup.</h1><p className="mt-6 max-w-xl text-pretty text-lg leading-8 text-slate-400">Describe an outcome and see how SupremeAI turns intent into a governed path. No account is required to begin.</p><div className="mt-8 flex flex-wrap gap-3 text-sm text-slate-400"><span className="flex items-center gap-2"><Check size={15} className="text-cyan-300" /> No card required</span><span className="flex items-center gap-2"><Check size={15} className="text-cyan-300" /> Human approval by design</span></div></section><section className="border border-cyan-400/20 bg-[#0b1a2d] shadow-2xl shadow-cyan-950/30" aria-labelledby="guest-chat-heading"><div className="flex items-center justify-between border-b border-cyan-400/15 px-5 py-4"><div><p className="font-mono text-[10px] uppercase tracking-[0.2em] text-cyan-300">Open session</p><h2 id="guest-chat-heading" className="mt-1 font-semibold">Intent workspace</h2></div><span className="flex items-center gap-2 text-xs text-slate-500"><span className="size-2 rounded-full bg-emerald-400" /> Ready</span></div><div className="flex min-h-80 flex-col gap-4 p-5">{messages.map((message, index) => <div key={`${message.role}-${index}`} className={message.role === 'user' ? 'ml-8 border border-cyan-400/20 bg-cyan-300/10 p-4 text-sm text-cyan-50' : 'mr-8 border border-white/10 bg-[#07111f] p-4 text-sm leading-6 text-slate-300'}>{message.text}</div>)}{isSubmitted && <Link to="/register" className="inline-flex items-center gap-2 self-start text-sm font-semibold text-cyan-200">Continue in workspace <ArrowRight size={15} /></Link>}</div><form onSubmit={submit} className="border-t border-cyan-400/15 p-4"><label htmlFor="guest-intent" className="sr-only">Describe what you want to accomplish</label><div className="flex gap-3"><textarea id="guest-intent" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing && event.keyCode !== 229) { event.preventDefault(); submit(event); } }} placeholder="e.g. Help me automate weekly customer reporting" rows={2} className="min-w-0 flex-1 resize-none border border-white/10 bg-[#07111f] px-4 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-cyan-300" /><button type="submit" className="self-end rounded-lg bg-cyan-300 px-4 py-3 text-sm font-semibold text-[#07111f] transition hover:bg-cyan-200">Send</button></div></form></section></main></PublicLayout>;
}

export default GuestChatPage;
