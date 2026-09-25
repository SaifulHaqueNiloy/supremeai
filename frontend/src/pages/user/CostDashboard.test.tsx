/**
 * Tests for pages/user/CostDashboard — Cost dashboard page.
 */
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';

vi.mock('../../services/apiClient', () => ({
  apiClient: { get: vi.fn().mockResolvedValue({}) },
  ApiError: class extends Error { status = 400; },
}));

describe('CostDashboard', () => {
  it('renders without crash', async () => {
    const { default: CostDashboard } = await import('./CostDashboard');
    render(<CostDashboard />);
    expect(document.body).toBeDefined();
  });
});
