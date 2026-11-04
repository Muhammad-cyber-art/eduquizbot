import axios from 'axios'

const API = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '/api' })

API.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

API.interceptors.response.use(r => r, err => {
  if (err.response?.status === 401) {
    localStorage.removeItem('token')
    // Dispatch a custom event instead of hard-reloading the SPA
    window.dispatchEvent(new Event('auth-unauthorized'))
  } else if (err.response?.status >= 500) {
    // Dispatch generic server error event
    window.dispatchEvent(new CustomEvent('api-error', { detail: 'Server xatosi yuz berdi. Iltimos keyinroq urinib ko\'ring.' }))
  }
  return Promise.reject(err)
})

export const authAPI = {
  login: (username, password, config = {}) => API.post('/auth/login', { username, password }, config),
  me: (config = {}) => API.get('/auth/me', config),
}
export const requestsAPI = {
  list: (f = 'all', config = {}) => API.get('/requests', { params: { status_filter: f }, ...config }),
  approve: (id, limits = {}, config = {}) => API.post(`/requests/${id}/approve`, null, { params: limits, ...config }),
  reject: (id, config = {}) => API.post(`/requests/${id}/reject`, null, config),
}
export const usersAPI = {
  list: (p = {}, config = {}) => API.get('/users', { params: p, ...config }),
  updateLimits: (id, limits, config = {}) => API.put(`/users/${id}/limits`, limits, config),
}
export const analyticsAPI = {
  dashboard: (config = {}) => API.get('/analytics/dashboard', config),
  userGrowth: (days = 30, config = {}) => API.get('/analytics/user-growth', { params: { days }, ...config }),
  activity: (days = 30, config = {}) => API.get('/analytics/activity', { params: { days }, ...config }),
}
export default API
