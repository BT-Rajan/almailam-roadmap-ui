import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/stores/authStore'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import { countCalls, fixture, mockCalls, overrideMockApi, resetMockApi, testUser } from '@/test-utils/mockApi'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

const page = <T>(items: T[]) => ({ items, page: 1, pageSize: 200, total: items.length, totalPages: 1 })
const LIST = { projects: /^\/api\/projects(\?|$)(?!.*clientId)/, clients: /^\/api\/clients(\?|$)/, tasks: /^\/api\/tasks(\?|$)(?!.*(assignedTo|projectId))/, submissions: /^\/api\/submissions(\?|$)/ }

// Pages scoped to one user/client/record must fetch only that, never a
// company-wide list (which made them slower the more data the system held).
describe('scoped loading -- no company-wide downloads', () => {
  beforeEach(() => {
    resetMockApi()
    setActivePinia(createPinia())
  })

  it("My Tasks asks the server for just the signed-in user's tasks", async () => {
    const me = testUser('Engineer')
    useAuthStore().$patch({ user: me })
    overrideMockApi(/^\/api\/tasks\?/, () =>
      page([{ id: 'T-1', projectId: 'P-1', title: 'Mine', assignedTo: me.name, priority: 'Medium', severity: 'Minor', dueDate: '2026-10-01', dueTime: '17:00', status: 'Pending', projectName: 'Villa', clientName: 'Al Mailam' }]),
    )
    const tasks = useTaskStore()
    await tasks.loadMyTasks()
    expect(countCalls(new RegExp(`^/api/tasks\\?.*assignedTo=${me.id}`))).toBe(1)
    for (const [name, re] of Object.entries(LIST)) expect(countCalls(re), `downloaded every ${name}`).toBe(0)
    expect(tasks.myTasks.map((t) => t.title)).toEqual(['Mine'])
  })

  it("a client's pages fetch only that client's projects", async () => {
    overrideMockApi(/^\/api\/projects\?.*clientId=CLT-014/, () => page([fixture.project]))
    await useProjectStore().loadProjectsForClient('CLT-014')
    expect(countCalls(/^\/api\/projects\?.*clientId=CLT-014/)).toBe(1)
    expect(countCalls(LIST.projects), 'downloaded every project').toBe(0)
    expect(useProjectStore().projects.map((p) => p.id)).toEqual([fixture.project.id])
  })

  it('opening one permit application fetches just that application', async () => {
    overrideMockApi(/^\/api\/submissions\/SUB-7$/, () => ({ id: '7', submissionNo: 'SUB-7', projectId: 'P-1' }))
    const store = useGovernmentSubmissionStore()
    const loaded = await store.loadSubmissionByNo('SUB-7')
    expect(loaded?.submissionNo).toBe('SUB-7')
    expect(countCalls(LIST.submissions), 'downloaded every application').toBe(0)
    expect(countCalls(LIST.projects), 'downloaded every project').toBe(0)
    expect(mockCalls.length).toBeLessThanOrEqual(3) // the application + authorities/forms catalogues
  })
})

describe('list pages label rows from server-sent names, not the full project list', () => {
  beforeEach(() => {
    resetMockApi()
    setActivePinia(createPinia())
  })

  it('Documents, Permit applications and Messages never download every project', async () => {
    overrideMockApi(/^\/api\/documents\?/, () => page([]))
    overrideMockApi(/^\/api\/submissions(\?|$)/, () => [])
    overrideMockApi(/^\/api\/government\//, () => [])
    overrideMockApi(/^\/api\/messages\//, () => [])
    overrideMockApi(/^\/api\/clients\?/, () => page([]))
    const { useDocumentStore } = await import('@/stores/documentStore')
    const { useMessageCentreStore } = await import('@/stores/messageCentreStore')
    await useDocumentStore().loadDocumentsPage()
    await useGovernmentSubmissionStore().loadSubmissions()
    await useMessageCentreStore().loadAll()
    expect(countCalls(LIST.projects), 'downloaded every project').toBe(0)
  })
})
