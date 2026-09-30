import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'

import { i18n } from '@/i18n'
import ProjectWorkspacePage from '@/pages/ProjectWorkspacePage.vue'
import router from '@/router'
import { useAuthStore } from '@/stores/authStore'
import { countCalls, fixture, mockCalls, resetMockApi, testUser } from '@/test-utils/mockApi'
import { waitForQuiet } from '@/test-utils/waitFor'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

// Opening a project must fetch that project and its client -- never every
// project or client in the company (the old behaviour made opening any
// project slower the more data the system held).
describe('ProjectWorkspacePage -- loads only the project being opened', () => {
  it('fetches this project and its client, never the full project or client lists', async () => {
    resetMockApi()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().$patch({ accessToken: 'token', user: testUser('Administrator'), hasHydrated: true })
    const project = fixture.project as { id: string; clientId: string; projectName: string }
    await router.push(`/projects/${project.id}`)
    await router.isReady()
    const w = mount(ProjectWorkspacePage, { global: { plugins: [pinia, i18n, router], stubs: { teleport: true } } })
    await waitForQuiet(() => mockCalls.length)

    expect(countCalls(new RegExp(`^/api/projects/${project.id}$`))).toBeGreaterThan(0)
    expect(countCalls(new RegExp(`^/api/clients/${project.clientId}$`))).toBeGreaterThan(0)
    expect(countCalls(/^\/api\/projects(\?|$)/), 'downloaded the whole project list').toBe(0)
    expect(countCalls(/^\/api\/clients(\?|$)/), 'downloaded the whole client list').toBe(0)
    expect(w.text()).toContain(project.projectName)
    w.unmount()
  })
})
