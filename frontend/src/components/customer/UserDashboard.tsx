import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bot, Play, FolderOpen, Zap, MessageSquare, Plus, ArrowRight } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

export const UserDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-surface-0 overflow-y-auto">
      <div className="max-w-6xl mx-auto w-full p-8 space-y-8">
        
        {/* Greeting & Primary Input */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-semibold text-text tracking-tight">
              Good morning{user?.username ? `, ${user.username}` : ''}.
            </h1>
            <p className="text-secondary mt-1">What would you like to build today?</p>
          </div>
          
          <div className="relative max-w-2xl">
            <input 
              type="text" 
              placeholder="Ask SupremeAI to generate, analyze, or deploy..." 
              className="w-full bg-surface-1 border border-border rounded-xl pl-4 pr-12 py-4 text-text placeholder:text-muted focus:outline-none focus:border-accent-primary transition-colors shadow-sm"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  navigate('/workspace/live');
                }
              }}
            />
            <button className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-lg bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20 transition-colors">
              <ArrowRight size={16} />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-1 border border-border text-sm font-medium hover:surface-2 transition-colors">
              <Plus size={16} className="text-secondary" /> New Project
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-1 border border-border text-sm font-medium hover:surface-2 transition-colors">
              <Bot size={16} className="text-accent-primary" /> Generate App
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-1 border border-border text-sm font-medium hover:surface-2 transition-colors">
              <Zap size={16} className="text-emerald-400" /> Deploy Service
            </button>
          </div>
        </div>

        {/* Bento Grid layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          
          {/* Main Action Area (Span 8) */}
          <div className="md:col-span-8 space-y-6">
            
            {/* Continue Where You Left Off */}
            <section className="bg-surface-1 rounded-2xl p-6 border border-border">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium text-text">Continue Working</h2>
                <Link to="/projects" className="text-xs text-accent-primary hover:underline">View All</Link>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl surface-2 border border-border hover:border-accent-primary/30 cursor-pointer transition-colors group">
                  <div className="flex items-start justify-between mb-3">
                    <FolderOpen size={20} className="text-accent-primary" />
                    <span className="text-[10px] uppercase tracking-wider text-muted font-mono">2 hrs ago</span>
                  </div>
                  <h3 className="font-medium text-text group-hover:text-accent-primary transition-colors">Ecommerce NextJS Agent</h3>
                  <p className="text-xs text-secondary mt-1 line-clamp-2">Working on generating product catalog schema and API routes.</p>
                </div>
                <div className="p-4 rounded-xl surface-2 border border-border hover:border-accent-primary/30 cursor-pointer transition-colors group">
                  <div className="flex items-start justify-between mb-3">
                    <FolderOpen size={20} className="text-secondary" />
                    <span className="text-[10px] uppercase tracking-wider text-muted font-mono">Yesterday</span>
                  </div>
                  <h3 className="font-medium text-text group-hover:text-accent-primary transition-colors">Internal Analytics Dashboard</h3>
                  <p className="text-xs text-secondary mt-1 line-clamp-2">Data visualization components setup.</p>
                </div>
              </div>
            </section>

            {/* Recent Conversations */}
            <section className="bg-surface-1 rounded-2xl p-6 border border-border">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium text-text">Recent Conversations</h2>
                <Link to="/workspace/live" className="text-xs text-accent-primary hover:underline">Go to Studio</Link>
              </div>
              <div className="space-y-3">
                {[1, 2, 3].map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:surface-2 cursor-pointer transition-colors">
                    <MessageSquare size={16} className="text-secondary shrink-0" />
                    <div className="flex-1 truncate text-sm text-text">How to configure CI/CD pipeline for SupremeAI agent?</div>
                    <div className="text-[10px] text-muted font-mono shrink-0">Oct 24</div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Sidebar / Status Area (Span 4) */}
          <div className="md:col-span-4 space-y-6">
            
            {/* Active Agents */}
            <section className="bg-surface-1 rounded-2xl p-6 border border-border">
              <h2 className="text-sm font-medium text-text mb-4 uppercase tracking-widest text-muted">Active Agents</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Bot size={16} className="text-accent-primary" />
                      <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    </div>
                    <span className="text-sm font-medium text-text">Code Generator</span>
                  </div>
                  <span className="text-xs text-emerald-400 font-mono">Running</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Bot size={16} className="text-secondary" />
                    </div>
                    <span className="text-sm font-medium text-text">QA Tester</span>
                  </div>
                  <span className="text-xs text-muted font-mono">Idle</span>
                </div>
              </div>
            </section>

            {/* Usage Summary */}
            <section className="bg-surface-1 rounded-2xl p-6 border border-border">
              <h2 className="text-sm font-medium text-text mb-4 uppercase tracking-widest text-muted">Usage (Pro Plan)</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-secondary">GPT-4 Tokens</span>
                    <span className="text-text font-mono">42k / 100k</span>
                  </div>
                  <div className="w-full h-1.5 bg-surface-2 rounded-full overflow-hidden">
                    <div className="h-full bg-accent-primary w-[42%]"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-secondary">Agent Compute</span>
                    <span className="text-text font-mono">12h / 50h</span>
                  </div>
                  <div className="w-full h-1.5 bg-surface-2 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 w-[24%]"></div>
                  </div>
                </div>
              </div>
            </section>
            
          </div>
        </div>

      </div>
    </div>
  );
};
