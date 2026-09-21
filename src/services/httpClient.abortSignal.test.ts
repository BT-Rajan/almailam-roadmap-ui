import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient, ApiError, RequestCancelledError } from '@/services/httpClient'

// These exercise the abort-signal plumbing in fetchWithTimeout/request<T>
// directly against a stubbed global fetch, rather than through
// test-utils/mockApi.ts -- that mock's route() has no concept of network
// timing or cancellation at all (every call resolves after a fixed delay),
// so it can't stand in for what's being tested here.
function deferredResponse() {
  let resolve!: (value: Response) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<Response>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

beforeEach(() => {
  setActivePinia(createPinia())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('httpClient: caller-supplied AbortSignal', () => {
  it('rejects immediately, without calling fetch, when the signal is already aborted', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    const controller = new AbortController()
    controller.abort()

    await expect(apiClient.get('/api/search?q=ab', { signal: controller.signal })).rejects.toBeInstanceOf(
      RequestCancelledError,
    )
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('rejects with RequestCancelledError (not the generic network-failure message) when aborted mid-flight', async () => {
    const pending = deferredResponse()
    const fetchSpy = vi.fn((_url: string, init: RequestInit) => {
      // Real fetch() rejects with a DOMException named AbortError once its
      // passed-in signal fires -- reproduce that contract here.
      const signal = init.signal as AbortSignal
      signal.addEventListener('abort', () => pending.reject(new DOMException('Aborted', 'AbortError')))
      return pending.promise
    })
    vi.stubGlobal('fetch', fetchSpy)

    const controller = new AbortController()
    const result = apiClient.get('/api/search?q=ab', { signal: controller.signal })
    controller.abort()

    await expect(result).rejects.toBeInstanceOf(RequestCancelledError)
  })

  it('a genuine timeout still produces the "taking longer than expected" ApiError, distinct from cancellation', async () => {
    const pending = deferredResponse()
    vi.stubGlobal(
      'fetch',
      vi.fn((_url: string, init: RequestInit) => {
        const signal = init.signal as AbortSignal
        signal.addEventListener('abort', () => pending.reject(new DOMException('Aborted', 'AbortError')))
        return pending.promise
      }),
    )

    await expect(apiClient.get('/api/search?q=ab', { timeoutMs: 5 })).rejects.toMatchObject({
      constructor: ApiError,
      message: expect.stringContaining('taking longer than expected'),
    })
  })

  it('a genuine network failure still produces "unable to reach the server", unaffected by the signal plumbing', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))),
    )

    await expect(apiClient.get('/api/search?q=ab')).rejects.toMatchObject({
      constructor: ApiError,
      message: expect.stringContaining('Unable to reach the server'),
    })
  })

  it('succeeds normally when a signal is passed but never fires', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 }))),
    )
    const controller = new AbortController()

    await expect(apiClient.get('/api/search?q=ab', { signal: controller.signal })).resolves.toEqual({ ok: true })
  })
})
