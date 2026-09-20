import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/httpClient'
import { describeStoreError } from '@/utils/storeError'

const FALLBACK = 'Unable to load contracts. Please try again.'

afterEach(() => vi.restoreAllMocks())

describe('describeStoreError', () => {
  it('appends the HTTP status and the backend message for API errors', () => {
    expect(describeStoreError(FALLBACK, new ApiError(429, 'Too many requests. Please slow down.'))).toBe(
      `${FALLBACK} (HTTP 429 – Too many requests. Please slow down.)`,
    )
    expect(describeStoreError(FALLBACK, new ApiError(403, 'You do not have permission to do this.'))).toBe(
      `${FALLBACK} (HTTP 403 – You do not have permission to do this.)`,
    )
  })

  it('does not repeat the status when the backend sent no message of its own', () => {
    expect(describeStoreError(FALLBACK, new ApiError(500, 'Request failed (500)'))).toBe(`${FALLBACK} (HTTP 500)`)
  })

  it('uses the network wording as-is when there was no response at all', () => {
    const offline = 'Unable to reach the server. Please check your connection and try again.'
    expect(describeStoreError(FALLBACK, new ApiError(0, offline))).toBe(`${FALLBACK} (${offline})`)
  })

  it('keeps the friendly text for non-API errors but logs them instead of swallowing them', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const bug = new TypeError("Cannot read properties of undefined (reading 'localeCompare')")
    expect(describeStoreError(FALLBACK, bug)).toBe(FALLBACK)
    expect(spy).toHaveBeenCalledOnce()
    expect(spy.mock.calls[0]).toContain(bug)
  })
})
