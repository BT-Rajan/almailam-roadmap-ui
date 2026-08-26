// Runs the ACTUAL Vue components (real render, real lifecycle hooks,
// real API calls against the live backend at VITE_API_BASE_URL) inside
// happy-dom instead of a full browser. This is not a substitute for
// Playwright/real Chrome -- happy-dom does no real layout, so it can't
// catch a CSS overflow or a visually broken mobile layout. What it CAN
// catch, because Vue's own runtime warns via console.error/console.warn
// exactly the same way in happy-dom as it would in a real browser
// console, is the actual "hidden console errors" class of bug: a
// missing/invalid prop, an unhandled promise rejection in setup(), a
// null/undefined property access during render, a failed watcher.
//
// Run with: npx vitest run e2e/component-smoke.test.ts
// (backend must already be running -- see backend/.env.example)
import { createPinia, setActivePinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

import router from '@/router/index'
import { useAuthStore } from '@/stores/authStore'
import App from '@/App.vue'
import CustomerPortalLoginPage from '@/pages/CustomerPortalLoginPage.vue'
import CustomerPortalProjectsPage from '@/pages/CustomerPortalProjectsPage.vue'
import CustomerProjectViewPage from '@/pages/CustomerProjectViewPage.vue'

const CUSTOMER_ID = 'CUST-1001'
const CUSTOMER_PASSWORD = 'Demo#2026'

let consoleErrors: unknown[][]
let consoleWarns: unknown[][]
let unhandledRejections: unknown[]

beforeAll(() => {
  process.on('unhandledRejection', (reason) => {
    unhandledRejections.push(reason)
  })
})

beforeEach(() => {
  setActivePinia(createPinia())
  consoleErrors = []
  consoleWarns = []
  unhandledRejections = []
  vi.spyOn(console, 'error').mockImplementation((...args) => {
    consoleErrors.push(args)
  })
  vi.spyOn(console, 'warn').mockImplementation((...args) => {
    consoleWarns.push(args)
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

function assertNoRuntimeErrors() {
  if (consoleErrors.length > 0) {
    console.info('--- captured console.error calls ---')
    for (const args of consoleErrors) console.info(args)
  }
  if (consoleWarns.length > 0) {
    console.info('--- captured console.warn calls ---')
    for (const args of consoleWarns) console.info(args)
  }
  if (unhandledRejections.length > 0) {
    console.info('--- captured unhandled promise rejections ---')
    for (const r of unhandledRejections) console.info(r)
  }
  expect(consoleErrors, 'console.error() during render/mount').toEqual([])
  // Vue's own dev-mode warnings (missing prop, failed watcher, invalid
  // v-model target, etc.) come through console.warn, not console.error --
  // asserting on these too, not just errors, is what actually catches
  // that class of bug.
  expect(consoleWarns, 'console.warn() during render/mount').toEqual([])
  expect(unhandledRejections, 'unhandled promise rejections during render/mount').toEqual([])
}

function goTo(path: string) {
  return router.push(path)
}

describe('Customer Portal: real component mount against the live backend', () => {
  it('login page mounts and logs in with no console errors', async () => {
    await goTo('/customer-portal')
    await router.isReady()
    const wrapper = mount(CustomerPortalLoginPage, {
      global: { plugins: [router] },
    })
    await flushPromises()

    const authStore = useAuthStore()
    await authStore.login(CUSTOMER_ID, CUSTOMER_PASSWORD)
    await flushPromises()

    expect(authStore.isAuthenticated).toBe(true)
    wrapper.unmount()
    assertNoRuntimeErrors()
  })

  it('projects list page mounts with real data, no console errors', async () => {
    const authStore = useAuthStore()
    await authStore.login(CUSTOMER_ID, CUSTOMER_PASSWORD)

    await goTo('/customer-portal/projects')
    await router.isReady()
    const wrapper = mount(CustomerPortalProjectsPage, {
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.html()).toBeTruthy()
    wrapper.unmount()
    assertNoRuntimeErrors()
  })

  it('project view page mounts with real (enriched) project data, every panel renders, no console errors', async () => {
    const authStore = useAuthStore()
    await authStore.login(CUSTOMER_ID, CUSTOMER_PASSWORD)

    await goTo('/customer-portal/2600001')
    await router.isReady()
    const wrapper = mount(CustomerProjectViewPage, {
      global: { plugins: [router] },
    })
    // flushPromises only drains already-settled microtasks -- it doesn't
    // wait for the real network round-trip the mounted component just
    // kicked off. vi.waitFor polls until the loading skeleton is
    // actually gone (or times out and fails with a clear message,
    // rather than silently asserting against a still-loading page).
    await vi.waitFor(
      () => {
        expect(wrapper.html()).not.toContain('animate-pulse')
      },
      { timeout: 5000 },
    )

    const html = wrapper.html()
    for (const heading of ['Project Milestones', 'Deliverables', 'Budget & Payments', 'Scope of Work', 'Recent Updates']) {
      expect(html, `missing panel heading: ${heading}`).toContain(heading)
    }
    // The actual bug this whole test file exists to catch: a future
    // milestone rendered as "-N days ago" in the Recent Updates panel.
    expect(html, 'negative relative-date text leaked into the DOM').not.toMatch(/-\d+ days ago/)

    wrapper.unmount()
    assertNoRuntimeErrors()
  })
})

describe('Customer Portal: full App.vue mount (real layout selection, real header/logout)', () => {
  it('wrong password shows an inline error, not a crash', async () => {
    const authStore = useAuthStore()
    await goTo('/customer-portal')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] } })
    await flushPromises()

    const inputs = wrapper.findAll('input')
    await inputs[0]!.setValue(CUSTOMER_ID)
    await inputs[1]!.setValue('wrong-password')
    await wrapper.find('form').trigger('submit')
    // Real network round-trip to the backend -- not a settled
    // microtask flushPromises() would catch.
    await vi.waitFor(() => {
      expect(wrapper.text()).toMatch(/invalid|incorrect|failed/i)
    }, { timeout: 5000 })

    expect(authStore.isAuthenticated).toBe(false)
    wrapper.unmount()
    assertNoRuntimeErrors()
  })

  it('logs in, shows the shared header, and logout actually clears the session', async () => {
    const authStore = useAuthStore()
    await authStore.login(CUSTOMER_ID, CUSTOMER_PASSWORD)
    await goTo('/customer-portal/2600001')
    await router.isReady()

    const wrapper = mount(App, { global: { plugins: [router] } })
    await vi.waitFor(() => {
      expect(wrapper.html()).not.toContain('animate-pulse')
    }, { timeout: 5000 })

    // The header this test exists to exercise -- built to match the
    // Site Engineer Portal's shell (see CustomerPortalLayout.vue).
    expect(wrapper.text()).toContain('Customer Portal')
    const logoutButton = wrapper.findAll('button').find((b) => /log out/i.test(b.text()))
    expect(logoutButton, 'Logout button not found in header').toBeTruthy()

    await logoutButton!.trigger('click')
    // Real network round-trip (authStore.logout() awaits the server-side
    // revoke call before clearing local state) -- not a settled
    // microtask flushPromises() would catch.
    await vi.waitFor(() => {
      expect(authStore.isAuthenticated).toBe(false)
    }, { timeout: 5000 })

    expect(router.currentRoute.value.name).toBe('customer-portal')

    wrapper.unmount()
    assertNoRuntimeErrors()
  })
})
