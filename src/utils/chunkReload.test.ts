import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { isChunkLoadError, reloadForNewBuild } from '@/utils/chunkReload'

describe('isChunkLoadError', () => {
  it.each([
    'Failed to fetch dynamically imported module: http://x/assets/Page-abc.js',
    'error loading dynamically imported module: http://x/assets/Page-abc.js',
    'Importing a module script failed.',
    'Unable to preload CSS for /assets/Page-abc.css',
  ])('recognises %s', (message) => {
    expect(isChunkLoadError(new Error(message))).toBe(true)
  })

  it('ignores ordinary errors', () => {
    expect(isChunkLoadError(new Error('Cannot read properties of undefined'))).toBe(false)
    expect(isChunkLoadError(undefined)).toBe(false)
  })
})

describe('reloadForNewBuild', () => {
  const assign = vi.fn()
  const reload = vi.fn()

  beforeEach(() => {
    sessionStorage.clear()
    vi.spyOn(window, 'location', 'get').mockReturnValue({ ...window.location, assign, reload })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    assign.mockReset()
    reload.mockReset()
  })

  it('loads the target page fresh', () => {
    expect(reloadForNewBuild('/projects/42', 1_000_000)).toBe(true)
    expect(assign).toHaveBeenCalledWith('/projects/42')
  })

  it('does not loop when the chunk is still missing right after a reload', () => {
    reloadForNewBuild(undefined, 1_000_000)
    expect(reloadForNewBuild(undefined, 1_005_000)).toBe(false)
    expect(reload).toHaveBeenCalledTimes(1)
  })

  it('reloads again for a later deploy', () => {
    reloadForNewBuild(undefined, 1_000_000)
    expect(reloadForNewBuild(undefined, 2_000_000)).toBe(true)
    expect(reload).toHaveBeenCalledTimes(2)
  })
})
