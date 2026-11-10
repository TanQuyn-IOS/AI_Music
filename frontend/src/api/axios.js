import axios from 'axios'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Nếu request mang FormData, xóa Content-Type cố định để browser/Axios tự động sinh boundary phân tách multipart chuẩn
  if (config.data && (typeof FormData !== 'undefined' && config.data instanceof FormData)) {
    if (config.headers) {
      delete config.headers['Content-Type']
      delete config.headers['content-type']
      if (typeof config.headers.delete === 'function') {
        config.headers.delete('Content-Type')
        config.headers.delete('content-type')
      }
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const isAuthEndpoint = original?.url?.includes('/auth/login') ||
                           original?.url?.includes('/auth/register') ||
                           original?.url?.includes('/token/refresh')

    if (error.response?.status === 401 && !original?._retry && !isAuthEndpoint) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/token/refresh/`, { refresh })
          localStorage.setItem('access_token', data.access)
          original.headers.Authorization = `Bearer ${data.access}`
          return api(original)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          const protectedRoutes = ['/feed', '/upload', '/settings']
          const isProtectedRoute = protectedRoutes.some((p) => window.location.pathname.startsWith(p))
          if (isProtectedRoute && window.location.pathname !== '/login' && window.location.pathname !== '/register') {
            window.location.href = '/login'
          }
        }
      } else {
        localStorage.removeItem('access_token')
        const protectedRoutes = ['/feed', '/upload', '/settings']
        const isProtectedRoute = protectedRoutes.some((p) => window.location.pathname.startsWith(p))
        if (isProtectedRoute && window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
