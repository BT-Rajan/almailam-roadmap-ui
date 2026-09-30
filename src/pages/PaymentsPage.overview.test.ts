import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { i18n } from '@/i18n'
import PaymentsPage from '@/pages/PaymentsPage.vue'
import { mockCalls, overrideMockApi, resetMockApi } from '@/test-utils/mockApi'
import { settleFor } from '@/test-utils/waitFor'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

// The Payments page shows server-computed rows and totals, and never
// downloads every instalment, project or client to add them up.
describe('PaymentsPage', () => {
  it('uses the agreements overview only', async () => {
    resetMockApi()
    const pinia = createPinia()
    setActivePinia(pinia)
    overrideMockApi(/^\/api\/financial-agreements\/overview$/, () => ({
      totals: { contractAmount: 1000, totalReceived: 100, totalPending: 400, totalOverdue: 200 },
      rows: [{
        id: '1', projectId: 'P1', projectName: 'Villa Salmiya', clientName: 'Acme Trading', stream: 'Design', currency: 'KWD',
        contractAmount: 1000, totalReceived: 100, totalPending: 400, totalOverdue: 200,
        nextPaymentAmount: 200, nextPaymentDueDate: '2026-09-20', nextPaymentIsOverdue: true,
      }],
    }))
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:p(.*)*', component: { template: '<div />' } }] })
    const w = mount(PaymentsPage, { global: { plugins: [pinia, i18n, router], stubs: { teleport: true } } })
    await flushPromises()
    await settleFor(30)

    const listCalls = mockCalls.filter((c) => /^\/api\/(obligations|projects|clients|financial-agreements)(\?|$)/.test(c.path))
    expect(listCalls.map((c) => c.path), 'downloaded a full list').toEqual([])
    expect(w.text()).toContain('Villa Salmiya')
    expect(w.text()).toContain('Acme Trading')
    expect(w.text()).toMatch(/1,000/)
  })
})
