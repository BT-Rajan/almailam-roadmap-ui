import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'

import { prefetchDashboardData, useDashboardData } from '@/composables/useDashboardData'
import { useAuthStore } from '@/stores/authStore'
import { testUser } from '@/test-utils/mockApi'

function mountTab(tab: string, load: () => Promise<number>) {
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().$patch({ accessToken: 'token', user: testUser('Administrator'), hasHydrated: true })
  const Tab = defineComponent({
    setup() {
      const { data } = useDashboardData(tab, load)
      return () => h('p', String(data.value ?? ''))
    },
  })
  return mount(Tab, { global: { plugins: [pinia] } })
}

// The router asks for the Dashboard's figures as soon as the session is
// restored; the tab then uses that request rather than starting its own.
describe('useDashboardData prefetch', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.useRealTimers()
  })

  it('uses a request started before the tab mounted', async () => {
    prefetchDashboardData('prefetched', () => Promise.resolve(41))
    const load = vi.fn(() => Promise.resolve(99))
    const w = mountTab('prefetched', load)
    await flushPromises()
    expect(load).not.toHaveBeenCalled()
    expect(w.text()).toBe('41')
  })

  it('uses it only once -- a later load asks the server again', async () => {
    prefetchDashboardData('once', () => Promise.resolve(1))
    mountTab('once', () => Promise.resolve(2))
    await flushPromises()
    const load = vi.fn(() => Promise.resolve(3))
    const w = mountTab('once', load)
    await flushPromises()
    expect(load).toHaveBeenCalledTimes(1)
    expect(w.text()).toBe('3')
  })

  it('ignores a stale prefetch', async () => {
    vi.useFakeTimers({ now: 0 })
    prefetchDashboardData('stale', () => Promise.resolve(1))
    vi.setSystemTime(60_000)
    vi.useRealTimers()
    const load = vi.fn(() => Promise.resolve(2))
    const w = mountTab('stale', load)
    await flushPromises()
    expect(load).toHaveBeenCalledTimes(1)
    expect(w.text()).toBe('2')
  })
})
