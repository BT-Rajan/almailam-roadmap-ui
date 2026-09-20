import { describe, expect, it } from 'vitest'

import { ApiError, asError } from '@/services/httpClient'

describe('asError', () => {
  it('returns an ApiError untouched, so its HTTP status survives', () => {
    const original = new ApiError(429, 'Too many requests. Please slow down.')
    const result = asError(original, 'Failed to fetch things')
    expect(result).toBe(original)
    expect((result as ApiError).status).toBe(429)
    expect(result.message).toBe('Too many requests. Please slow down.')
  })

  it('wraps any other Error as a plain Error with its own message', () => {
    const result = asError(new TypeError('boom'), 'Failed to fetch things')
    expect(result).toBeInstanceOf(Error)
    expect(result).not.toBeInstanceOf(ApiError)
    expect(result.message).toBe('boom')
  })

  it('uses the fallback message when what was thrown is not an Error at all', () => {
    expect(asError('a string', 'Failed to fetch things').message).toBe('Failed to fetch things')
    expect(asError(undefined, 'Failed to fetch things').message).toBe('Failed to fetch things')
  })
})
