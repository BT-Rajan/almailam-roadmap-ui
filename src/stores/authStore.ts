import { defineStore } from 'pinia'

import { authService, type CurrentUser, type ProfileUpdatePayload, type SessionBootstrap } from '@/services/authService'
import { ApiError } from '@/services/httpClient'
import { clearDashboardCache } from '@/utils/dashboardCache'
import { broadcastLogout, withRefreshLock } from '@/utils/sessionSync'

// Renew the access token this long before it expires rather than waiting
// for a request to 401. Refreshing only on a 401 meant someone filling in
// a long form (no API calls, but plenty of typing) could go past the
// server's idle backstop (INACTIVITY_TIMEOUT_MINUTES, measured from the
// last refresh) and be signed out on submit despite never being idle.
const PROACTIVE_REFRESH_LEAD_MS = 60_000
// After a transient refresh failure (busy server, dropped connection).
const PROACTIVE_REFRESH_RETRY_MS = 30_000
const MIN_REFRESH_DELAY_MS = 5_000

// Deliberately outside the store's state: a timer handle is not UI state.
let refreshTimer: ReturnType<typeof setTimeout> | undefined

/**
 * How long the access token is valid for (exp - iat), in ms, or null if it
 * can't be read. Uses the token's own lifetime rather than comparing `exp`
 * with this computer's clock: an office PC whose clock is off by more than
 * the token lifetime would otherwise think every new token is already
 * expired and refresh in a tight loop.
 */
function tokenLifetimeMs(token: string): number | null {
  try {
    const segment = token.split('.')[1]
    if (!segment) return null
    const json = atob(segment.replace(/-/g, '+').replace(/_/g, '/'))
    const { exp, iat } = JSON.parse(json) as { exp?: unknown; iat?: unknown }
    if (typeof exp !== 'number' || typeof iat !== 'number' || exp <= iat) return null
    return (exp - iat) * 1000
  } catch {
    return null
  }
}

function cancelProactiveRefresh(): void {
  if (refreshTimer !== undefined) {
    clearTimeout(refreshTimer)
    refreshTimer = undefined
  }
}

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
   * (e.g. "You were signed out after 5 minutes of inactivity" -- see
   * useIdleLogout). Carried in memory rather than a ?reason= query
   * param, since the login route always stays the bare /login. Read
   * once by LoginPage.vue and cleared, the same "nothing survives a
   * reload" convention already used for the session itself.
   */
  logoutReason: string | null
  /**
   * The server date, branding and knowledgebase switch sent with the
   * latest token (see stores/sessionBootstrap.ts), so the app doesn't ask
   * for them one by one after sign-in. Null until then, or from an older
   * server -- each store then loads its own as before.
   */
  session: SessionBootstrap | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: null,
    user: null,
    refreshPromise: null,
    hydrationPromise: null,
    hasHydrated: false,
    logoutReason: null,
    session: null,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.user),
  },

  actions: {
    async login(username: string, password: string) {
      const tokens = await authService.login(username, password)
      this._setToken(tokens.access_token)
      this._applySession(tokens.session)
      this.user = tokens.user ?? (await authService.me())
    },

    async logout() {
      // Only a tab that was actually signed in speaks for the others. A tab
      // whose session already ended (e.g. a late 401 after another tab
      // logged out) must not announce a logout that could end a session
      // someone has since started in a different tab.
      const wasSignedIn = this.accessToken !== null
      try {
        await authService.logout()
      } catch (error) {
        // Best-effort server-side revoke; clear local state regardless.
        // Logged rather than swallowed outright -- a revoke that silently
        // fails to reach the backend leaves that refresh token live there
        // even though the browser has moved on, so it's worth knowing
        // about even though it can't block the local logout.
        console.error('Failed to revoke session server-side during logout:', error)
      }
      this._clearToken()
      if (wasSignedIn) broadcastLogout()
    },

    /** Ends this tab's session because another tab already logged out. No
     * server call: the other tab already revoked the refresh token. */
    endSessionFromOtherTab() {
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
      broadcastLogout()
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
          const tokens = await withRefreshLock(() => authService.refresh())
          this._setToken(tokens.access_token)
          // The server sends the user with the token: on a fresh page load
          // that is the profile hydrate() needs, with no separate /me call,
          // and mid-session it keeps name and permissions current.
          if (tokens.user) this.user = tokens.user
          this._applySession(tokens.session)
          return true
        } catch (error) {
          // Only a definite "no" from the server (401/403: cookie missing,
          // revoked, expired, idle) ends the session. A busy server (429),
          // a 5xx or a dropped connection says nothing about the session
          // itself -- clearing it here is what used to throw the whole
          // office back to the login page whenever the API was briefly
          // throttled. Keep the token so the caller can surface a normal,
          // retryable error instead.
          if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
            this._clearToken()
          }
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
     * The refresh response carries the profile too (tryRefresh stores it), so a resumed
     * session is one round trip; only an older server without it needs the /me fallback,
     * and if that fails the session is dropped the same as any other failed refresh. */
    async hydrate(): Promise<void> {
      if (this.hasHydrated) return
      if (this.hydrationPromise) return this.hydrationPromise

      this.hydrationPromise = (async () => {
        const refreshed = await this.tryRefresh()
        if (refreshed && !this.user) {
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

    /** Keeps what the server sent with the token; sessionBootstrap.ts
     * hands it to the stores that need it. */
    _applySession(session: SessionBootstrap | undefined) {
      if (session) this.session = session
    },

    _setToken(accessToken: string) {
      this.accessToken = accessToken
      this._scheduleProactiveRefresh(accessToken)
    },

    _clearToken() {
      cancelProactiveRefresh()
      this.accessToken = null
      this.user = null
      this.session = null
      // Every way a session ends lands here -- saved Dashboard figures
      // (incl. Financials) must not outlive it.
      clearDashboardCache()
    },

    _scheduleProactiveRefresh(accessToken: string) {
      cancelProactiveRefresh()
      const lifetime = tokenLifetimeMs(accessToken)
      if (lifetime === null) return
      const delay = Math.max(lifetime - PROACTIVE_REFRESH_LEAD_MS, MIN_REFRESH_DELAY_MS)
      const attempt = async (): Promise<void> => {
        refreshTimer = undefined
        const refreshed = await this.tryRefresh()
        // A transient failure keeps the token (see tryRefresh); try again
        // shortly rather than letting it lapse into a 401 mid-task. A
        // success reschedules itself through _setToken.
        if (!refreshed && this.accessToken === accessToken) {
          refreshTimer = setTimeout(attempt, PROACTIVE_REFRESH_RETRY_MS)
        }
      }
      refreshTimer = setTimeout(attempt, delay)
    },
  },
})
