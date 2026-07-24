// apps/studio-client/src/pages/ErrorPage.tsx
// Branded Error 404 & 500 Component
// বাংলা মন্তব্য: সুপ্রিম ব্র্যান্ডিং সম্বলিত ইউজার ফ্রেন্ডলি ৪০৪ ও ৫০০ এরর পেজ।

import React from 'react';
import { AlertTriangle, Home, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ErrorPageProps {
  code?: 404 | 500;
  message?: string;
}

export const ErrorPage: React.FC<ErrorPageProps> = ({
  code = 404,
  message = code === 404 ? 'The workspace route you are looking for does not exist or has been moved.' : 'An internal core system exception occurred. The autonomous self-healing loop has been notified.',
}) => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen w-full bg-slate-950 text-slate-100 p-6 text-center select-none">
      <div className="relative mb-6">
        <div className="h-24 w-24 rounded-3xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-2xl shadow-cyan-500/20">
          <AlertTriangle className="h-12 w-12" />
        </div>
        <span className="absolute -bottom-2 -right-2 px-2.5 py-0.5 rounded-full bg-red-950 border border-red-500/40 text-red-400 text-xs font-mono font-bold">
          {code}
        </span>
      </div>

      <h1 className="text-3xl font-extrabold tracking-tight mb-2 text-slate-100">
        {code === 404 ? 'Page Not Found' : 'Autonomous Core Exception'}
      </h1>
      <p className="max-w-md text-sm text-slate-400 mb-8 leading-relaxed">
        {message}
      </p>

      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 font-medium text-sm transition-colors"
        >
          <Home className="h-4 w-4 text-cyan-400" /> Return Home
        </button>
        <button
          onClick={() => window.location.reload()}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition-colors shadow-lg shadow-cyan-500/20"
        >
          <RefreshCw className="h-4 w-4" /> Retry Connection
        </button>
      </div>
    </div>
  );
};

export default ErrorPage;
