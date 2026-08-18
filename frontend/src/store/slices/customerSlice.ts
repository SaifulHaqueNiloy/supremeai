import type { StateCreator } from 'zustand';
import { getApiBaseUrl } from '../../utils/api';
import type { SupremeStore } from '../useSupremeStore';
import type { Project, Widget, ChatMessage, UserProfile } from '../../types/customer';

export interface CustomerSlice {
  // Admin CRM customer management
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  customers: any[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  selectedCustomer: any | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  addCustomer: (customer: any) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  updateCustomer: (customerId: string, customer: any) => void;
  removeCustomer: (customerId: string) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  selectCustomer: (customer: any) => void;
  fetchCustomers: () => Promise<void>;

  // Customer Portal state
  projects: Project[];
  activeProjectId: string | null;
  customerChatHistory: ChatMessage[];
  widgets: Widget[];
  sidebarCollapsed: boolean;
  hydrated: boolean;
  setProjects: (projects: Project[]) => void;
  setActiveProject: (id: string | null) => void;
  addMessage: (message: ChatMessage) => void;
  addCustomerMessage: (message: ChatMessage) => void;
  clearChat: () => void;
  clearCustomerChat: () => void;
  toggleSidebar: () => void;
  reorderWidgets: (widgets: Widget[]) => void;
  setHydrated: (val: boolean) => void;
  setCustomerUser: (user: UserProfile | null) => void;
}

export const createCustomerSlice: StateCreator<SupremeStore, [], [], CustomerSlice> = (set) => ({
  customers: [],
  selectedCustomer: null,
  addCustomer: (customer) => set((state) => ({ customers: [...state.customers, customer] })),
  updateCustomer: (customerId, customer) =>
    set((state) => ({
      customers: state.customers.map((c) => (c.id === customerId ? { ...c, ...customer } : c)),
    })),
  removeCustomer: (customerId) =>
    set((state) => ({ customers: state.customers.filter((c) => c.id !== customerId) })),
  selectCustomer: (customer) => set({ selectedCustomer: customer }),
  fetchCustomers: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${getApiBaseUrl()}/admin-api/customers`);
      const customers = await response.json();
      set({ customers });
    } catch {
      set({ error: 'Failed to fetch customers' });
    } finally {
      set({ loading: false });
    }
  },

  projects: [],
  activeProjectId: null,
  customerChatHistory: [],
  widgets: [],
  sidebarCollapsed: false,
  hydrated: false,
  setProjects: (projects) => set({ projects }),
  setActiveProject: (id) => set({ activeProjectId: id }),
  addMessage: (message) =>
    set((state) => ({
      customerChatHistory: [...state.customerChatHistory, message],
    })),
  addCustomerMessage: (message) =>
    set((state) => ({
      customerChatHistory: [...state.customerChatHistory, message],
    })),
  clearChat: () => set({ customerChatHistory: [] }),
  clearCustomerChat: () => set({ customerChatHistory: [] }),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  reorderWidgets: (widgets) => set({ widgets }),
  setHydrated: (val) => set({ hydrated: val }),
  setCustomerUser: (user) =>
    set({ user: user ? ({ id: user.id, name: user.username, email: user.email, role: user.role } as unknown as SupremeStore['user']) : null }),
});
