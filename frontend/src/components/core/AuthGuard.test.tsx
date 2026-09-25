/**
 * Tests for core/AuthGuard — Authentication guard component.
 */
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';

vi.mock('../../store/authStore', () => ({
  useAuthStore: () => ({ isAuthenticated: false, user: null }),
}));

describe('AuthGuard', () => {
  it('renders without crash', async () => {
    const { default: AuthGuard } = await import('./AuthGuard');
    render(<AuthGuard><div>protected</div></AuthGuard>);
    expect(document.body).toBeDefined();
  });
});
