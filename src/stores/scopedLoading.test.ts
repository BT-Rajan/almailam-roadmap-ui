import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useDocumentStore } from '@/stores/documentStore'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useTaskStore } from '@/stores/taskStore'
import { mockCalls, overrideMockApi, resetMockApi } from '@/test-utils/mockApi'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

const paged = (items: unknown[]) => ({ items, page: 1, pageSize: 200, total: items.length, totalPages: 1 })
const requests = (pattern: RegExp) => mockCalls.filter((call) => call.method === 'GET' && pattern.test(call.path))

beforeEach(() => {
  setActivePinia(createPinia())
  resetMockApi()
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

describe('taskStore: project-scoped loading', () => {
  const task = (id: string, projectId: string) => ({ id, projectId, title: id }) as never

  it('asks the server for only that project, and merges without touching other projects', async () => {
    overrideMockApi(/^\/api\/tasks\?/, () => paged([task('T-new', 'P-1')]))
    const store = useTaskStore()
    store.tasks = [task('T-old', 'P-1'), task('T-other', 'P-2')]

    await store.loadTasksForProject('P-1')

    expect(requests(/^\/api\/tasks\?/)).toHaveLength(1)
    expect(requests(/^\/api\/tasks\?/)[0].path).toContain('projectId=P-1')
    expect(store.tasks.map((t) => t.id).sort()).toEqual(['T-new', 'T-other'])
  })

  it('does not claim the list is complete, so other pages still do a real full load', async () => {
    overrideMockApi(/^\/api\/tasks\?/, () => paged([task('T-1', 'P-1')]))
    const store = useTaskStore()

    await store.loadTasksForProject('P-1')

    expect(store.tasks).toHaveLength(1)
    expect(store.isFullyLoaded).toBe(false)
    expect(store.needsFullLoad).toBe(true)
  })

  it('a full load marks it complete; scoped loads are then no-ops unless forced', async () => {
    // Like the real endpoint, honour the projectId filter when one is sent.
    const everyTask = [task('T-1', 'P-1'), task('T-2', 'P-2')] as { projectId: string }[]
    overrideMockApi(/^\/api\/tasks\?/, ({ path }) => {
      const projectId = new URLSearchParams(path.split('?')[1]).get('projectId')
      return paged(projectId ? everyTask.filter((t) => t.projectId === projectId) : everyTask)
    })
    const store = useTaskStore()

    await store.loadTasks()
    expect(store.isFullyLoaded).toBe(true)
    expect(store.needsFullLoad).toBe(false)

    const before = mockCalls.length
    await store.loadTasksForProject('P-1')
    expect(mockCalls.length).toBe(before)

    await store.loadTasksForProject('P-1', { force: true })
    expect(mockCalls.length).toBeGreaterThan(before)
    expect(store.tasks).toHaveLength(2)
  })

  it('concurrent callers for the same project share one request', async () => {
    overrideMockApi(/^\/api\/tasks\?/, () => paged([task('T-1', 'P-1')]))
    const store = useTaskStore()

    await Promise.all([store.loadTasksForProject('P-1'), store.loadTasksForProject('P-1')])

    expect(requests(/^\/api\/tasks\?/)).toHaveLength(1)
  })

  it('removes a task that was deleted server-side from that project only', async () => {
    overrideMockApi(/^\/api\/tasks\?/, () => paged([]))
    const store = useTaskStore()
    store.tasks = [task('T-gone', 'P-1'), task('T-keep', 'P-2')]

    await store.loadTasksForProject('P-1')

    expect(store.tasks.map((t) => t.id)).toEqual(['T-keep'])
  })
})

describe('documentStore: project-scoped loading', () => {
  const doc = (id: string, projectId: string) => ({ id, projectId }) as never

  it('fetches one project and leaves the rest, without marking the list complete', async () => {
    overrideMockApi(/^\/api\/documents\?/, () => paged([doc('D-new', 'P-1')]))
    const store = useDocumentStore()
    store.documents = [doc('D-old', 'P-1'), doc('D-other', 'P-2')]

    await store.loadDocumentsForProject('P-1')

    expect(requests(/^\/api\/documents\?/)[0].path).toContain('projectId=P-1')
    expect(store.documents.map((d) => d.id).sort()).toEqual(['D-new', 'D-other'])
    expect(store.isFullyLoaded).toBe(false)
    expect(store.needsFullLoad).toBe(true)
  })
})

describe('governmentSubmissionStore: project-scoped loading', () => {
  const submission = (id: string, projectId: string) => ({ id, projectId, submissionNo: id }) as never

  it('fetches one project, keeps the rest, and does not claim completeness', async () => {
    overrideMockApi(/^\/api\/submissions/, () => [submission('S-new', 'P-1')])
    const store = useGovernmentSubmissionStore()
    store.submissions = [submission('S-old', 'P-1'), submission('S-other', 'P-2')]

    await store.loadSubmissionsForProject('P-1')

    expect(requests(/^\/api\/submissions/)[0].path).toContain('projectId=P-1')
    expect(store.submissions.map((s) => s.id).sort()).toEqual(['S-new', 'S-other'])
    expect(store.isFullyLoaded).toBe(false)
  })
})

describe('paymentStore: project-scoped loading', () => {
  const agreement = (id: string, projectId: string) => ({ id, projectId }) as never
  const obligation = (id: string, agreementId: string) => ({ id, agreementId }) as never

  it('replaces only that project’s agreements and obligations', async () => {
    overrideMockApi(/^\/api\/financial-agreements\?/, () => [agreement('FA-1', 'P-1')])
    overrideMockApi(/^\/api\/obligations\?/, () => [obligation('O-1', 'FA-1')])
    const store = usePaymentStore()
    store.agreements = [agreement('FA-0', 'P-1'), agreement('FA-9', 'P-2')]
    store.obligations = [obligation('O-0', 'FA-0'), obligation('O-9', 'FA-9')]

    await store.loadForProject('P-1')

    expect(requests(/^\/api\/financial-agreements\?/)[0].path).toContain('projectId=P-1')
    expect(requests(/^\/api\/obligations\?/)[0].path).toContain('projectId=P-1')
    expect(store.agreements.map((a) => a.id).sort()).toEqual(['FA-1', 'FA-9'])
    // O-0 belonged to this project's previous agreement, so it goes too.
    expect(store.obligations.map((o) => o.id).sort()).toEqual(['O-1', 'O-9'])
    expect(store.isFullyLoaded).toBe(false)
    expect(store.needsFullLoad).toBe(true)
  })

  it('keeps both billing streams of a project', async () => {
    overrideMockApi(/^\/api\/financial-agreements\?/, () => [agreement('FA-D', 'P-1'), agreement('FA-S', 'P-1')])
    overrideMockApi(/^\/api\/obligations\?/, () => [])
    const store = usePaymentStore()

    await store.loadForProject('P-1')

    expect(store.agreements).toHaveLength(2)
  })

  it('loadAll marks it complete', async () => {
    overrideMockApi(/^\/api\/financial-agreements$/, () => [agreement('FA-1', 'P-1')])
    overrideMockApi(/^\/api\/obligations$/, () => [])
    const store = usePaymentStore()

    await store.loadAll()

    expect(store.isFullyLoaded).toBe(true)
    expect(store.needsFullLoad).toBe(false)
  })
})
