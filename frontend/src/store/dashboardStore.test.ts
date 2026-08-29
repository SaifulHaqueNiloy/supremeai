import { describe, it, expect, beforeEach } from 'vitest';
import { useDashboardStore } from './dashboardStore';

describe('dashboardStore', () => {
  beforeEach(() => {
    useDashboardStore.setState({
      isDeploymentModalOpen: false,
      systemStatus: 'healthy',
      activePanel: null,
      dashboardMode: 'simple',
      chatTabTerminalOpen: true,
      chatTabBrowserOpen: true,
    });
  });

  it('sets the deployment modal open state', () => {
    useDashboardStore.getState().setDeploymentModal(true);
    expect(useDashboardStore.getState().isDeploymentModalOpen).toBe(true);
    useDashboardStore.getState().setDeploymentModal(false);
    expect(useDashboardStore.getState().isDeploymentModalOpen).toBe(false);
  });

  it('updates the system status', () => {
    useDashboardStore.getState().updateSystemStatus('critical');
    expect(useDashboardStore.getState().systemStatus).toBe('critical');
  });

  it('sets the active panel', () => {
    useDashboardStore.getState().setActivePanel('logs');
    expect(useDashboardStore.getState().activePanel).toBe('logs');
    useDashboardStore.getState().setActivePanel(null);
    expect(useDashboardStore.getState().activePanel).toBeNull();
  });

  it('toggles the dashboard mode between simple and advanced', () => {
    expect(useDashboardStore.getState().dashboardMode).toBe('simple');
    useDashboardStore.getState().toggleDashboardMode();
    expect(useDashboardStore.getState().dashboardMode).toBe('advanced');
    useDashboardStore.getState().toggleDashboardMode();
    expect(useDashboardStore.getState().dashboardMode).toBe('simple');
  });

  it('toggles the terminal and browser chat tabs', () => {
    useDashboardStore.getState().toggleTerminal();
    expect(useDashboardStore.getState().chatTabTerminalOpen).toBe(false);
    useDashboardStore.getState().toggleBrowser();
    expect(useDashboardStore.getState().chatTabBrowserOpen).toBe(false);
    useDashboardStore.getState().toggleTerminal();
    expect(useDashboardStore.getState().chatTabTerminalOpen).toBe(true);
  });
});
