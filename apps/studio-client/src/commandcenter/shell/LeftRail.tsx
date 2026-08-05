import React from 'react';
import {
  LayoutDashboard,
  Bot,
  Network,
  ListTodo,
  Users,
  Building2,
  Route,
  Server,
  Puzzle,
  Book,
  Activity,
  FileText,
  Radio,
  Rocket,
  HeartPulse,
  Gauge,
  Shield,
  ScrollText,
  Inbox,
  Scale,
  KeyRound,
  Ban,
  DollarSign,
  Receipt,
  PiggyBank,
  TrendingUp,
  SlidersHorizontal,
  Settings,
  FolderKanban,
  DatabaseBackup,
  Lock,
} from 'lucide-react';
import type { CommandModuleId } from '../data/types';
import { useCommandCenterStore } from '../state/useCommandCenterStore';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Command Center — Left Rail Navigation
// বাংলা মন্তব্য: গ্রুপড নেভিগেশন রেইল — DECK/OPERATE/BUILD/OBSERVE/SECURE/MONEY/SYSTEM
// ═══════════════════════════════════════════════════════════════════════════

interface RailItem {
  id: string;
  label: string;
  module: string;
  icon: React.ReactNode;
  badge?: number;
}

interface RailGroup {
  title: string;
  items: RailItem[];
}

interface LeftRailProps {
  badges?: Partial<Record<string, number>>;
}

export function LeftRail({ badges = {} }: LeftRailProps) {
  const { activeModule, setActiveModule } = useCommandCenterStore();

  const groups: RailGroup[] = [
    {
      title: 'DECK',
      items: [
        { id: 'deck', label: 'কমান্ড ডেক', module: 'deck', icon: <LayoutDashboard size={14} /> },
      ],
    },
    {
      title: 'OPERATE',
      items: [
        { id: 'agents', label: 'এজেন্ট', module: 'agents', icon: <Bot size={14} /> },
        { id: 'swarm', label: 'সোয়ার্ম', module: 'swarm', icon: <Network size={14} /> },
        { id: 'tasks', label: 'টাস্ক ও কিউ', module: 'tasks', icon: <ListTodo size={14} /> },
        { id: 'sessions', label: 'সেশন', module: 'sessions', icon: <Users size={14} /> },
        { id: 'tenants', label: 'টেন্যান্ট', module: 'tenants', icon: <Building2 size={14} /> },
      ],
    },
    {
      title: 'BUILD',
      items: [
        { id: 'router', label: 'মডেল রাউটার', module: 'router', icon: <Route size={14} /> },
        { id: 'providers', label: 'প্রোভাইডার', module: 'providers', icon: <Server size={14} /> },
        { id: 'skills', label: 'স্কিল', module: 'skills', icon: <Puzzle size={14} /> },
        { id: 'memory', label: 'মেমোরি ও নলেজ', module: 'memory', icon: <Book size={14} /> },
      ],
    },
    {
      title: 'OBSERVE',
      items: [
        { id: 'metrics', label: 'লাইভ মেট্রিক্স', module: 'metrics', icon: <Gauge size={14} /> },
        { id: 'logs', label: 'লগ', module: 'logs', icon: <FileText size={14} /> },
        { id: 'events', label: 'ইভেন্ট', module: 'events', icon: <Radio size={14} /> },
        { id: 'ci', label: 'CI/CD', module: 'ci', icon: <Rocket size={14} /> },
        { id: 'health', label: 'হেলথ ম্যাপ', module: 'health', icon: <HeartPulse size={14} /> },
        { id: 'traffic', label: 'ট্রাফিক', module: 'traffic', icon: <Activity size={14} /> },
      ],
    },
    {
      title: 'SECURE',
      items: [
        { id: 'threats', label: 'থ্রেট', module: 'threats', icon: <Shield size={14} /> },
        { id: 'audit', label: 'অডিট এক্সপ্লোরার', module: 'audit', icon: <ScrollText size={14} /> },
        { id: 'approvals', label: 'অ্যাপ্রুভাল কিউ', module: 'approvals', icon: <Inbox size={14} />, badge: badges.approvals },
        { id: 'rules', label: 'রুলস ও পলিসি', module: 'rules', icon: <Scale size={14} /> },
        { id: 'secrets', label: 'সিক্রেটস হেলথ', module: 'secrets', icon: <KeyRound size={14} /> },
        { id: 'ratelimits', label: 'রেট লিমিট', module: 'ratelimits', icon: <Ban size={14} /> },
      ],
    },
    {
      title: 'MONEY',
      items: [
        { id: 'cost', label: 'কস্ট অডিটর', module: 'cost', icon: <DollarSign size={14} /> },
        { id: 'usage', label: 'ইউসেজ ও বিলিং', module: 'usage', icon: <Receipt size={14} /> },
        { id: 'budget', label: 'বাজেট ক্যাপ', module: 'budget', icon: <PiggyBank size={14} /> },
        { id: 'roi', label: 'ROI সেভিংস', module: 'roi', icon: <TrendingUp size={14} /> },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { id: 'config', label: 'কনফিগ এডিটর', module: 'config', icon: <SlidersHorizontal size={14} /> },
        { id: 'flags', label: 'ফিচার ফ্ল্যাগ', module: 'flags', icon: <Settings size={14} /> },
        { id: 'workspaces', label: 'ওয়ার্কস্পেস', module: 'workspaces', icon: <FolderKanban size={14} /> },
        { id: 'backups', label: 'ব্যাকআপ', module: 'backups', icon: <DatabaseBackup size={14} /> },
        { id: 'deploy', label: 'ডিপ্লয় ও গেট', module: 'deploy', icon: <Lock size={14} /> },
      ],
    },
  ];

  return (
    <nav className="w-52 border-r border-[var(--sa-line)] bg-[var(--sa-bg-1)] overflow-y-auto py-3">
      {groups.map((group) => (
        <div key={group.title} className="mb-4">
          <div className="px-3 mb-1 text-[8px] font-mono font-bold tracking-widest text-[var(--sa-text-2)]">
            {group.title}
          </div>
          {group.items.map((item) => {
            const isActive = activeModule === item.module;
            return (
              <button
                key={item.id}
                onClick={() => setActiveModule(item.module as never)}
                className={`w-full flex items-center gap-2.5 px-3 py-1.5 text-left transition-colors ${
                  isActive
                    ? 'bg-[#00f3ff]/10 text-[#00f3ff] border-r-2 border-[#00f3ff]'
                    : 'text-[var(--sa-text-1)] hover:bg-[var(--sa-bg-2)] hover:text-[var(--sa-text-0)]'
                }`}
              >
                <span className={isActive ? 'text-[#00f3ff]' : 'text-[var(--sa-text-2)]'}>{item.icon}</span>
                <span className="text-[10px] font-mono flex-1">{item.label}</span>
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="text-[8px] font-mono px-1.5 py-0.5 rounded-full bg-[#ef4444]/20 text-[#ef4444]">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      ))}
    </nav>
  );
}