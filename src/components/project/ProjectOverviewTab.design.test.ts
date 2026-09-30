import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import ProjectOverviewTab from '@/components/project/ProjectOverviewTab.vue'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/authStore'
import { useProjectStore } from '@/stores/projectStore'
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

describe('ProjectOverviewTab -- Design activity with its own auto-created task', () => {
  const baseTask = { projectId: '', assignedTo: 'Ahmed Rashid', priority: 'Medium', severity: 'Minor', dueDate: '2026-10-31', dueTime: '17:00', selectedActivityId: '11' } as const

  async function mountWith(tasks: Array<{ id: string; title: string; status: 'Preset' | 'Pending' | 'Completed' }>) {
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().$patch({ accessToken: 'token', user: testUser('Administrator'), hasHydrated: true })
    const project = {
      ...fixture.project,
      selectedActivities: [{ id: '11', activityId: 'A1', activityName: 'Architectural Design', status: 'Not Started' }],
    } as Project
    const taskStore = useTaskStore()
    vi.spyOn(taskStore, 'loadTasksForProject').mockResolvedValue()
    taskStore.$patch({ tasks: tasks.map((task) => ({ ...baseTask, ...task, projectId: project.id })) })
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { template: '<div />' } }] })
    const w = mount(ProjectOverviewTab, {
      props: { project, client: undefined, stageContext: 'Design' },
      global: { plugins: [pinia, i18n, router], stubs: { teleport: true } },
    })
    await settleFor(60)
    return { w, taskStore, project }
  }

  it('folds the only, same-named task into the activity line instead of repeating it', async () => {
    const { w } = await mountWith([{ id: 'T-main', title: 'Architectural Design', status: 'Preset' }])
    expect(w.text().match(/Architectural Design/g)?.length).toBe(1)
    expect(w.text()).toContain('Ahmed Rashid')
    expect(w.text()).not.toContain('0/1 tasks')
    expect(w.text()).not.toContain('Complete all tasks linked to this activity')
  })

  it('Mark Complete completes that task and the activity in one click', async () => {
    const { w, taskStore, project } = await mountWith([{ id: 'T-main', title: 'Architectural Design', status: 'Preset' }])
    const update = vi.spyOn(taskStore, 'updateTaskStatus').mockResolvedValue()
    const projectStore = useProjectStore()
    vi.spyOn(projectStore, 'refreshProject').mockImplementation(async () => {
      await w.setProps({ project: { ...project, selectedActivities: [{ ...project.selectedActivities![0], status: 'Complete' }] } })
    })
    const markComplete = () => w.findAll('button').find((b) => b.text() === 'Mark Complete')!
    expect(markComplete().attributes('disabled')).toBeDefined() // still needs a closure document or the override
    await w.find('input[type="checkbox"]').setValue(true)
    expect(markComplete().attributes('disabled')).toBeUndefined()
    await markComplete().trigger('click')
    await settleFor(60)
    expect(update).toHaveBeenCalledWith('T-main', 'Completed')
  })

  it('shows the full checklist, main task labelled, once there is more than one task', async () => {
    const { w } = await mountWith([
      { id: 'T-main', title: 'Architectural Design', status: 'Preset' },
      { id: 'T-2', title: 'Check setbacks', status: 'Pending' },
    ])
    expect(w.text()).toContain('Main task')
    expect(w.text()).toContain('Check setbacks')
    expect(w.text()).toContain('0/2 tasks')
    expect(w.text()).toContain('Complete all tasks linked to this activity')
  })
})

describe('ProjectOverviewTab -- completed Design phase', () => {
  it('disables Add task on a closed activity, and New Task once every activity is closed', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().$patch({ accessToken: 'token', user: testUser('Administrator'), hasHydrated: true })
    const project = {
      ...fixture.project,
      selectedActivities: [
        { id: '11', activityId: 'A1', activityName: 'Architectural Design', status: 'Complete' },
        { id: '12', activityId: 'A2', activityName: 'Sanitary', status: 'In Progress' },
      ],
    } as Project
    vi.spyOn(useTaskStore(), 'loadTasksForProject').mockResolvedValue()
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { template: '<div />' } }] })
    const w = mount(ProjectOverviewTab, {
      props: { project, client: undefined, stageContext: 'Design' },
      global: { plugins: [pinia, i18n, router], stubs: { teleport: true } },
    })
    await settleFor(60)
    const buttons = (label: string) => w.findAll('button').filter((b) => b.text() === label)
    const [closedAdd, openAdd] = buttons('Add task')
    expect(closedAdd.attributes('disabled')).toBeDefined()
    expect(openAdd.attributes('disabled')).toBeUndefined()
    expect(buttons('New Task')[0].attributes('disabled')).toBeUndefined()

    await w.setProps({ project: { ...project, selectedActivities: project.selectedActivities!.map((a) => ({ ...a, status: 'Complete' })) } })
    expect(buttons('New Task')[0].attributes('disabled')).toBeDefined()
    expect(buttons('Add task').every((b) => b.attributes('disabled') !== undefined)).toBe(true)
  })
})
