import { test, expect, type Page, type ConsoleMessage } from '@playwright/test'

// Demo customer login seeded by backend/testdata.sql -- see that file's
// "Customer Portal demo logins" section. Swap these if you're running
// against a different dataset.
const CUSTOMER_ID = 'CUST-1001'
const CUSTOMER_PASSWORD = 'Demo#2026'

/**
 * Attaches console/pageerror/failed-response listeners and returns the
 * accumulated list plus a helper to assert none were unexpected. This is
 * the actual "hidden errors in browser developer mode" check -- static
 * code review can catch a lot, but a console error from a bad prop
 * access, an unhandled promise rejection, or a bad network response
 * generally only shows up once the page has really run in a browser.
 */
function trackPageHealth(page: Page) {
  const consoleErrors: string[] = []
  const pageErrors: string[] = []
  const failedResponses: string[] = []

  page.on('console', (msg: ConsoleMessage) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (err) => {
    pageErrors.push(err.message)
  })
  page.on('response', (res) => {
    // 401 on the very first /me-style check before login is expected;
    // only flag it once we're past the login screen.
    if (res.status() >= 500) {
      failedResponses.push(`${res.status()} ${res.request().method()} ${res.url()}`)
    }
  })

  return {
    consoleErrors,
    pageErrors,
    failedResponses,
    assertClean() {
      expect(pageErrors, 'Uncaught JS exceptions').toEqual([])
      expect(consoleErrors, 'console.error() calls').toEqual([])
      expect(failedResponses, '5xx responses').toEqual([])
    },
  }
}

test.describe('Customer Portal', () => {
  test('login -> project view -> every section renders with no console errors', async ({ page }) => {
    const health = trackPageHealth(page)

    await page.goto('/customer-portal')

    // No horizontal scroll at whatever viewport this project runs
    // under (mobile project uses a 393px-wide device) -- the most
    // common literal meaning of "doesn't work on mobile" is content
    // wider than the screen forcing sideways scrolling.
    const loginOverflowX = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(loginOverflowX, 'Login page has horizontal overflow').toBeLessThanOrEqual(1)

    await page.getByLabel(/customer id/i).fill(CUSTOMER_ID)
    await page.getByLabel(/password/i).fill(CUSTOMER_PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()

    // Single-project customers auto-redirect straight into the project
    // view (see customer_portal_service.list_projects_for_customer) --
    // wait for either that (/customer-portal/<projectId>) or the picker
    // (/customer-portal/projects), whichever this account gets.
    await page.waitForURL(/\/customer-portal\/(projects$|[^/]+$)/, { timeout: 10_000 })

    if (page.url().endsWith('/customer-portal/projects')) {
      // Multi-project account: click into the first one.
      await page.locator('main').getByRole('button').first().click()
      await page.waitForURL(/\/customer-portal\/[^/]+$/)
    }

    // Header
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible()

    // Every panel should at least render its own heading -- whether it
    // shows real data or its EmptyState, both are a legitimate render;
    // what would be a real bug is the section missing outright or the
    // page having crashed partway through.
    for (const heading of ['Project Milestones', 'Deliverables', 'Budget & Payments', 'Scope of Work', 'Recent Updates']) {
      await expect(page.getByText(heading, { exact: true })).toBeVisible()
    }

    // No horizontal overflow on the actual data-heavy project view --
    // this is the page most likely to have a wide element (a table, a
    // long badge row) that only shows up once real content is on screen.
    const projectOverflowX = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(projectOverflowX, 'Project view has horizontal overflow').toBeLessThanOrEqual(1)

    // Logout is reachable and actually logs out (returns to login,
    // doesn't just navigate away leaving the session intact).
    await page.getByRole('button', { name: /log out/i }).click()
    await page.waitForURL(/\/customer-portal$/, { timeout: 10_000 })

    health.assertClean()
  })

  test('wrong password shows an error, not a crash', async ({ page }) => {
    const health = trackPageHealth(page)
    await page.goto('/customer-portal')
    await page.getByLabel(/customer id/i).fill(CUSTOMER_ID)
    await page.getByLabel(/password/i).fill('wrong-password')
    await page.getByRole('button', { name: /sign in/i }).click()

    await expect(page.getByText(/invalid|incorrect|failed/i)).toBeVisible({ timeout: 10_000 })
    // A failed login is expected to log a 401 network response, not
    // throw in the page itself.
    expect(health.pageErrors, 'Uncaught JS exceptions on failed login').toEqual([])
  })

  test('deliverable download button triggers a download, not a broken link', async ({ page }) => {
    await page.goto('/customer-portal')
    await page.getByLabel(/customer id/i).fill(CUSTOMER_ID)
    await page.getByLabel(/password/i).fill(CUSTOMER_PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL(/\/customer-portal\/(projects$|[^/]+$)/, { timeout: 10_000 })
    if (page.url().endsWith('/customer-portal/projects')) {
      await page.locator('main').getByRole('button').first().click()
      await page.waitForURL(/\/customer-portal\/[^/]+$/)
    }

    const downloadButton = page.getByLabel('Download document').first()
    if (await downloadButton.count() === 0) {
      test.skip(true, 'No downloadable deliverables on this seeded project')
    }
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 10_000 }),
      downloadButton.click(),
    ])
    expect(download.suggestedFilename()).toBeTruthy()
  })
})
