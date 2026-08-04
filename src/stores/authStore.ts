import { defineStore } from 'pinia'

import { authService, type CurrentUser } from '@/services/authService'

const REFRESH_STORAGE_KEY = 'almailam-refresh-token'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: CurrentUser | null
  /** Tracks whether we've attempted to restore a session from storage yet. */
  isHydrated: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: null,
    refreshToken: localStorage.getItem(REFRESH_STORAGE_KEY),
    user: null,
    isHydrated: false,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.user),
  },

  actions: {
    async login(username: string, password: string) {
      const tokens = await authService.login(username, password)
      this._setTokens(tokens.access_token, tokens.refresh_token)
      this.user = await authService.me()
    },

    async logout() {
      if (this.refreshToken) {
        try {
          await authService.logout(this.refreshToken)
        } catch {
          // Best-effort server-side revoke; clear local state regardless.
        }
      }
      this._clearTokens()
    },

    /** Attempts to exchange the stored refresh token for a new access token. Returns success. */
    async tryRefresh(): Promise<boolean> {
      if (!this.refreshToken) return false
      try {
        const tokens = await authService.refresh(this.refreshToken)
        this._setTokens(tokens.access_token, tokens.refresh_token)
        return true
      } catch {
        this._clearTokens()
        return false
      }
    },

    /** Call once on app startup to silently restore a session from the stored refresh token. */
    async hydrate() {
      if (this.isHydrated) return
      if (this.refreshToken) {
        const refreshed = await this.tryRefresh()
        if (refreshed) {
          try {
            this.user = await authService.me()
          } catch {
            this._clearTokens()
          }
        }
      }
      this.isHydrated = true
    },

    _setTokens(accessToken: string, refreshToken: string) {
      this.accessToken = accessToken
      this.refreshToken = refreshToken
      localStorage.setItem(REFRESH_STORAGE_KEY, refreshToken)
    },

    _clearTokens() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      localStorage.removeItem(REFRESH_STORAGE_KEY)
    },
  },
})
