import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QuickActionsPanel } from './QuickActionsPanel';
import { ToastContext } from '../../contexts/ToastContext';

// #2736: CustomEvent ('supremeai-notification') ছিল শ্রোতা-শূন্য dead-end —
// এখন আসল ToastProvider-চুক্তি (showToast) মক করে যাচাই।
const showToast = vi.fn();

const renderPanel = () =>
  render(
    <MemoryRouter>
      <ToastContext.Provider value={{ showToast }}>
        <QuickActionsPanel />
      </ToastContext.Provider>
    </MemoryRouter>
  );

describe('QuickActionsPanel', () => {
  beforeEach(() => {
    showToast.mockClear();
  });

  it('renders all 4 quick action items properly', () => {
    renderPanel();

    expect(screen.getByText('Trigger Self-Healer')).toBeInTheDocument();
    expect(screen.getByText('Evolve New Skill')).toBeInTheDocument();
    expect(screen.getByText('Browser Live Preview')).toBeInTheDocument();
    expect(screen.getByText('Deep Codebase Audit')).toBeInTheDocument();
  });

  it('shows a toast on Self-Healer click (real feedback, not a dead-end event)', () => {
    renderPanel();

    fireEvent.click(screen.getByText('Trigger Self-Healer'));
    expect(showToast).toHaveBeenCalledWith(
      'info',
      'Self-Healer Loop Triggered. All background connections healthy.'
    );
  });

  it('shows a toast on Gap-Miner click', () => {
    renderPanel();

    fireEvent.click(screen.getByText('Deep Codebase Audit'));
    expect(showToast).toHaveBeenCalledWith(
      'info',
      'Codebase Gap Audit running across 52 knowledge domains.'
    );
  });
});
