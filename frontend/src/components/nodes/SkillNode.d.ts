import type { FC } from 'react';

export interface SkillNodeData {
  label?: string;
  type?: string;
  health?: { status?: string; latency?: number };
  [key: string]: unknown;
}

export declare const SkillNode: FC<{ data: SkillNodeData }>;
