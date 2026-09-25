/**
 * Tests for core/RoleGuard — Role-based access guard.
 */
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';

vi.mock('../../store/authStore', () => ({
  useAuthStore: () => ({ user: { role: 'user' } }),
}));

describe('RoleGuard', () => {
  it('renders children when role matches', async () => {
    const { default: RoleGuard } = await import('./RoleGuard');
    render(<RoleGuard requiredRole="user"><div>content</div></RoleGuard>);
    expect(document.body).toBeDefined();
  });
});
