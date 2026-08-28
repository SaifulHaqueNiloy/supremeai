import { describe, it, expect } from 'vitest';
import {
  LEGACY_TO_UNIFIED_MAP,
  type LegacyStoreName,
  type UnifiedSliceName,
} from './migration_map';

describe('LEGACY_TO_UNIFIED_MAP', () => {
  it('maps the 12 legacy stores to unified slices', () => {
    expect(Object.keys(LEGACY_TO_UNIFIED_MAP)).toHaveLength(12);
  });

  it('maps useStore directly to the root unified store', () => {
    expect(LEGACY_TO_UNIFIED_MAP.useStore).toBe('root');
  });

  it('exposes the correct value type for a known key', () => {
    const key: LegacyStoreName = 'chatStore';
    const value: UnifiedSliceName = LEGACY_TO_UNIFIED_MAP[key];
    expect(value).toBe('chat');
  });
});
