import { defineStore } from 'pinia'

import { authService, type CurrentUser } from '@/services/authService'

interface AuthState {
  accessToken: string | null
  user: CurrentUser | null
  /** Tracks whether we've attempted to restore a session from storage yet. */
  isHydrated: boolean
  /**
   * In-flight refresh call, shared across concurrent 401s.
   * The backend rotates (single-use) refresh tokens, so if several
   * requests 401 around the same time (e.g. several dashboard widgets
   * loading after the access token expired) and each independently calls
   * /api/auth/refresh, only the first succeeds -- the rest arrive with an
   * already-revoked token and force a logout. This makes every concurrent
   * caller await the same request instead of firing their own.
   */
  refreshPromise: Promise<boolean> | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: null,
    user: null,
    isHydrated: false,
    refreshPromise: null,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.user),
  },

  actions: {
    async login(username: string, password: string) {
      const tokens = await authService.login(username, password)
      this._setToken(tokens.access_token)
      this.user = await authService.me()
    },

    async logout() {
      try {
        await authService.logout()
      } catch {
        // Best-effort server-side revoke; clear local state regardless.
      }
      this._clearToken()
    },

    /** Attempts to exchange the httpOnly refresh cookie for a new access token. Returns success.
     * Safe to call concurrently -- overlapping calls share a single in-flight request. */
    async tryRefresh(): Promise<boolean> {
      if (this.refreshPromise) return this.refreshPromise

      this.refreshPromise = (async () => {
        try {
          const tokens = await authService.refresh()
          this._setToken(tokens.access_token)
          return true
        } catch {
          this._clearToken()
          return false
        } finally {
          this.refreshPromise = null
        }
      })()

      return this.refreshPromise
    },

    /** Call once on app startup to silently restore a session from the refresh cookie, if any.
     * The cookie is httpOnly, so there's no way to check for it up front -- attempting the
     * refresh is the only way to find out, and a 401 here just means there wasn't one. */
    async hydrate() {
      if (this.isHydrated) return
      const refreshed = await this.tryRefresh()
      if (refreshed) {
        try {
          this.user = await authService.me()
        } catch {
          this._clearToken()
        }
      }
      this.isHydrated = true
    },

    _setToken(accessToken: string) {
      this.accessToken = accessToken
    },

    _clearToken() {
      this.accessToken = null
      this.user = null
    },
  },
})
