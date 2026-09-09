import { defineStore } from 'pinia'

import { authService, type CurrentUser, type ProfileUpdatePayload } from '@/services/authService'

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
  /**
   * In-flight startup hydration (see hydrate()). Shared the same way as
   * refreshPromise so concurrent callers (in practice just the router
   * guard, but cheap to make safe) await the same attempt instead of
   * racing two refreshes off one single-use cookie.
   */
  hydrationPromise: Promise<void> | null
  /** True once hydrate() has run (successfully or not) this page load, so it only ever runs once. */
  hasHydrated: boolean
  /**
   * One-shot message for the login page to show after a forced logout
   * (e.g. "You were signed out after 30 minutes of inactivity" -- see
   * useIdleLogout). Carried in memory rather than a ?reason= query
   * param: a query string surviving into a later hard reload/reopened
   * tab at that exact URL was landing some users on a login page that
   * silently refused to submit, and stripping the query was the
   * reported fix -- so the login route now always stays the bare
   * /login, and this in-memory field is read once by LoginPage.vue and
   * cleared, the same "nothing survives a reload" convention already
   * used for the session itself.
   */
  logoutReason: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: null,
    user: null,
    refreshPromise: null,
    hydrationPromise: null,
    hasHydrated: false,
    logoutReason: null,
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

    /** Reads and clears the one-shot post-logout message -- see
     * logoutReason's own doc comment above. Consuming it (rather than
     * just reading) means it only ever shows once, even if the login
     * page instance survives multiple internal navigations. */
    consumeLogoutReason(): string | null {
      const reason = this.logoutReason
      this.logoutReason = null
      return reason
    },

    // Updates the caller's own profile (name/designation/mobile) and
    // refreshes local user state from the response, so the header avatar,
    // initials and "My Profile" details stay in sync immediately without
    // a separate /me refetch.
    async updateProfile(payload: ProfileUpdatePayload) {
      this.user = await authService.updateProfile(payload)
    },

    // Backend revokes every refresh token on a successful password change,
    // so the current session can't silently keep going -- clear local
    // state the same way logout() does and send the user back to sign in.
    async changePassword(currentPassword: string, newPassword: string) {
      await authService.changePassword(currentPassword, newPassword)
      this._clearToken()
    },

    /** Attempts to exchange the httpOnly refresh cookie for a new access token. Returns success.
     * Safe to call concurrently -- overlapping calls share a single in-flight request.
     * Two callers: the httpClient 401-retry (see services/httpClient.ts), renewing an expired
     * access token transparently mid-session, and hydrate() below, restoring a session on a
     * fresh page load. Either way the actual limits on how long a session can be silently
     * resumed are enforced server-side (refresh-token expiry, single-use rotation, and the
     * inactivity backstop in auth_service.refresh) and by the cookie itself being a session
     * cookie with no max_age, so it doesn't outlive the browser being closed. */
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

    /** Runs once per page load, awaited by the router guard before the first navigation
     * resolves (see router/index.ts). Tries to silently resume a session from the httpOnly
     * refresh cookie instead of forcing a full relogin on every hard refresh/reopened tab --
     * the cookie is already designed to be safely redeemable this way (rotated, revocable,
     * capped by both absolute expiry and the idle-timeout backstop), so this only changes
     * *when* it gets redeemed, not what it's trusted to do.
     * tryRefresh() only returns a new access token, not the profile, so a successful
     * hydration also fetches /me; if that fails (e.g. the account was deactivated in the
     * meantime) the session is dropped the same as any other failed refresh. */
    async hydrate(): Promise<void> {
      if (this.hasHydrated) return
      if (this.hydrationPromise) return this.hydrationPromise

      this.hydrationPromise = (async () => {
        const refreshed = await this.tryRefresh()
        if (refreshed) {
          try {
            this.user = await authService.me()
          } catch {
            this._clearToken()
          }
        }
        this.hasHydrated = true
        this.hydrationPromise = null
      })()

      return this.hydrationPromise
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
