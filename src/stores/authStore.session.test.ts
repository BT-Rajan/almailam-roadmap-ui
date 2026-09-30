import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { authService } from '@/services/authService'
import { ApiError } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import { useCompanyStore } from '@/stores/companyStore'
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import { useServerTimeStore } from '@/stores/serverTimeStore'
import { installSessionBootstrap } from '@/stores/sessionBootstrap'
import { broadcastLogout, withRefreshLock } from '@/utils/sessionSync'

vi.mock('@/services/authService', () => ({
  authService: { refresh: vi.fn(), logout: vi.fn(), me: vi.fn() },
}))
vi.mock('@/utils/sessionSync', () => ({
  broadcastLogout: vi.fn(),
  withRefreshLock: vi.fn((fn: () => Promise<unknown>) => fn()),
}))

const refreshMock = vi.mocked(authService.refresh)

/** An unsigned JWT-shaped token valid for `ms`, issued at `issuedAt` (seconds). */
function tokenExpiringIn(ms: number, issuedAt = 1_700_000_000): string {
  const payload = btoa(JSON.stringify({ iat: issuedAt, exp: issuedAt + ms / 1000 }))
  return `header.${payload.replace(/=+$/, '')}.signature`
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.useFakeTimers()
  vi.clearAllMocks()
})

afterEach(() => {
  useAuthStore()._clearToken()
  vi.useRealTimers()
})

describe('authStore: proactive refresh', () => {
  it('renews the access token shortly before it expires, without waiting for a 401', async () => {
    const store = useAuthStore()
    const next = tokenExpiringIn(30 * 60_000)
    refreshMock.mockResolvedValue({ access_token: next, token_type: 'bearer' })

    store._setToken(tokenExpiringIn(30 * 60_000))
    await vi.advanceTimersByTimeAsync(28 * 60_000)
    expect(refreshMock).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(90_000)
    expect(refreshMock).toHaveBeenCalledTimes(1)
    expect(withRefreshLock).toHaveBeenCalledTimes(1)
    expect(store.accessToken).toBe(next)
  })

  it('retries after a transient failure instead of letting the token lapse', async () => {
    const store = useAuthStore()
    refreshMock.mockRejectedValueOnce(new ApiError(503, 'busy'))
    refreshMock.mockResolvedValueOnce({ access_token: tokenExpiringIn(30 * 60_000), token_type: 'bearer' })

    store._setToken(tokenExpiringIn(2 * 60_000))
    await vi.advanceTimersByTimeAsync(60_000)
    expect(refreshMock).toHaveBeenCalledTimes(1)
    expect(store.accessToken).not.toBeNull()

    await vi.advanceTimersByTimeAsync(40_000)
    expect(refreshMock).toHaveBeenCalledTimes(2)
  })

  it('stops renewing once the session is cleared', async () => {
    const store = useAuthStore()
    store._setToken(tokenExpiringIn(2 * 60_000))
    store._clearToken()
    await vi.advanceTimersByTimeAsync(5 * 60_000)
    expect(refreshMock).not.toHaveBeenCalled()
  })

  it('is unaffected by a wrong clock on this computer', async () => {
    const store = useAuthStore()
    refreshMock.mockResolvedValue({ access_token: tokenExpiringIn(30 * 60_000, 1), token_type: 'bearer' })
    // Issued "in 1970" as far as this machine's clock is concerned.
    store._setToken(tokenExpiringIn(30 * 60_000, 1))
    await vi.advanceTimersByTimeAsync(10 * 60_000)
    expect(refreshMock).not.toHaveBeenCalled()
  })

  it('ignores a token whose expiry cannot be read', async () => {
    const store = useAuthStore()
    store._setToken('not-a-jwt')
    await vi.advanceTimersByTimeAsync(60 * 60_000)
    expect(refreshMock).not.toHaveBeenCalled()
  })
})

describe('authStore: cross-tab logout', () => {
  it('tells other tabs when a signed-in tab logs out', async () => {
    const store = useAuthStore()
    store._setToken('token')
    await store.logout()
    expect(broadcastLogout).toHaveBeenCalledTimes(1)
  })

  it('does not speak for other tabs when this tab was already signed out', async () => {
    await useAuthStore().logout()
    expect(broadcastLogout).not.toHaveBeenCalled()
  })

  it('ends the session locally, without a server call, when another tab logged out', () => {
    const store = useAuthStore()
    store._setToken('token')
    store.endSessionFromOtherTab()
    expect(store.accessToken).toBeNull()
    expect(authService.logout).not.toHaveBeenCalled()
    expect(broadcastLogout).not.toHaveBeenCalled()
  })
})

// The server sends the signed-in user with every new token, so resuming a
// session on page load is one round trip, not refresh then /me.
describe('authStore: session restore in one round trip', () => {
  const user = { id: 'USR-1', name: 'Ahmed Rashid', designation: null, email: 'a@example.com', mobile: null, role: 'Administrator', avatar: 'AR', status: 'Active' }

  it('takes the user from the refresh response instead of calling /me', async () => {
    refreshMock.mockResolvedValue({ access_token: 'token', token_type: 'bearer', user })
    const store = useAuthStore()
    await store.hydrate()
    expect(store.user).toEqual(user)
    expect(store.isAuthenticated).toBe(true)
    expect(authService.me).not.toHaveBeenCalled()
  })

  it('still asks /me when the server sends no user', async () => {
    refreshMock.mockResolvedValue({ access_token: 'token', token_type: 'bearer' })
    vi.mocked(authService.me).mockResolvedValue(user)
    const store = useAuthStore()
    await store.hydrate()
    expect(authService.me).toHaveBeenCalledTimes(1)
    expect(store.user).toEqual(user)
  })
})

// The server date, branding and knowledgebase switch come with the token,
// so starting the app doesn't need three more requests after sign-in.
describe('authStore: session bootstrap', () => {
  const session = {
    serverTime: { date: '2026-09-30', datetime: '2026-09-30T10:00:00+03:00', timezone: 'Asia/Kuwait' },
    branding: { companyName: 'Al Mailam', brandColor: '#123456', hasLogo: true },
    knowledgeEnabled: true,
  }

  it('fills the server date, branding and knowledgebase switch from the refresh response', async () => {
    installSessionBootstrap()
    refreshMock.mockResolvedValue({ access_token: 'token', token_type: 'bearer', session })
    vi.mocked(authService.me).mockResolvedValue({ id: 'USR-1', name: 'A', designation: null, email: 'a@example.com', mobile: null, role: 'Viewer', avatar: 'A', status: 'Active' })
    await useAuthStore().hydrate()
    expect(useServerTimeStore().todayIso).toBe('2026-09-30')
    expect(useCompanyStore().branding).toEqual(session.branding)
    expect(useKnowledgeStore().isEnabled).toBe(true)
  })

  it('leaves them to load on their own when the server sends none', async () => {
    installSessionBootstrap()
    refreshMock.mockResolvedValue({ access_token: 'token', token_type: 'bearer' })
    vi.mocked(authService.me).mockResolvedValue({ id: 'USR-1', name: 'A', designation: null, email: 'a@example.com', mobile: null, role: 'Viewer', avatar: 'A', status: 'Active' })
    await useAuthStore().hydrate()
    expect(useServerTimeStore().todayIso).toBeNull()
    expect(useCompanyStore().branding).toBeUndefined()
    expect(useKnowledgeStore().isEnabled).toBeUndefined()
  })
})
