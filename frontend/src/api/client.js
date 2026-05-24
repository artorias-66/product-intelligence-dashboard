import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Separate client for file uploads — longer timeout
const uploadClient = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 120000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const dashboardApi = {
  getQualitySummary: () => api.get('/dashboard/quality-summary'),
};

export const productsApi = {
  getAll: (params) => api.get('/products', { params }),
  getById: (skuId) => api.get(`/products/${skuId}`),
  getIssues: (skuId) => api.get(`/products/${skuId}/issues`),
  enhanceTitle: (skuId) => api.post(`/products/${skuId}/enhance-title`),
  getCompetitorPrices: (skuId) => api.get(`/products/${skuId}/competitor-prices`),
  getRecommendations: (skuId) => api.get(`/products/${skuId}/recommendations`),
};

export const jobsApi = {
  getAll: (params) => api.get('/jobs', { params }),
  getById: (jobId) => api.get(`/jobs/${jobId}`),
  approve: (jobId, data) => api.post(`/jobs/${jobId}/approve`, data),
  retry: (jobId) => api.post(`/jobs/${jobId}/retry`),
};

export const uploadApi = {
  uploadVideo: (formData) =>
    uploadClient.post('/upload-video', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  uploadCsv: (formData) =>
    uploadClient.post('/upload-products-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

export const alertsApi = {
  getAll: (params) => api.get('/alerts', { params }),
  markRead: (id) => api.put(`/alerts/${id}/read`),
};

export const competitorApi = {
  getForProduct: (skuId) => api.get(`/competitor-prices/product/${skuId}`),
  getPriceHistory: (skuId) => api.get(`/competitor-prices/product/${skuId}/history`),
  uploadCsv: (formData) =>
    api.post('/competitor-prices/upload-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  refresh: () => api.post('/competitor-prices/refresh'),
  refreshForProduct: (skuId) => api.post(`/competitor-prices/product/${skuId}/refresh`),
};

export const seedApi = {
  seed: () => api.post('/seed'),
};

export default api;
