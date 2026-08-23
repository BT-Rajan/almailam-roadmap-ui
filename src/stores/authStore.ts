import { defineStore } from 'pinia'

import { authService, type CurrentUser } from '@/services/authService'

interface AuthState {
  accessToken: string | null
  user: CurrentUser | null
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

    async loginWithEmployeeId(employeeId: string, password: string) {
      // Same tokens, same session shape as staff login -- the Site
      // Engineer Portal is a different frontend surface hitting a
      // different login endpoint for the same underlying account, not
      // a separate auth system. Everything downstream (the httpClient
      // interceptor, tryRefresh, logout) is shared as-is.
      const tokens = await authService.loginWithEmployeeId(employeeId, password)
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
     * Safe to call concurrently -- overlapping calls share a single in-flight request.
     * Used mid-session by the httpClient 401-retry (see services/httpClient.ts) to renew an
     * expired access token transparently while the user is actively working in the same tab.
     * Deliberately NOT called on app startup/page load -- see the removed hydrate() below;
     * a session must not survive a page refresh, tab close, or browser restart. */
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

    _setToken(accessToken: string) {
      this.accessToken = accessToken
    },

    _clearToken() {
      this.accessToken = null
      this.user = null
    },
  },
})
