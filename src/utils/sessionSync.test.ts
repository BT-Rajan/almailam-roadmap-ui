import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { lastSharedActivity, recordActivity, withRefreshLock } from '@/utils/sessionSync'

beforeEach(() => localStorage.clear())

describe('sessionSync: shared activity', () => {
  it('makes activity in one tab visible to every tab', () => {
    recordActivity(1_000_000)
    expect(lastSharedActivity()).toBe(1_000_000)
  })

  it('throttles writes from constant mouse movement', () => {
    recordActivity(2_000_000)
    recordActivity(2_001_000)
    expect(lastSharedActivity()).toBe(2_000_000)
    recordActivity(2_006_000)
    expect(lastSharedActivity()).toBe(2_006_000)
  })

  it('reports no activity when nothing was recorded', () => {
    expect(lastSharedActivity()).toBe(0)
  })
})

describe('sessionSync: refresh lock', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('serializes refreshes across tabs through the Web Locks API', async () => {
    const request = vi.fn((_name: string, fn: () => Promise<unknown>) => fn())
    vi.stubGlobal('navigator', { locks: { request } })
    await expect(withRefreshLock(async () => 'ok')).resolves.toBe('ok')
    expect(request).toHaveBeenCalledWith('serviceos-auth-refresh', expect.any(Function))
  })

  it('still refreshes in a browser without Web Locks', async () => {
    vi.stubGlobal('navigator', {})
    await expect(withRefreshLock(async () => 'ok')).resolves.toBe('ok')
  })
})
