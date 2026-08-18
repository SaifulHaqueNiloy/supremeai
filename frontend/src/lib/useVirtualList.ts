import { useEffect, useRef } from 'react';

/**
 * Virtual list hook for efficient rendering of large datasets.
 * Only renders what's visible in the viewport.
 * 
 * @param items - Array of items to render
 * @param itemHeight - Height of each item in pixels
 * @param viewportHeight - Visible area height in pixels
 * @returns Object with visible range and ref to attach to container
 */
export function useVirtualList(
  items: any[],
  itemHeight: number = 40,
  viewportHeight: number = 600
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const visibleStartRef = useRef(0);
  const visibleEndRef = useRef(0);

  const visibleStart = Math.max(0, visibleStartRef.current);
  const visibleEnd = Math.min(items.length, visibleEndRef.current);

  // Calculate visible range based on container height
  useEffect(() => {
    if (containerRef.current) {
      const containerHeight = containerRef.current.clientHeight;
      const scrollTop = containerRef.current.scrollTop;

      // Calculate visible range
      visibleStartRef.current = Math.max(0, Math.floor(scrollTop / itemHeight) - 1);
      visibleEndRef.current = Math.min(
        items.length,
        Math.ceil((scrollTop + containerHeight) / itemHeight) + 1
      );
    }
  }, [items.length, itemHeight, viewportHeight]);

  return {
    containerRef,
    visibleStart,
    visibleEnd,
    totalHeight: items.length * itemHeight,
  };
}