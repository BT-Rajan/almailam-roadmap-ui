import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import ProjectOverviewTab from '@/components/project/ProjectOverviewTab.vue'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/authStore'
import { useTaskStore } from '@/stores/taskStore'
import { fixture, testUser } from '@/test-utils/mockApi'
import { settleFor } from '@/test-utils/waitFor'
import type { Project } from '@/types/Project'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

describe('ProjectOverviewTab -- Design stage', () => {
  it('is the task list: activities with their tasks and New Task, no Permits or design-document report', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().$patch({ accessToken: 'token', user: testUser('Administrator'), hasHydrated: true })
    const project = {
      ...fixture.project,
      selectedActivities: [{ id: '11', activityId: 'A1', activityName: 'Architectural Design', status: 'Not Started' }],
      selectedPermits: [],
    } as Project
    const taskStore = useTaskStore()
    vi.spyOn(taskStore, 'loadTasksForProject').mockResolvedValue()
    taskStore.$patch({
      tasks: [{ id: 'T-1', projectId: project.id, title: 'Draft floor plans', assignedTo: 'Someone', priority: 'Medium', severity: 'Minor', dueDate: '2026-10-01', dueTime: '17:00', status: 'Preset', selectedActivityId: '11' }],
    })
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { template: '<div />' } }] })
    const w = mount(ProjectOverviewTab, {
      props: { project, client: undefined, stageContext: 'Design' },
      global: { plugins: [pinia, i18n, router], stubs: { teleport: true } },
    })
    await settleFor(60)
    const text = w.text()
    expect(text).toContain('Architectural Design')
    expect(text).toContain('Draft floor plans')
    expect(text).toContain('New Task')
    expect(text).toContain('Mark Complete')
    expect(text).not.toContain('No permits selected for this project.')
    expect(text).not.toContain('No design documents delivered yet.')
  })
})
