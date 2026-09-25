/**
 * Tests for chat/ChatInterface — Main chat interface.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock child components
vi.mock('./UnifiedChatBubble', () => ({ default: () => <div data-testid="bubble" /> }));
vi.mock('./ThinkingPanel', () => ({ default: () => <div data-testid="thinking" /> }));

describe('ChatInterface', () => {
  it('renders without crash', async () => {
    const { default: ChatInterface } = await import('./ChatInterface');
    render(<ChatInterface />);
    expect(document.body).toBeDefined();
  });
});
