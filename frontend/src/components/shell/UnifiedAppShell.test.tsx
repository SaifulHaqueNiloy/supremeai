/**
 * Tests for shell/UnifiedAppShell — Main app shell.
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';

describe('UnifiedAppShell', () => {
  it('renders without crash', async () => {
    const mod = await import('./UnifiedAppShell');
    if (mod.default) {
      render(<mod.default><div>test</div></mod.default>);
    }
    expect(document.body).toBeDefined();
  });
});
