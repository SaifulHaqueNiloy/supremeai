import { expect, vi } from 'vitest';
import { matchers } from '@testing-library/jest-dom';

// Extend Vitest's expect with Jest-DOM matchers
expect.extend(matchers);