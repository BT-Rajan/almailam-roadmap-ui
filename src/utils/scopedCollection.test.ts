import { describe, expect, it } from 'vitest'

import { replaceScope } from '@/utils/scopedCollection'

interface Row {
  id: number
  project: string
}

describe('replaceScope', () => {
  const existing: Row[] = [
    { id: 1, project: 'A' },
    { id: 2, project: 'B' },
    { id: 3, project: 'A' },
  ]

  it('swaps one scope for fresh rows and keeps every other scope', () => {
    const result = replaceScope(existing, [{ id: 9, project: 'A' }], (row) => row.project === 'A')
    expect(result.map((row) => row.id).sort()).toEqual([2, 9])
  })

  it('drops rows that no longer exist in the fresh set (e.g. deleted server-side)', () => {
    const result = replaceScope(existing, [], (row) => row.project === 'A')
    expect(result).toEqual([{ id: 2, project: 'B' }])
  })

  it('adds rows for a scope that had none loaded yet', () => {
    const result = replaceScope(existing, [{ id: 7, project: 'C' }], (row) => row.project === 'C')
    expect(result).toHaveLength(4)
  })

  it('does not mutate the original array', () => {
    const snapshot = [...existing]
    replaceScope(existing, [], (row) => row.project === 'A')
    expect(existing).toEqual(snapshot)
  })
})
