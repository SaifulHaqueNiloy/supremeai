import { describe, expect, it } from 'vitest';
import { getNavigationForContext, getImplementedRoutePaths } from './navigationRegistry';

describe('canonical navigation registry', () => {
  it('keeps advanced operational routes out of the core user navigation', () => {
    const paths = getNavigationForContext('user')
      .flatMap((group) => group.items)
      .filter((item) => item.kind === 'route')
      .map((item) => item.path);

    expect(paths).toContain('/workspace');
    expect(paths).toContain('/integrations');
    expect(paths).not.toContain('/swarm');
    expect(paths).not.toContain('/evolution-forge');
    expect(paths).not.toContain('/architect-tower');
  });

  it('does not expose action-only admin entries as user navigation', () => {
    const userItems = getNavigationForContext('user').flatMap((group) => group.items);
    expect(userItems.every((item) => item.kind === 'route')).toBe(true);
  });

  it('only reports implemented route paths', () => {
    expect(getImplementedRoutePaths()).not.toContain('/swarm');
    expect(getImplementedRoutePaths()).toContain('/workspace');
  });
});
