// apps/studio-client/src/pages/ProfilePage.tsx
// User Profile & Preferences Page
// বাংলা মন্তব্য: ব্যবহারকারীর প্রোফাইল, সিকিউরিটি সেটিন্স ও এআই অপশন সেটিংস পেজ।

import React, { useState } from 'react';
import { User, Shield, Key, Bell, Check, Lock } from 'lucide-react';
import { NavRail } from '../components/layout/NavRail';

export const ProfilePage: React.FC = () => {
  const [saved, setSaved] = useState(false);
  const [name, setName] = useState('Supreme Developer');
  const [email, setEmail] = useState('developer@supremeai.io');
  const [preferredModel, setPreferredModel] = useState('DeepSeek-V3');
  const [jitOtpEnabled, setJitOtpEnabled] = useState(true);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 overflow-hidden">
      <NavRail />
      <main className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto">
        <header className="mb-8">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400">
              <User className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">User Profile & Preferences</h1>
              <p className="text-sm text-slate-400">Manage your identity, AI model defaults, and security shield settings</p>
            </div>
          </div>
        </header>

        <div className="space-y-6">
          {/* Identity Section */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2 text-slate-200">
              <User className="h-5 w-5 text-cyan-400" /> Account Identity
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>
          </div>

          {/* AI Preferences */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2 text-slate-200">
              <Key className="h-5 w-5 text-cyan-400" /> Default AI Model Preferences
            </h2>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Preferred Code Engine</label>
              <select
                value={preferredModel}
                onChange={(e) => setPreferredModel(e.target.value)}
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="DeepSeek-V3">DeepSeek-V3 (Coding & Math Specialist)</option>
                <option value="Kimi-K2.5">Moonshot Kimi K2.5 (Bangla & Complex Reasoning)</option>
                <option value="Together-Fallback">Together AI (Auto-Fallback)</option>
              </select>
            </div>
          </div>

          {/* Security Shield */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2 text-slate-200">
              <Shield className="h-5 w-5 text-emerald-400" /> Malware Immunity & JIT OTP Defense
            </h2>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-200">Just-In-Time (JIT) OTP Enforcement</p>
                <p className="text-xs text-slate-400">Require single-use OTP verification before executing high-privilege actions.</p>
              </div>
              <button
                onClick={() => setJitOtpEnabled(!jitOtpEnabled)}
                className={`w-12 h-6 rounded-full transition-colors relative ${
                  jitOtpEnabled ? 'bg-cyan-500' : 'bg-slate-800'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-transform ${
                    jitOtpEnabled ? 'right-0.5' : 'left-0.5'
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Action Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-cyan-500/20"
            >
              {saved ? <Check className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
              {saved ? 'Saved Successfully!' : 'Save Preferences'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ProfilePage;
