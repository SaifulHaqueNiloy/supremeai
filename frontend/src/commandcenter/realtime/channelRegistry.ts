import { cmdKeys } from '../data/hooks';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Command Center — Channel Registry
// বাংলা মন্তব্য: WS/SSE চ্যানেল → React Query key ম্যাপিং — Ripple-Effect Guard
// ═══════════════════════════════════════════════════════════════════════════

export type ChannelName =
  | 'metrics.update'
  | 'providers.update'
  | 'jobs.status'
  | 'health.update'
  | 'alerts.emergency'
  | 'audit.event'
  | 'traffic.update'
  | 'deploy.status';

export interface ChannelMapping {
  channel: ChannelName;
  queryKey: readonly unknown[];
  /** How to merge incoming payload with existing cache data */
  merge: 'replace' | 'patch' | 'append';
}

// একক সত্য — WS চ্যানেল → React Query key
export const CHANNEL_REGISTRY: ChannelMapping[] = [
  { channel: 'metrics.update', queryKey: cmdKeys.metrics, merge: 'replace' },
  { channel: 'providers.update', queryKey: cmdKeys.providers, merge: 'replace' },
  { channel: 'jobs.status', queryKey: cmdKeys.ci, merge: 'append' },
  { channel: 'health.update', queryKey: cmdKeys.health, merge: 'replace' },
  { channel: 'alerts.emergency', queryKey: cmdKeys.events, merge: 'append' },
  { channel: 'audit.event', queryKey: cmdKeys.audit, merge: 'append' },
  { channel: 'traffic.update', queryKey: cmdKeys.traffic, merge: 'replace' },
  { channel: 'deploy.status', queryKey: cmdKeys.deploy, merge: 'replace' },
];

export function getChannelMapping(channel: string): ChannelMapping | undefined {
  return CHANNEL_REGISTRY.find((m) => m.channel === channel);
}

export function getQueryKeyForChannel(channel: string): readonly unknown[] | undefined {
  return getChannelMapping(channel)?.queryKey;
}