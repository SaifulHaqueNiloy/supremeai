// ══════════════════════════════════════════════════════════════════════════════
// CI Dashboard — JOBS TAB
// (extracted verbatim from CIDashboard.tsx — mechanical split, no behavior change)
// ══════════════════════════════════════════════════════════════════════════════

import { Filter } from 'lucide-react';
import { JobRow } from '../cards';
import type { CISummaryData, JobResult } from '../types';

interface JobsTabProps {
  data: CISummaryData;
  onJobClick: (job: JobResult) => void;
}

export function JobsTab({ data, onJobClick }: JobsTabProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">
          All Jobs ({data.jobs.length})
        </h3>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select className="text-sm border border-gray-200 rounded-lg px-3 py-1.5">
            <option>All Status</option>
            <option>Passed Only</option>
            <option>Failed Only</option>
          </select>
        </div>
      </div>

      {data.jobs.map((job, idx) => (
        <JobRow
          key={idx}
          job={job}
          onClick={() => onJobClick(job)}
        />
      ))}
    </div>
  );
}
