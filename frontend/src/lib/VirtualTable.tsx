import React from 'react';
import { useVirtualList } from './useVirtualList';

/**
 * Virtual table that only renders visible rows for large datasets.
 * Suitable for tables with 50+ rows.
 * 
 * @param props - Table props
 * @param props.data - Array of row data
 * @param props.columns - Column definitions
 * @param props.rowHeight - Height of each row (default 40)
 * @param props.className - Optional CSS class
 */
interface VirtualTableProps {
  data: any[];
  columns: { key: string; label: string; className?: string }[];
  rowHeight?: number;
  className?: string;
}

export const VirtualTable: React.FC<VirtualTableProps> = ({
  data,
  columns,
  rowHeight = 40,
  className,
}) => {
  const { containerRef, visibleStart, visibleEnd, totalHeight } = useVirtualList(
    data,
    rowHeight,
    600 // default viewport height
  );

  return (
    <div
      ref={containerRef}
      style={className ? { ...style, ...className } : style}
      style={{
        height: '600px',
        overflow: 'auto',
        width: '100%',
        position: 'relative',
      }}
    >
      {/* Total height indicator for accessibility */}
      <div style={{ height: totalHeight, width: '1px' }} aria-hidden="true" />

      {/* Header row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: columns.map(() => 'auto').join(', '),
          backgroundColor: '#18181b',
          color: '#fff',
          padding: '8px 12px',
          fontWeight: '600',
          fontSize: '12px',
          lineHeight: '1.5',
        }}
      >
        {columns.map((col) => (
          <div key={col.key} style={{ minWidth: '120px' }}>
            {col.label}
          </div>
        ))}
      </div>

      {/* Visible rows */}
      {data.slice(visibleStart, visibleEnd).map((row, index) => {
        const actualIndex = visibleStart + index;
        const rowStyle: React.CSSProperties = {
          display: 'grid',
          gridTemplateColumns: columns.map(() => 'auto').join(', '),
          backgroundColor: actualIndex % 2 === 0 ? '#27272a' : '#18181b',
          color: '#fafafa',
          padding: '8px 12px',
          fontSize: '14px',
          lineHeight: '1.5',
        };

        return (
          <div
            key={actualIndex}
            style={rowStyle}
            style={{ minHeight: `${rowHeight}px` }}
          >
            {columns.map((col) => (
              <div key={col.key} style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {row[col.key] ?? ''}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
};

/* eslint-disable @typescript-eslint/no-unused-vars */
const style: React.CSSProperties = {};
/* eslint-enable @typescript-eslint/no-unused-vars */