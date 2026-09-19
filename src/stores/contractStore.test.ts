import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/httpClient'
import { useContractStore } from '@/stores/contractStore'
import { fixture, overrideMockApi, resetMockApi } from '@/test-utils/mockApi'

vi.mock('@/services/httpClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/httpClient')>()
  const { mockApiClient } = await import('@/test-utils/mockApi')
  return { ...actual, apiClient: mockApiClient }
})

const FALLBACK = 'Unable to load contracts. Please try again.'
const PROJECT = fixture.projectNo as string

describe('contractStore.loadContractsForProject error reporting', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    resetMockApi()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('surfaces the real HTTP failure instead of one generic message', async () => {
    overrideMockApi(/^\/api\/contracts/, () => {
      throw new ApiError(429, 'Too many requests. Please slow down.')
    })
    const store = useContractStore()
    await store.loadContractsForProject(PROJECT)
    expect(store.error).toBe(`${FALLBACK} (HTTP 429 – Too many requests. Please slow down.)`)
    expect(store.isLoading).toBe(false)
  })

  it.each([
    [403, 'You do not have permission to do this.'],
    [500, 'A database error occurred. Please try again.'],
  ])('reports HTTP %i with the backend’s own message', async (status, message) => {
    overrideMockApi(/^\/api\/contracts/, () => {
      throw new ApiError(status, message)
    })
    const store = useContractStore()
    await store.loadContractsForProject(PROJECT)
    expect(store.error).toContain(`HTTP ${status}`)
    expect(store.error).toContain(message)
  })

  it('reports a dropped connection as such', async () => {
    overrideMockApi(/^\/api\/contracts/, () => {
      throw new ApiError(0, 'Unable to reach the server. Please check your connection and try again.')
    })
    const store = useContractStore()
    await store.loadContractsForProject(PROJECT)
    expect(store.error).toContain('Unable to reach the server')
  })

  it('clears the error once a retry succeeds', async () => {
    let fail = true
    overrideMockApi(/^\/api\/contracts/, () => {
      if (fail) throw new ApiError(429, 'Too many requests. Please slow down.')
      return fixture.contracts
    })
    const store = useContractStore()
    await store.loadContractsForProject(PROJECT)
    expect(store.error).toContain('HTTP 429')

    fail = false
    await store.loadContractsForProject(PROJECT)
    expect(store.error).toBeUndefined()
    expect(store.contracts).toHaveLength(fixture.contracts.length)
  })
})
