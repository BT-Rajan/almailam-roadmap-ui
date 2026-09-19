import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ProjectHandoverPaymentTab from '@/components/project/ProjectHandoverPaymentTab.vue'
import { i18n } from '@/i18n'
import { ApiError } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { countCalls, fixture, mockUnmatched, overrideMockApi, PERMISSIONS_BY_ROLE, resetMockApi, testUser } from '@/test-utils/mockApi'
import { settleFor } from '@/test-utils/waitFor'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

const NO_EDIT_NOTE = 'Your role can’t edit projects. Ask someone with edit access to Projects to confirm or undo payment.'
const FINANCE_NOTE = 'Payment figures are only shown to roles with Finance access.'

const confirmedProject = {
  ...fixture.project,
  handoverPaymentConfirmedAt: '2026-09-19T20:00:00+03:00',
  handoverPaymentConfirmedBy: 'Someone Else',
}

async function mountTab(user: ReturnType<typeof testUser>, project = fixture.project) {
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().$patch({ accessToken: 'token', user, hasHydrated: true })

  // What ProjectWorkspacePage does before any tab renders. For a role without
  // Finance access the real API answers 403 here and the store stays empty.
  if (user.permissions && !user.permissions.Finance?.view) {
    overrideMockApi(/^\/api\/(financial-agreements|obligations)/, () => {
      throw new ApiError(403, 'You do not have permission to do this.')
    })
  }
  await usePaymentStore().loadAll()

  const wrapper = mount(ProjectHandoverPaymentTab, { props: { project }, global: { plugins: [pinia, i18n] } })
  await settleFor(60)
  return wrapper
}

const button = (w: ReturnType<typeof mount>, label: string) => w.findAll('button').find((b) => b.text().includes(label))

describe('ProjectHandoverPaymentTab role gating', () => {
  beforeEach(() => {
    resetMockApi()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('Administrator and Engineer can confirm; nothing is disabled or explained away', async () => {
    for (const role of ['Administrator', 'Engineer'] as const) {
      const w = await mountTab(testUser(role))
      const confirm = button(w, 'Confirm Payment Received')
      expect(confirm, role).toBeTruthy()
      expect(confirm!.attributes('disabled'), role).toBeUndefined()
      expect(w.text(), role).not.toContain(NO_EDIT_NOTE)
      w.unmount()
    }
  })

  it('Viewer sees Confirm disabled with the reason, but still sees the payment figures', async () => {
    const w = await mountTab(testUser('Viewer'))
    const confirm = button(w, 'Confirm Payment Received')
    expect(confirm).toBeTruthy() // visible-but-disabled, per the repo convention
    expect(confirm!.attributes('disabled')).toBeDefined()
    expect(confirm!.attributes('title')).toBe(NO_EDIT_NOTE)
    expect(w.text()).toContain(NO_EDIT_NOTE)
    expect(w.text()).not.toContain(FINANCE_NOTE)
    expect(w.text()).toContain('KWD')
  })

  it('Document Controller: no Finance access is explained instead of showing a false "No payment plan yet"', async () => {
    const w = await mountTab(testUser('Document Controller'))
    expect(w.text()).toContain(FINANCE_NOTE)
    expect(w.text()).not.toContain('No payment plan yet')
    expect(button(w, 'Confirm Payment Received')!.attributes('disabled')).toBeDefined()
  })

  it('a disabled Confirm never reaches the API', async () => {
    const w = await mountTab(testUser('Viewer'))
    await button(w, 'Confirm Payment Received')!.trigger('click')
    await settleFor(60)
    expect(countCalls(/confirm-payment/, 'POST')).toBe(0)
  })

  it('Undo is disabled too when the payment is already confirmed', async () => {
    const w = await mountTab(testUser('Viewer'), confirmedProject)
    const undo = button(w, 'Undo Confirmation')
    expect(undo).toBeTruthy()
    expect(undo!.attributes('disabled')).toBeDefined()
    await undo!.trigger('click')
    await settleFor(60)
    expect(countCalls(/unconfirm-payment/, 'POST')).toBe(0)

    const admin = await mountTab(testUser('Administrator'), confirmedProject)
    expect(button(admin, 'Undo Confirmation')!.attributes('disabled')).toBeUndefined()
  })

  it('follows the server-sent flags, not the role name', async () => {
    const granted = { ...PERMISSIONS_BY_ROLE.Viewer, Projects: { view: true, edit: true, delete: false } }
    const w = await mountTab(testUser('Viewer', granted))
    expect(button(w, 'Confirm Payment Received')!.attributes('disabled')).toBeUndefined()
  })

  it('fails closed when the session has no permissions payload', async () => {
    const w = await mountTab(testUser('Administrator', null))
    expect(button(w, 'Confirm Payment Received')!.attributes('disabled')).toBeDefined()
  })

  it('an allowed user can still confirm end to end', async () => {
    const w = await mountTab(testUser('Engineer'))
    await button(w, 'Confirm Payment Received')!.trigger('click')
    await flushPromises()
    await settleFor(80)
    expect(countCalls(/confirm-payment/, 'POST')).toBe(1)
  })

  it('every request the tab makes is covered by the fixture', async () => {
    await mountTab(testUser('Administrator'))
    expect(mockUnmatched).toEqual([])
  })
})
