/**
 * Tests for pages/user/SkillCatalog — Skill catalog page.
 */
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';

vi.mock('../../services/apiClient', () => ({
  apiClient: { get: vi.fn().mockResolvedValue([]) },
  ApiError: class extends Error { status = 400; },
}));

describe('SkillCatalog', () => {
  it('renders without crash', async () => {
    const { default: SkillCatalog } = await import('./SkillCatalog');
    render(<SkillCatalog />);
    expect(document.body).toBeDefined();
  });
});
