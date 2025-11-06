import axios from 'axios'

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    console.error('API Error:', message)
    throw new Error(message)
  }
)

// Overview API
export const overviewAPI = {
  getStats: () => api.get('/overview/stats'),
}

// Authors API
export const authorsAPI = {
  getStatistics: (params) => api.get('/authors/statistics', { params }),
  getTopContributors: (params) => api.get('/authors/top-contributors', { params }),
}

// Commits API
export const commitsAPI = {
  getCommits: (params) => api.get('/commits/', { params }),
  getTopByLines: (params) => api.get('/commits/top-by-lines', { params }),
}

// Pull Requests API
export const pullRequestsAPI = {
  getPullRequests: (params) => api.get('/pull-requests/', { params }),
  getTopApprovers: (params) => api.get('/pull-requests/top-approvers', { params }),
}

// Staff API
export const staffAPI = {
  getStaffList: (params) => api.get('/staff/', { params }),
}

// Mappings API
export const mappingsAPI = {
  getMappings: () => api.get('/mappings/'),
  createMapping: (data) => api.post('/mappings/', data),
  deleteMapping: (authorName) => api.delete(`/mappings/${encodeURIComponent(authorName)}`),
  getUnmappedAuthors: () => api.get('/mappings/unmapped-authors'),
}

// Tables API
export const tablesAPI = {
  getTableInfo: () => api.get('/tables/info'),
  getTableData: (tableName, params) => api.get(`/tables/${tableName}/data`, { params }),
}

// SQL Executor API
export const sqlAPI = {
  execute: (query) => api.post('/sql/execute', { query }),
  generateQuery: (prompt) => api.post('/sql/generate-query', { prompt }),
}

export default api
