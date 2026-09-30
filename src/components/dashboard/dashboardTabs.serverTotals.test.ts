import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import DashboardClientsTab from '@/components/dashboard/DashboardClientsTab.vue'
import DashboardDeadlinesTab from '@/components/dashboard/DashboardDeadlinesTab.vue'
import DashboardFinancialsTab from '@/components/dashboard/DashboardFinancialsTab.vue'
import DashboardProjectsTab from '@/components/dashboard/DashboardProjectsTab.vue'
import { i18n } from '@/i18n'
import { mockCalls, overrideMockApi, resetMockApi } from '@/test-utils/mockApi'
import { settleFor } from '@/test-utils/waitFor'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

// The dashboard must show server-computed totals and never download a
// company-wide list (every client/project/task/document/payment).
const FULL_LISTS = /^\/api\/(clients|projects|tasks|documents|contracts|financial-agreements|obligations)(\?|$)/

async function mountTab(component: object, tab: string, payload: unknown): Promise<string> {
  resetMockApi()
  setActivePinia(createPinia())
  overrideMockApi(new RegExp(`^/api/dashboard/${tab}$`), () => payload)
  overrideMockApi(/^\/api\/reports\/financial-summary/, () => ({ byCurrency: [] }))
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:p(.*)*', component: { template: '<div />' } }] })
  const w = mount(component, { global: { plugins: [createPinia(), i18n, router], stubs: { teleport: true } } })
  await flushPromises()
  await settleFor(30)
  expect(mockCalls.filter((c) => FULL_LISTS.test(c.path)).map((c) => c.path), 'downloaded a full list').toEqual([])
  expect(mockCalls.some((c) => c.path === `/api/dashboard/${tab}`)).toBe(true)
  return w.text()
}

describe('dashboard tabs use server-computed figures', () => {
  beforeEach(() => vi.spyOn(console, 'error').mockImplementation(() => {}))

  it('Clients', async () => {
    const text = await mountTab(DashboardClientsTab, 'clients', {
      total: 1234, active: 1100, inactive: 34, onboarding: 100,
      recentClients: [{ id: 'CLT-001', name: 'Acme Trading', type: 'Company', status: 'Active', city: 'Kuwait City', createdDate: '2026-09-01' }],
    })
    expect(text).toContain('1234')
    expect(text).toContain('Acme Trading')
  })

  it('Projects', async () => {
    const text = await mountTab(DashboardProjectsTab, 'projects', {
      total: 812, active: 400, onHold: 12,
      recentProjects: [{ id: 'P1', name: 'Villa Salmiya', client: 'Acme Trading', status: 'Active', progress: 40, dueDate: '2026-12-01', siteAddress: null }],
      pendingTasksTotal: 1, pendingTasks: [{ id: 'T1', title: 'Draft floor plans', project: 'Villa Salmiya', priority: 'High', assignee: 'Ahmed Rashid', dueDate: '2026-10-05', status: 'Pending' }],
      documentsTotal: 1, recentDocuments: [{ id: 'D1', name: 'Site plan', project: 'Villa Salmiya', type: 'Drawing', uploadedAt: '2026-09-29', uploadedBy: 'Ahmed Rashid', size: '2.0 KB' }],
    })
    expect(text).toContain('812')
    expect(text).toContain('Villa Salmiya')
    expect(text).toContain('Draft floor plans')
    expect(text).toContain('Site plan')
  })

  it('Deadlines', async () => {
    const text = await mountTab(DashboardDeadlinesTab, 'deadlines', {
      overdueTasks: 57,
      upcomingDeadlines: [{ id: 'T2', title: 'Submit drawings', project: 'Villa Salmiya', dueDate: '2026-10-03', priority: 'Medium' }],
      contractsExpiringSoon: [],
      contractsNotRenewed: [{ contractNo: 'CON-9', projectId: 'P1', project: 'Villa Salmiya', expiryDate: '2026-09-20' }],
    })
    expect(text).toContain('57')
    expect(text).toContain('Submit drawings')
    expect(text).toContain('CON-9')
  })

  it('Financials', async () => {
    const text = await mountTab(DashboardFinancialsTab, 'financials', {
      totalPending: 400, totalOverdue: 200,
      overdueAgreements: [{ id: '1', projectId: 'P1', project: 'Villa Salmiya', client: 'Acme Trading', overdueAmount: 200, currency: 'KWD' }],
    })
    expect(text).toContain('Villa Salmiya')
    expect(text).toContain('Acme Trading')
  })

  it('shows an error with retry instead of zeros when the server fails', async () => {
    resetMockApi()
    setActivePinia(createPinia())
    overrideMockApi(/^\/api\/dashboard\/clients$/, () => { throw new Error('boom') })
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { template: '<div />' } }] })
    const w = mount(DashboardClientsTab, { global: { plugins: [createPinia(), i18n, router] } })
    await flushPromises()
    await settleFor(30)
    expect(w.text()).toContain('Unable to load the dashboard')
  })
})
