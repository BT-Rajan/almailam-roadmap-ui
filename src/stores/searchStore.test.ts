import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { RequestCancelledError } from '@/services/httpClient'
import { searchService } from '@/services/searchService'
import { MIN_QUERY_LENGTH, useSearchStore } from '@/stores/searchStore'
import type { SearchResult } from '@/types/Search'

vi.mock('@/services/searchService', () => ({ searchService: { search: vi.fn() } }))

const searchMock = vi.mocked(searchService.search)

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((res) => {
    resolve = res
  })
  return { promise, resolve }
}

const result = (id: string): SearchResult => ({
  id,
  category: 'Project',
  title: id,
  subtitle: '',
  routeName: 'project-workspace',
})

beforeEach(() => {
  setActivePinia(createPinia())
  searchMock.mockReset()
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

describe('searchStore: minimum query length', () => {
  it('does not call the network below MIN_QUERY_LENGTH, and reports needsMoreCharacters', async () => {
    const store = useSearchStore()
    await store.setQuery('a')

    expect(searchMock).not.toHaveBeenCalled()
    expect(store.results).toEqual([])
    expect(store.isLoading).toBe(false)
    expect(store.needsMoreCharacters).toBe(true)
    expect(store.hasQuery).toBe(true)
  })

  it('searches once the term reaches MIN_QUERY_LENGTH', async () => {
    searchMock.mockResolvedValue([result('P-1')])
    const store = useSearchStore()
    await store.setQuery('a'.repeat(MIN_QUERY_LENGTH))

    expect(searchMock).toHaveBeenCalledTimes(1)
    expect(store.results).toHaveLength(1)
    expect(store.needsMoreCharacters).toBe(false)
  })

  it('an empty query needs no "keep typing" prompt either', async () => {
    const store = useSearchStore()
    await store.setQuery('')
    expect(store.needsMoreCharacters).toBe(false)
    expect(store.hasQuery).toBe(false)
  })
})

describe('searchStore: cancelling a superseded search', () => {
  it('aborts the previous request’s signal when a new query comes in', async () => {
    const first = deferred<SearchResult[]>()
    let firstSignal: AbortSignal | undefined
    searchMock.mockImplementationOnce((_term, signal) => {
      firstSignal = signal
      return first.promise
    })
    const store = useSearchStore()

    const firstCall = store.setQuery('ab')
    await Promise.resolve() // let setQuery reach the awaited search() call
    expect(firstSignal?.aborted).toBe(false)

    searchMock.mockImplementationOnce(async () => [result('P-2')])
    const secondCall = store.setQuery('abc')

    expect(firstSignal?.aborted).toBe(true)
    first.resolve([result('P-1')])
    await Promise.all([firstCall, secondCall])
  })

  it('a cancelled (superseded) request does not clobber the newer one’s results, and logs nothing', async () => {
    const first = deferred<SearchResult[]>()
    searchMock.mockImplementationOnce(() => first.promise)
    const store = useSearchStore()

    const firstCall = store.setQuery('ab')
    searchMock.mockImplementationOnce(async () => [result('P-new')])
    const secondCall = store.setQuery('abc')
    await secondCall

    expect(store.results).toEqual([result('P-new')])
    expect(store.isLoading).toBe(false)

    // The older call's promise settles later, as a real aborted fetch would
    // (rejecting once the network layer notices) -- it must not resurrect
    // loading state or overwrite the newer results.
    first.resolve([result('P-stale')])
    await firstCall
    expect(store.results).toEqual([result('P-new')])
    expect(store.isLoading).toBe(false)
    expect(console.error).not.toHaveBeenCalled()
  })

  it('treats a RequestCancelledError rejection the same as a superseded resolve: silent, no state clobber', async () => {
    searchMock.mockImplementationOnce(async () => {
      throw new RequestCancelledError()
    })
    const store = useSearchStore()

    await store.setQuery('ab')

    expect(store.results).toEqual([])
    expect(console.error).not.toHaveBeenCalled()
  })

  it('logs and clears loading state for a genuine search failure (not a cancellation)', async () => {
    searchMock.mockImplementationOnce(async () => {
      throw new Error('boom')
    })
    const store = useSearchStore()

    await store.setQuery('ab')

    expect(store.isLoading).toBe(false)
    expect(console.error).toHaveBeenCalledWith('Search failed:', expect.any(Error))
  })

  it('close() aborts whatever search is in flight', async () => {
    const first = deferred<SearchResult[]>()
    let signal: AbortSignal | undefined
    searchMock.mockImplementationOnce((_term, s) => {
      signal = s
      return first.promise
    })
    const store = useSearchStore()
    store.open()

    const call = store.setQuery('ab')
    await Promise.resolve()
    store.close()

    expect(signal?.aborted).toBe(true)
    expect(store.isOpen).toBe(false)
    expect(store.query).toBe('')
    first.resolve([result('P-1')])
    await call
  })
})
