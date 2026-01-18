import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('jwt_token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// === API Methods ===

export const apiService = {
  // Health Check
  getStatus: async () => {
    const response = await api.get('/');
    return response.data;
  },

  // Templates
  getTemplates: async () => {
    const response = await api.get('/api/v1/templates');
    return response.data.templates || response.data;
  },

  // Datasources
  getDatasources: async () => {
    const response = await api.get('/api/v1/datasources');
    return response.data.datasources || response.data;
  },

  // Query Builder
  getMetrics: async () => {
    const response = await api.get('/api/v1/query/metrics');
    return response.data.metrics || response.data;
  },

  buildQuery: async (queryRequest) => {
    const response = await api.post('/api/v1/query/build', queryRequest);
    return response.data;
  },

  validateQuery: async (query) => {
    const response = await api.post('/api/v1/query/validate', { query });
    return response.data;
  },

  // Dashboards
  createDashboard: async (dashboardRequest) => {
    const response = await api.post('/api/v1/dashboards', dashboardRequest);
    return response.data;
  },

  getDashboards: async () => {
    const response = await api.get('/api/v1/dashboards');
    return response.data.dashboards || response.data;
  },

  getDashboard: async (uid) => {
    const response = await api.get(`/api/v1/dashboards/${uid}`);
    return response.data;
  },

  deleteDashboard: async (uid) => {
    const response = await api.delete(`/api/v1/dashboards/${uid}`);
    return response.data;
  },
};

export default api;
