import { describe, expect, it, vi } from 'vitest'

import { createLoadGate, getLoadGate } from '@/utils/loadGate'

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('createLoadGate', () => {
  it('shares one in-flight request between concurrent callers', async () => {
    const gate = createLoadGate(1000)
    const pending = deferred<boolean>()
    const load = vi.fn(() => pending.promise)

    const first = gate.run(load)
    const second = gate.run(load)
    pending.resolve(true)
    await Promise.all([first, second])

    expect(load).toHaveBeenCalledTimes(1)
  })

  it('skips the network while data is fresh, and reloads once the window has passed', async () => {
    let clock = 0
    const gate = createLoadGate(1000, () => clock)
    const load = vi.fn(async () => true)

    await gate.run(load)
    clock = 999
    await gate.run(load)
    expect(load).toHaveBeenCalledTimes(1)

    clock = 1000
    await gate.run(load)
    expect(load).toHaveBeenCalledTimes(2)
  })

  it('does not mark data fresh after a handled failure, so the next call retries', async () => {
    const gate = createLoadGate(1000)
    const load = vi.fn(async () => false)

    await gate.run(load)
    await gate.run(load)

    expect(load).toHaveBeenCalledTimes(2)
  })

  it('surfaces a rejected load to the caller and recovers on the next call', async () => {
    const gate = createLoadGate(1000)

    await expect(gate.run(async () => Promise.reject(new Error('boom')))).rejects.toThrow('boom')

    const load = vi.fn(async () => true)
    await gate.run(load)
    expect(load).toHaveBeenCalledTimes(1)
  })

  it('force always issues a new request, even while another is in flight or data is fresh', async () => {
    const gate = createLoadGate(1000)
    const slow = deferred<boolean>()
    const first = gate.run(() => slow.promise)

    const forced = vi.fn(async () => true)
    await gate.run(forced, { force: true })
    expect(forced).toHaveBeenCalledTimes(1)

    slow.resolve(true)
    await first

    await gate.run(forced, { force: true })
    expect(forced).toHaveBeenCalledTimes(2)
  })

  it('reports an older load as no longer current once a newer one has started', async () => {
    const gate = createLoadGate(1000)
    const older = deferred<boolean>()
    let olderIsCurrent: (() => boolean) | undefined

    const first = gate.run((isCurrent) => {
      olderIsCurrent = isCurrent
      return older.promise
    })
    expect(olderIsCurrent?.()).toBe(true)

    await gate.run(async () => true, { force: true })
    expect(olderIsCurrent?.()).toBe(false)

    older.resolve(true)
    await first
  })

  it('a superseded load finishing late does not mark the data fresh', async () => {
    const gate = createLoadGate(1000)
    const older = deferred<boolean>()
    const first = gate.run(() => older.promise)

    // A newer forced load fails; the older one then succeeds. Only a current,
    // successful load may mark the data fresh -- so a follow-up must reload.
    await gate.run(async () => false, { force: true })
    older.resolve(true)
    await first

    const next = vi.fn(async () => true)
    await gate.run(next)
    expect(next).toHaveBeenCalledTimes(1)
  })

  it('invalidate() makes the next non-forced call refetch', async () => {
    const gate = createLoadGate(1000)
    const load = vi.fn(async () => true)

    await gate.run(load)
    gate.invalidate()
    await gate.run(load)

    expect(load).toHaveBeenCalledTimes(2)
  })
})

describe('getLoadGate', () => {
  it('returns the same gate for the same owner and key, and separate gates otherwise', () => {
    const ownerA = {}
    const ownerB = {}

    expect(getLoadGate(ownerA, 'projects', 1000)).toBe(getLoadGate(ownerA, 'projects', 1000))
    expect(getLoadGate(ownerA, 'projects', 1000)).not.toBe(getLoadGate(ownerA, 'clients', 1000))
    expect(getLoadGate(ownerA, 'projects', 1000)).not.toBe(getLoadGate(ownerB, 'projects', 1000))
  })
})
