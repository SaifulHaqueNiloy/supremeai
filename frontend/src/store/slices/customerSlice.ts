import type { StateCreator } from 'zustand';
import { getApiBaseUrl } from '../../utils/api';
import type { SupremeStore } from '../useSupremeStore';

export interface CustomerSlice {
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
});
