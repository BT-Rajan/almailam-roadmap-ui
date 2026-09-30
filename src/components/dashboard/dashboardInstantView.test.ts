import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import DashboardClientsTab from '@/components/dashboard/DashboardClientsTab.vue'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/authStore'
import { overrideMockApi, resetMockApi, testUser } from '@/test-utils/mockApi'
import { readDashboardCache, writeDashboardCache } from '@/utils/dashboardCache'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

const figures = (total: number, name: string) => ({
  total, active: total, inactive: 0, onboarding: 0,
  recentClients: [{ id: 'CLT-001', name, type: 'Company', status: 'Active', city: 'Kuwait City', createdDate: '2026-09-01' }],
})

function signIn(role: Parameters<typeof testUser>[0] = 'Administrator') {
  const pinia = createPinia()
  setActivePinia(pinia)
  const user = testUser(role)
  useAuthStore().$patch({ accessToken: 'token', user, hasHydrated: true })
  return { pinia, user }
}

function mountTab(pinia: ReturnType<typeof createPinia>) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:p(.*)*', component: { template: '<div />' } }] })
  return mount(DashboardClientsTab, { global: { plugins: [pinia, i18n, router] } })
}

// The Dashboard shows the figures from the user's last visit instantly and
// refreshes them in the background (useDashboardData + dashboardCache).
describe('Dashboard instant view', () => {
  beforeEach(() => {
    resetMockApi()
    localStorage.clear()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it("shows the last visit's figures before the server answers, then the fresh ones", async () => {
    const { pinia, user } = signIn()
    writeDashboardCache('clients', user.id, figures(111, 'Saved Client'))
    let answer!: (value: unknown) => void
    overrideMockApi(/^\/api\/dashboard\/clients$/, () => new Promise((resolve) => { answer = resolve }))

    const w = mountTab(pinia)
    expect(w.text()).toContain('111') // on first render, no waiting
    expect(w.text()).toContain('Saved Client')

    await vi.waitFor(() => expect(answer).toBeTypeOf('function'))
    expect(w.text()).toContain('111') // still the saved figures while the request is out
    answer(figures(222, 'Fresh Client'))
    await flushPromises()
    expect(w.text()).toContain('222')
    expect(w.text()).toContain('Fresh Client')
    expect(readDashboardCache<{ total: number }>('clients', user.id)?.data.total).toBe(222) // saved for next time
  })

  it("never shows another user's saved figures", async () => {
    writeDashboardCache('clients', 'USR-999', figures(999, 'Someone Else'))
    const { pinia } = signIn()
    overrideMockApi(/^\/api\/dashboard\/clients$/, () => new Promise(() => {}))
    const w = mountTab(pinia)
    expect(w.text()).not.toContain('999')
    expect(w.text()).not.toContain('Someone Else')
  })

  it('keeps the saved figures up with a notice when the refresh fails', async () => {
    const { pinia, user } = signIn()
    writeDashboardCache('clients', user.id, figures(111, 'Saved Client'))
    overrideMockApi(/^\/api\/dashboard\/clients$/, () => { throw new Error('boom') })
    const w = mountTab(pinia)
    await flushPromises()
    await new Promise((r) => setTimeout(r, 20))
    expect(w.text()).toContain('Saved Client')
    expect(w.text()).toContain("Couldn't refresh")
    expect(w.text()).not.toContain('Unable to load the dashboard')
  })

  it('ending the session wipes the saved figures', () => {
    const { user } = signIn()
    writeDashboardCache('financials', user.id, { totalPending: 1, totalOverdue: 2, overdueAgreements: [] })
    useAuthStore().endSessionFromOtherTab()
    expect(readDashboardCache('financials', user.id)).toBeUndefined()
    expect(Object.keys(localStorage).filter((k) => k.startsWith('serviceos.dashboard.'))).toEqual([])
  })

  it('ignores saved figures older than a day', () => {
    const { user } = signIn()
    const now = Date.now()
    vi.spyOn(Date, 'now').mockReturnValue(now - 25 * 60 * 60 * 1000)
    writeDashboardCache('clients', user.id, figures(1, 'Old'))
    vi.spyOn(Date, 'now').mockReturnValue(now)
    expect(readDashboardCache('clients', user.id)).toBeUndefined()
  })
})
