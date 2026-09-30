import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useTaskStore } from '@/stores/taskStore'
import { mockCalls, overrideMockApi, resetMockApi } from '@/test-utils/mockApi'
import type { Task, TaskStatus } from '@/types/Task'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

const task = (id: string, status: TaskStatus): Task =>
  ({ id, projectId: 'P1', title: id, assignedTo: 'A', priority: 'Medium', severity: 'Minor', dueDate: '2026-10-01', dueTime: '17:00', status }) as Task

// The Task Board loads each status column as a server page, filtered by the
// server -- never every task ever created.
describe('Task Board loading', () => {
  beforeEach(() => {
    resetMockApi()
    setActivePinia(createPinia())
    overrideMockApi(/^\/api\/tasks\?/, ({ path }) => {
      const params = new URLSearchParams(path.split('?')[1])
      const status = params.get('status') as TaskStatus
      const page = Number(params.get('page'))
      const items = [task(`${status}-${page}a`, status), task(`${status}-${page}b`, status)]
      return { items, page, pageSize: 30, total: 5, totalPages: 3 }
    })
  })

  const taskCalls = () => mockCalls.filter((c) => c.path.startsWith('/api/tasks'))

  it('asks for one page per column, with the filters, and keeps the real totals', async () => {
    const store = useTaskStore()
    store.projectFilter = 'P1'
    store.assigneeFilter = 'USR-004'
    await store.loadBoard()
    const calls = taskCalls()
    expect(calls).toHaveLength(4)
    for (const call of calls) {
      expect(call.path).toMatch(/status=/)
      expect(call.path).toMatch(/projectId=P1/)
      expect(call.path).toMatch(/assignedTo=USR-004/)
      expect(call.path).toMatch(/page=1(&|$)/)
    }
    expect(calls.find((c) => c.path.includes('status=Completed'))!.path).toMatch(/sort=-dueDate/)
    expect(store.boardTotals.Pending).toBe(5)
    expect(store.tasksByStatus.Pending.map((t) => t.id)).toEqual(['Pending-1a', 'Pending-1b'])
  })

  it('"Load more" fetches the next page of just that column', async () => {
    const store = useTaskStore()
    await store.loadBoard()
    mockCalls.length = 0
    await store.loadMoreBoard('Completed')
    expect(taskCalls().map((c) => c.path)).toEqual([expect.stringMatching(/status=Completed.*page=2/)])
    expect(store.tasksByStatus.Completed).toHaveLength(4)
  })

  it('changing a filter reloads the board from the server', async () => {
    const store = useTaskStore()
    await store.loadBoard()
    mockCalls.length = 0
    store.setAssigneeFilter('USR-009')
    await vi.waitFor(() => expect(taskCalls()).toHaveLength(4))
    expect(taskCalls().every((c) => c.path.includes('assignedTo=USR-009'))).toBe(true)
  })

  it('moves a card to its new column when its status changes', async () => {
    const store = useTaskStore()
    await store.loadBoard()
    overrideMockApi(/^\/api\/tasks\/Pending-1a$/, () => task('Pending-1a', 'In Progress'), 'PATCH')
    await store.updateTaskStatus('Pending-1a', 'In Progress')
    expect(store.tasksByStatus.Pending.map((t) => t.id)).toEqual(['Pending-1b'])
    expect(store.tasksByStatus['In Progress'][0].id).toBe('Pending-1a')
    expect(store.boardTotals.Pending).toBe(4)
    expect(store.boardTotals['In Progress']).toBe(6)
  })
})
