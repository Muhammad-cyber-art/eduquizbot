import axios from 'axios';

const API_BASE = 'http://localhost:8001/api';

const api = axios.create({
  baseURL: API_BASE,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  me: () => api.get('/auth/me'),
};

export const requestsAPI = {
  list: (filter = 'all') => api.get('/requests', { params: { status_filter: filter } }),
  approve: (id) => api.post(`/requests/${id}/approve`),
  reject: (id) => api.post(`/requests/${id}/reject`),
};

export const usersAPI = {
  list: (params = {}) => api.get('/users', { params }),
};

export const analyticsAPI = {
  dashboard: () => api.get('/analytics/dashboard'),
  userGrowth: (days = 30) => api.get('/analytics/user-growth', { params: { days } }),
  activity: (days = 30) => api.get('/analytics/activity', { params: { days } }),
};

export default api;
