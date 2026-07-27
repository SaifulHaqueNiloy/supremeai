import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { cn } from './cn';

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('removes undefined inputs', () => {
    expect(cn('foo', undefined, 'bar')).toBe('foo bar');
  });

  it('handles conditional classes with falsy values', () => {
    const active = true;
    const inactive = false;
    expect(cn('base', active && 'active', inactive && 'inactive')).toBe('base active');
  });

  it('merges tailwind conflicting classes', () => {
    expect(cn('p-4', 'p-2')).toBe('p-2');
  });
});
