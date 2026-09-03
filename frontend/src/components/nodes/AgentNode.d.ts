import type { FC } from 'react';

export interface AgentNodeData {
  label?: string;
  type?: string;
  health?: { status?: string; latency?: number };
  [key: string]: unknown;
}

export declare const AgentNode: FC<{ data: AgentNodeData }>;
