import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ServiceTasksDialog from '@/components/project/ServiceTasksDialog.vue'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/authStore'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import { useUserStore } from '@/stores/userStore'
import { fixture, resetMockApi, testUser } from '@/test-utils/mockApi'
import type { Project } from '@/types/Project'
import type { Task } from '@/types/Task'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

const project: Project = {
  ...fixture.project,
  selectedActivities: [{ id: '11', activityId: 'A1', activityName: 'Architectural Design', status: 'Not Started' }],
} as Project

function task(overrides: Partial<Task>): Task {
  return {
    id: 'T-1', projectId: project.id, title: 'Task', assignedTo: 'Someone', priority: 'Medium', severity: 'Minor',
    dueDate: '2026-10-01', dueTime: '17:00', status: 'Pending', ...overrides,
  }
}

function setup() {
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().$patch({ accessToken: 'token', user: testUser('Administrator'), hasHydrated: true })
  const taskStore = useTaskStore()
  taskStore.$patch({
    tasks: [
      task({ id: 'T-sys', title: 'System-created drawing task', status: 'Preset', selectedActivityId: '11' }),
      task({ id: 'T-mine', title: 'Hand-added review', selectedActivityId: '11' }),
      task({ id: 'T-general', title: 'Unlinked chore' }),
      task({ id: 'T-permit', title: 'Permit task', selectedPermitId: '5' }),
    ],
  })
  vi.spyOn(taskStore, 'loadTasksForProject').mockResolvedValue()
  vi.spyOn(useUserStore(), 'loadUsers').mockResolvedValue()
  vi.spyOn(useClientStore(), 'loadClients').mockResolvedValue()
  const refreshProject = vi.spyOn(useProjectStore(), 'refreshProject').mockResolvedValue()
  return { pinia, taskStore, refreshProject }
}

function mountDialog(pinia: ReturnType<typeof createPinia>, service: { kind: 'design'; id: string; name: string } | null) {
  return mount(ServiceTasksDialog, {
    props: { modelValue: true, project, service },
    global: { plugins: [pinia, i18n], stubs: { teleport: true } },
  })
}

describe('ServiceTasksDialog', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    resetMockApi()
  })

  it("lists the service's system-created and hand-added tasks together, and nothing else", async () => {
    const { pinia } = setup()
    const w = mountDialog(pinia, { kind: 'design', id: '11', name: 'Architectural Design' })
    await flushPromises()
    expect(w.text()).toContain('System-created drawing task')
    expect(w.text()).toContain('Hand-added review')
    expect(w.text()).not.toContain('Unlinked chore')
    expect(w.text()).not.toContain('Permit task')
    expect(w.text()).toContain('0 of 2 tasks done')
  })

  it('shows only unlinked tasks for the general list', async () => {
    const { pinia } = setup()
    const w = mountDialog(pinia, null)
    await flushPromises()
    expect(w.text()).toContain('Unlinked chore')
    expect(w.text()).not.toContain('Hand-added review')
  })

  it('quick-adds a task linked to the same service', async () => {
    const { pinia, taskStore, refreshProject } = setup()
    const create = vi.spyOn(taskStore, 'createTask').mockImplementation(async (input) => task({ ...input, id: 'T-new' }))
    const w = mountDialog(pinia, { kind: 'design', id: '11', name: 'Architectural Design' })
    await flushPromises()
    await w.find('form input').setValue('Check setbacks')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(create).toHaveBeenCalledWith(expect.objectContaining({ title: 'Check setbacks', projectId: project.id, selectedActivityId: '11' }))
    expect(create.mock.calls[0][0].selectedPermitId).toBeUndefined()
    expect(refreshProject).toHaveBeenCalledWith(project.id)
  })

  it('completes a task in one click and refreshes the project', async () => {
    const { pinia, taskStore, refreshProject } = setup()
    const update = vi.spyOn(taskStore, 'updateTaskStatus').mockResolvedValue()
    const w = mountDialog(pinia, { kind: 'design', id: '11', name: 'Architectural Design' })
    await flushPromises()
    await w.findAll('button').find((b) => b.attributes('aria-label') === 'Mark "Hand-added review" as done')!.trigger('click')
    await flushPromises()
    expect(update).toHaveBeenCalledWith('T-mine', 'Completed')
    expect(refreshProject).toHaveBeenCalledWith(project.id)
    expect(w.emitted('changed')).toBeTruthy()
  })

  it('opens a task in the editor inside the modal and goes back to the list', async () => {
    const { pinia } = setup()
    const w = mountDialog(pinia, { kind: 'design', id: '11', name: 'Architectural Design' })
    await flushPromises()
    await w.findAll('button').find((b) => b.text().includes('Hand-added review'))!.trigger('click')
    await flushPromises()
    expect(w.text()).toContain('All tasks for Architectural Design')
    expect(w.text()).toContain('Delete')
    await w.findAll('button').find((b) => b.text().includes('All tasks for Architectural Design'))!.trigger('click')
    expect(w.text()).toContain('0 of 2 tasks done')
  })
})
