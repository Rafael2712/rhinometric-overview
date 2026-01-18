import { create } from 'zustand';

export const useAuthStore = create((set) => {
  // Initialize from localStorage
  const token = localStorage.getItem('jwt_token');
  
  return {
    token: token || null,
    isAuthenticated: !!token,
    setToken: (token) => {
      localStorage.setItem('jwt_token', token);
      set({ token, isAuthenticated: true });
    },
    clearToken: () => {
      localStorage.removeItem('jwt_token');
      set({ token: null, isAuthenticated: false });
    },
  };
});

export const useDashboardStore = create((set) => ({
  currentStep: 1,
  selectedTemplate: null,
  selectedDatasource: null,
  panels: [],
  layout: [],
  dashboardConfig: {
    title: '',
    description: '',
    tags: [],
    refresh: '30s',
    timeRange: { from: 'now-6h', to: 'now' },
  },
  
  setStep: (step) => set({ currentStep: step }),
  setTemplate: (template) => set({ selectedTemplate: template }),
  setDatasource: (datasource) => set({ selectedDatasource: datasource }),
  setPanels: (panels) => set({ panels }),
  setLayout: (layout) => set({ layout }),
  setConfig: (config) => set((state) => ({ 
    dashboardConfig: { ...state.dashboardConfig, ...config } 
  })),
  
  reset: () => set({
    currentStep: 1,
    selectedTemplate: null,
    selectedDatasource: null,
    panels: [],
    layout: [],
    dashboardConfig: {
      title: '',
      description: '',
      tags: [],
      refresh: '30s',
      timeRange: { from: 'now-6h', to: 'now' },
    },
  }),
}));

export const useHistoryStore = create((set) => {
  // Initialize from localStorage
  const stored = localStorage.getItem('dashboard-history');
  const dashboards = stored ? JSON.parse(stored) : [];
  
  return {
    dashboards,
    addDashboard: (dashboard) => set((state) => {
      const updated = [dashboard, ...state.dashboards].slice(0, 50);
      localStorage.setItem('dashboard-history', JSON.stringify(updated));
      return { dashboards: updated };
    }),
    clearHistory: () => {
      localStorage.removeItem('dashboard-history');
      return set({ dashboards: [] });
    },
  };
});
