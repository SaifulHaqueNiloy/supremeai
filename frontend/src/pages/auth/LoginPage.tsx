import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { ServiceHealthBar } from '../../components/auth/ServiceHealthBar';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('দয়া করে সব ফিল্ড পূরণ করুন।');
      return;
    }

    setIsLoading(true);
    // LIVE-002/003 FIX: Add 30s timeout so login doesn't hang forever.
    // Previously: if backend was slow/down, 'INITIALIZING...' stuck indefinitely.
    const LOGIN_TIMEOUT = 30000;
    try {
      const loginPromise = login(email, password);
      await Promise.race([
        loginPromise,
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('Connection timeout. Server may be starting up — please retry in 30s.')), LOGIN_TIMEOUT)
        ),
      ]);
      navigate('/workspace');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      // বাংলা মন্তব্য: Enhanced Error Handling — Backend/Network সমস্যা চিহ্নিত করে User-friendly message দেখায়
      let userMessage = 'লগইন ব্যর্থ হয়েছে।';
      
      // Network/Timeout errors (backend down, cold start, etc.)
      if (err?.message?.includes('timed out') || err?.message?.includes('timeout')) {
        userMessage = '⏰ Server response timeout — Backend may be starting up (cold start). Please retry in 30s.';
      } else if (err?.message?.includes('Failed to fetch') || err?.message?.includes('NetworkError')) {
        userMessage = '🌐 Network Error — Unable to reach server. Check your connection or try again later.';
      } else if (err?.status === 503 || err?.status === 502 || err?.status === 504) {
        userMessage = '🔧 Server temporarily unavailable (maintenance/cold start). Please wait 1-2 minutes.';
      } else if (err?.status === 401 || err?.status === 403) {
        userMessage = '🔑 Invalid credentials. Check your email/password and try again.';
      } else if (err?.response?.data?.detail) {
        const detail = typeof err.response.data.detail === 'string' 
          ? err.response.data.detail 
          : JSON.stringify(err.response.data.detail);
        userMessage = detail.includes('database') || detail.includes('Database')
          ? '🗄️ Database service unavailable — Our team has been notified.'
          : `Error: ${detail}`;
      }
      
      setError(userMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[var(--supremeai-color-bg-void-light)] px-5 py-6 text-[var(--supremeai-color-text-primary-light)] dark:bg-[var(--supremeai-color-bg-void-dark)] dark:text-[var(--supremeai-color-text-primary-dark)] sm:px-8 lg:px-12">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl flex-col">
        <header className="flex items-center justify-between gap-4 py-2">
          <Link to="/" className="flex items-center gap-3" aria-label="SupremeAI home">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--supremeai-color-primary-light)] text-sm font-bold text-white shadow-sm dark:bg-[var(--supremeai-color-primary-dark)]">S</span>
            <span className="font-semibold tracking-tight">SupremeAI</span>
          </Link>
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--supremeai-color-text-secondary-light)] dark:text-[var(--supremeai-color-text-secondary-dark)]">Secure workspace access</span>
        </header>

        <div className="grid flex-1 items-center gap-12 py-12 lg:grid-cols-[1fr_420px] lg:gap-20">
          <section className="hidden max-w-xl lg:block">
            <p className="mb-5 font-mono text-xs uppercase tracking-[0.2em] text-[var(--supremeai-color-primary-light)] dark:text-[var(--supremeai-color-primary-dark)]">Your command center</p>
            <h1 className="max-w-lg text-4xl font-semibold leading-tight tracking-[-0.04em] sm:text-5xl">Turn intent into reliable action.</h1>
            <p className="mt-6 max-w-md text-base leading-7 text-[var(--supremeai-color-text-secondary-light)] dark:text-[var(--supremeai-color-text-secondary-dark)]">Coordinate agents, automate repeatable work, and keep every important decision in view.</p>
            <div className="mt-10 grid max-w-md grid-cols-3 gap-3" aria-label="SupremeAI capabilities">
              {['Agents', 'Automations', 'Oversight'].map((item) => <div key={item} className="rounded-2xl border border-[var(--supremeai-color-border-default-light)] bg-white/70 p-4 text-xs font-medium dark:border-[var(--supremeai-color-border-default-dark)] dark:bg-white/[0.03]">{item}</div>)}
            </div>
          </section>

          <section className="w-full">
            <div className="mb-4"><ServiceHealthBar /></div>
            <div className="rounded-3xl border border-[var(--supremeai-color-border-default-light)] bg-white p-7 shadow-[0_18px_50px_rgba(17,22,21,0.08)] dark:border-[var(--supremeai-color-border-default-dark)] dark:bg-[var(--supremeai-color-bg-elevated-dark)] dark:shadow-none sm:p-9">
              <div className="mb-8">
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--supremeai-color-text-secondary-light)] dark:text-[var(--supremeai-color-text-secondary-dark)]">Welcome back</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight">Sign in to continue</h2>
                <p className="mt-2 text-sm text-[var(--supremeai-color-text-secondary-light)] dark:text-[var(--supremeai-color-text-secondary-dark)]">Access your workspace and active tasks.</p>
              </div>

              {error && <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">{error}</div>}

              <form onSubmit={handleLogin} className="space-y-5">
                <label className="block text-sm font-medium" htmlFor="login-email">Email address<input id="login-email" name="email" autoComplete="email" type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} className="mt-2 w-full rounded-xl border border-[var(--supremeai-color-border-default-light)] bg-[var(--supremeai-color-bg-void-light)] px-4 py-3 outline-none transition focus:border-[var(--supremeai-color-primary-light)] focus:ring-4 focus:ring-[var(--supremeai-color-primary-soft-light)] dark:border-[var(--supremeai-color-border-default-dark)] dark:bg-[var(--supremeai-color-bg-void-dark)] dark:focus:border-[var(--supremeai-color-primary-dark)]" /></label>
                <label className="block text-sm font-medium" htmlFor="login-password">Password<input id="login-password" name="password" autoComplete="current-password" type="password" placeholder="Enter your password" value={password} onChange={e => setPassword(e.target.value)} className="mt-2 w-full rounded-xl border border-[var(--supremeai-color-border-default-light)] bg-[var(--supremeai-color-bg-void-light)] px-4 py-3 outline-none transition focus:border-[var(--supremeai-color-primary-light)] focus:ring-4 focus:ring-[var(--supremeai-color-primary-soft-light)] dark:border-[var(--supremeai-color-border-default-dark)] dark:bg-[var(--supremeai-color-bg-void-dark)] dark:focus:border-[var(--supremeai-color-primary-dark)]" /></label>
                <button type="submit" disabled={isLoading} className="w-full rounded-xl bg-[var(--supremeai-color-primary-light)] px-4 py-3 font-semibold text-white transition hover:brightness-95 focus:outline-none focus:ring-4 focus:ring-[var(--supremeai-color-primary-soft-light)] disabled:cursor-not-allowed disabled:opacity-60 dark:bg-[var(--supremeai-color-primary-dark)]">{isLoading ? 'Signing in…' : 'Sign in'}</button>
                <button type="button" className="w-full rounded-xl border border-[var(--supremeai-color-border-default-light)] px-4 py-3 text-sm font-medium transition hover:bg-[var(--supremeai-color-bg-muted-light)] dark:border-[var(--supremeai-color-border-default-dark)] dark:hover:bg-[var(--supremeai-color-bg-muted-dark)]">Continue with Google</button>
              </form>

              <p className="mt-7 text-center text-sm text-[var(--supremeai-color-text-secondary-light)] dark:text-[var(--supremeai-color-text-secondary-dark)]">Don&apos;t have an account? <Link to="/register" className="font-semibold text-[var(--supremeai-color-primary-light)] hover:underline dark:text-[var(--supremeai-color-primary-dark)]">Create one</Link></p>
            </div>
          </section>
        </div>
        <footer className="flex items-center justify-between border-t border-[var(--supremeai-color-border-default-light)] py-5 text-[10px] text-[var(--supremeai-color-text-secondary-light)] dark:border-[var(--supremeai-color-border-default-dark)] dark:text-[var(--supremeai-color-text-secondary-dark)]"><span>Private by design.</span><span className="font-mono">Build {typeof __APP_BUILD_TIME__ !== 'undefined' ? __APP_BUILD_TIME__ : 'Dev'}</span></footer>
      </div>
    </main>
  );
};
