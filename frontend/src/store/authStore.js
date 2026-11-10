import { create } from 'zustand'
import api from '../api/axios'

const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  loading: true,

  login: async (username, password) => {
    const { data } = await api.post('/auth/login/', { username, password })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    set({ user: data.user, isAuthenticated: true })
    return data.user
  },

  register: async (formData) => {
    const { data } = await api.post('/auth/register/', formData)
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    set({ user: data.user, isAuthenticated: true })
    return data.user
  },

  logout: async () => {
    try {
      await api.post('/auth/logout/', { refresh: localStorage.getItem('refresh_token') })
    } catch {}
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  fetchProfile: async () => {
    try {
      const { data } = await api.get('/auth/profile/')
      set({ user: data, isAuthenticated: true, loading: false })
    } catch {
      set({ user: null, isAuthenticated: false, loading: false })
    }
  },

  updateProfile: async (formData) => {
    const { data } = await api.patch('/auth/profile/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    set({ user: data })
    return data
  },
}))

export default useAuthStore
