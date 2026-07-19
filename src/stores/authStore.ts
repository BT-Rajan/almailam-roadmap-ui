import { defineStore } from 'pinia'

const AUTH_STORAGE_KEY = 'serviceos-auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isAuthenticated: localStorage.getItem(AUTH_STORAGE_KEY) === 'true',
  }),

  actions: {
    login() {
      this.isAuthenticated = true
      localStorage.setItem(AUTH_STORAGE_KEY, 'true')
    },

    logout() {
      this.isAuthenticated = false
      localStorage.removeItem(AUTH_STORAGE_KEY)
    },
  },
})
