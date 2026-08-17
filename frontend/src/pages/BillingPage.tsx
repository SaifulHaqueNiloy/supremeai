// apps/studio-client/src/pages/BillingPage.tsx
// Subscription & Token Billing Page
// বাংলা মন্তব্য: বিলিং ও সাবস্ক্রিপশন ব্যবস্থাপনা পেজ — সম্পূর্ণ ফ্রি-টিয়ার এবং অন-ডিমান্ড টোকেন প্ল্যান।

import React from 'react';
import { Zap, CheckCircle2, ShieldCheck, CreditCard } from 'lucide-react';
import { NavRail } from '../components/layout/NavRail';

export const BillingPage: React.FC = () => {
  const plans = [
    {
      name: 'Zero-Cost Free Tier',
      price: '$0',
      period: 'forever',
      description: 'Ideal for solo developers utilizing free AI provider quotas.',
      features: [
        '500 Free AI Executions / day',
        'Access to SupremeAI Deep & SupremeAI Reason',
        'Standard Rate Limiting (60 req/min)',
        'Community Discord Support',
      ],
      current: true,
      buttonText: 'Current Plan',
    },
    {
      name: 'Pro Autonomous Agent',
      price: '$19',
      period: 'per month',
      description: 'For power users needing multi-agent swarm orchestration.',
      features: [
        'Unlimited AI Swarm Executions',
        'Priority LiteLLM Smart Routing',
        'High-speed JIT OTP Security Shield',
        'Dedicated 24/7 Support Escalation',
      ],
      current: false,
      buttonText: 'Upgrade to Pro',
    },
  ];

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 overflow-hidden">
      <NavRail />
      <main className="flex-1 overflow-y-auto p-8 max-w-6xl mx-auto">
        <header className="mb-10">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400">
              <Zap className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Billing & Subscriptions</h1>
              <p className="text-sm text-slate-400">Manage your subscription, usage quotas, and payment gateways</p>
            </div>
          </div>
        </header>

        {/* Pricing Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-2xl border p-8 flex flex-col justify-between transition-all ${
                plan.current
                  ? 'border-cyan-500/50 bg-slate-900/80 shadow-xl shadow-cyan-500/10'
                  : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-slate-200">{plan.name}</h2>
                  {plan.current && (
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                      Active
                    </span>
                  )}
                </div>
                <div className="flex items-baseline gap-1 mb-4">
                  <span className="text-4xl font-extrabold">{plan.price}</span>
                  <span className="text-sm text-slate-400">/{plan.period}</span>
                </div>
                <p className="text-sm text-slate-400 mb-6">{plan.description}</p>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-3 text-sm text-slate-300">
                      <CheckCircle2 className="h-4 w-4 text-cyan-400" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <button
                className={`w-full py-3 px-4 rounded-xl font-semibold text-sm transition-all ${
                  plan.current
                    ? 'bg-slate-800 text-slate-400 cursor-default border border-slate-700'
                    : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/25'
                }`}
              >
                {plan.buttonText}
              </button>
            </div>
          ))}
        </div>

        {/* Security & Gateways Info */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <ShieldCheck className="h-8 w-8 text-emerald-400" />
            <div>
              <h3 className="font-semibold text-slate-200">Zero-Cost Free Tier Guarantee</h3>
              <p className="text-xs text-slate-400">All basic workloads are routed automatically through free-tier providers.</p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-slate-400 text-xs">
            <CreditCard className="h-4 w-4" /> SSLCommerz & Stripe Verified
          </div>
        </div>
      </main>
    </div>
  );
};

export default BillingPage;
