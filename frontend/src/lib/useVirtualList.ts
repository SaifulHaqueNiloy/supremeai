import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Virtual list hook for efficient rendering of large datasets.
 * Only renders what's visible in the viewport.
 * 
 * @param items - Array of items to render
 * @param itemHeight - Height of each item in pixels
 * @param viewportHeight - Visible area height in pixels
 * @returns Object with visible range and ref to attach to container
 */
export function useVirtualList<T = unknown>(
  items: T[],
  itemHeight: number = 40,
  viewportHeight: number = 600
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);

  const handleScroll = useCallback(() => {
    if (containerRef.current) {
      setScrollTop(containerRef.current.scrollTop);
    }
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      el.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll]);

  const visibleStart = Math.max(0, Math.floor(scrollTop / itemHeight) - 1);
  const visibleEnd = Math.min(
    items.length,
    Math.ceil((scrollTop + viewportHeight) / itemHeight) + 1
  );

  return {
    containerRef,
    visibleStart,
    visibleEnd,
    totalHeight: items.length * itemHeight,
  };
}