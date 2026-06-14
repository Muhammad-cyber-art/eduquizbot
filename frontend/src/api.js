import axios from 'axios'

const API = axios.create({ baseURL: '/api' })

API.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

API.interceptors.response.use(r => r, err => {
  if (err.response?.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/admin/login'
  }
  return Promise.reject(err)
})

export const authAPI = {
  login: (username, password) => API.post('/auth/login', { username, password }),
  me: () => API.get('/auth/me'),
}
export const requestsAPI = {
  list: (f = 'all') => API.get('/requests', { params: { status_filter: f } }),
  approve: (id, limits = {}) => API.post(`/requests/${id}/approve`, null, { params: limits }),
  reject: id => API.post(`/requests/${id}/reject`),
}
export const usersAPI = {
  list: (p = {}) => API.get('/users', { params: p }),
  updateLimits: (id, limits) => API.put(`/users/${id}/limits`, limits),
}
export const analyticsAPI = {
  dashboard: () => API.get('/analytics/dashboard'),
  userGrowth: (days = 30) => API.get('/analytics/user-growth', { params: { days } }),
  activity: (days = 30) => API.get('/analytics/activity', { params: { days } }),
}
export default API
