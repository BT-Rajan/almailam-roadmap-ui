import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { i18n } from '@/i18n'
import ProjectWorkspacePage from '@/pages/ProjectWorkspacePage.vue'
import router from '@/router'
import { ApiError } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import {
  countCalls,
  fixture,
  mockCalls,
  mockUnmatched,
  resetMockApi,
  setMockRateLimit,
  testUser,
} from '@/test-utils/mockApi'
import { settleFor, waitFor, waitForQuiet } from '@/test-utils/waitFor'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

const PROJECT = fixture.projectNo as string
// Same ceiling the real API enforces (backend/app/core/rate_limit.py: 300
// requests per 60s per client). If the page ever starts hammering the API
// again this run ends the way production did -- 429 -- instead of spinning.
const REAL_API_RATE_LIMIT = 300

type Wrapper = ReturnType<typeof mount>
const text = (w: Wrapper) => w.text().replace(/\s+/g, ' ')
const confirmButton = (w: Wrapper) => w.findAll('button').find((b) => b.text().includes('Confirm Payment Received'))

async function openPaymentTab(role: Parameters<typeof testUser>[0] = 'Administrator'): Promise<Wrapper> {
  const pinia = createPinia()
  setActivePinia(pinia)
  // hasHydrated: the router guard would otherwise try to resume a session over the network.
  useAuthStore().$patch({ accessToken: 'token', user: testUser(role), hasHydrated: true })

  await router.push(`/projects/${PROJECT}?tab=handover-payment`)
  await router.isReady()

  return mount(ProjectWorkspacePage, {
    global: { plugins: [pinia, i18n, router], stubs: { teleport: true } },
  })
}

describe('ProjectWorkspacePage -> Handover > Payment Confirmation tab', () => {
  let wrapper: Wrapper | undefined

  beforeEach(() => {
    resetMockApi()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })
  afterEach(() => {
    wrapper?.unmount()
    wrapper = undefined
    vi.restoreAllMocks()
  })

  it('settles on the tab instead of remounting in a loop that ends in "Unable to load contracts"', async () => {
    setMockRateLimit(REAL_API_RATE_LIMIT, () => new ApiError(429, 'Too many requests. Please slow down.'))
    wrapper = await openPaymentTab()

    // Loading must finish: a healthy page goes quiet within moments, while one
    // stuck in a reload/remount loop keeps generating traffic until the rate
    // limiter kicks in (and then ends on the error screen asserted below).
    await waitForQuiet(() => mockCalls.length)

    expect(text(wrapper), 'landed on an error screen').not.toContain('Something went wrong')
    expect(confirmButton(wrapper), 'tab never rendered').toBeTruthy()

    // ...and stay quiet.
    const requestsWhenSettled = mockCalls.length
    await settleFor(1000)
    expect(mockCalls.length, 'the page kept making requests after it had finished loading').toBe(requestsWhenSettled)

    // The page loads contracts once; the tab may fetch handover status a couple
    // of times as the page finishes loading around it. The old loop made dozens
    // of each per second (~300 requests in the first second or so).
    expect(countCalls(/^\/api\/contracts\?/)).toBe(1)
    expect(countCalls(/\/handover$/)).toBeLessThanOrEqual(3)
    expect(mockCalls.length).toBeLessThan(100)

    expect(text(wrapper)).not.toContain('Unable to load contracts')
    expect(mockUnmatched, 'a request has no fixture route -- refresh src/test-utils/fixtures').toEqual([])
  })

  it('still confirms and undoes payment inside the real page', async () => {
    wrapper = await openPaymentTab()
    await waitFor(() => Boolean(confirmButton(wrapper!)))

    await confirmButton(wrapper)!.trigger('click')
    await waitFor(() => text(wrapper!).includes('Confirmed by Sandbox Admin'))
    expect(countCalls(/confirm-payment$/, 'POST')).toBe(1)

    const undo = wrapper.findAll('button').find((b) => b.text().includes('Undo Confirmation'))
    await undo!.trigger('click')
    await waitFor(() => Boolean(confirmButton(wrapper!)))
    expect(text(wrapper)).not.toContain('Something went wrong')
    await flushPromises()
  })

  it('shows a Viewer the tab with Confirm disabled -- the page does not error for them either', async () => {
    wrapper = await openPaymentTab('Viewer')
    await waitFor(() => Boolean(confirmButton(wrapper!)))
    expect(confirmButton(wrapper)!.attributes('disabled')).toBeDefined()
    expect(text(wrapper)).toContain('Your role can’t edit projects')
    expect(text(wrapper)).not.toContain('Something went wrong')
  })
})
